"""Acesso SQLite do hub.

O caminho pode ser definido por ``ESTEIRA_HUB_DB``. O padrão fica em
``data/hub.db``, dentro do repositório e fora do controle de versão.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Mapping


CAMINHO_PADRAO = Path(
    os.getenv(
        "ESTEIRA_HUB_DB",
        str(Path(__file__).resolve().parents[2] / "data" / "hub.db"),
    )
)
BUSY_TIMEOUT_MS = 5_000


def abrir(caminho: str | Path | None = None) -> sqlite3.Connection:
    """Abre o banco preparado para dois processos escritores."""
    alvo = Path(caminho) if caminho is not None else CAMINHO_PADRAO
    alvo.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(alvo, timeout=BUSY_TIMEOUT_MS / 1_000)
    con.row_factory = sqlite3.Row
    con.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    con.execute("PRAGMA journal_mode = WAL")
    return con


def migrar(con: sqlite3.Connection) -> None:
    """Cria o esquema. Pode ser chamada em toda inicialização."""
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS execucoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            pessoa TEXT NOT NULL,
            runtime TEXT NOT NULL,
            tier TEXT NOT NULL,
            task_id TEXT,
            demanda TEXT,
            cwd TEXT,
            duracao_s REAL,
            codigo INTEGER,
            timeout INTEGER,
            exit_confiavel INTEGER,
            arquivos_mudados INTEGER,
            log_bytes INTEGER,
            veredito TEXT,
            custo_nocional_usd REAL,
            bruto_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_execucoes_pessoa_ts
            ON execucoes (pessoa, ts);

        CREATE TABLE IF NOT EXISTS contas (
            pessoa TEXT NOT NULL,
            runtime TEXT NOT NULL,
            estado TEXT NOT NULL,
            ultimo_smoke_ts TEXT,
            ultimo_smoke_ok INTEGER,
            cooldown_ate TEXT,
            quota_reset_ts TEXT,
            motivo TEXT,
            PRIMARY KEY (pessoa, runtime)
        );

        CREATE TABLE IF NOT EXISTS eventos (
            ts TEXT NOT NULL,
            tipo TEXT NOT NULL,
            pessoa TEXT,
            runtime TEXT,
            detalhe TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_eventos_ts ON eventos (ts);
        """
    )
    con.commit()


def tabelas(con: sqlite3.Connection) -> list[str]:
    linhas = con.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    return [linha[0] for linha in linhas]


def colunas(con: sqlite3.Connection, tabela: str) -> list[str]:
    if tabela not in {"execucoes", "contas", "eventos"}:
        raise ValueError("tabela desconhecida")
    return [linha[1] for linha in con.execute(f"PRAGMA table_info({tabela})")]


def _agora() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _bruto_seguro(valor: Any) -> Any:
    """Remove credenciais evidentes sem descartar métricas de uso."""
    if isinstance(valor, Mapping):
        limpo = {}
        for chave, item in valor.items():
            nome = str(chave).lower().replace("-", "_")
            segredo = (
                any(
                    parte in nome
                    for parte in (
                        "secret", "senha", "password", "credential",
                        "auth", "apikey", "api_key",
                    )
                )
                or nome in {"token", "access_token", "refresh_token", "api_token"}
            )
            limpo[str(chave)] = "[REMOVIDO]" if segredo else _bruto_seguro(item)
        return limpo
    if isinstance(valor, (list, tuple)):
        return [_bruto_seguro(item) for item in valor]
    return valor


def _json_bruto(dados: Mapping[str, Any]) -> str:
    bruto = dados.get("bruto_json", dados)
    if isinstance(bruto, str):
        try:
            bruto = json.loads(bruto)
        except json.JSONDecodeError:
            bruto = {"texto": bruto}
    return json.dumps(_bruto_seguro(bruto), ensure_ascii=False, separators=(",", ":"))


def gravar_execucao(con: sqlite3.Connection, dados: Mapping[str, Any]) -> int:
    campos = (
        "ts", "pessoa", "runtime", "tier", "task_id", "demanda", "cwd",
        "duracao_s", "codigo", "timeout", "exit_confiavel",
        "arquivos_mudados", "log_bytes", "veredito", "custo_nocional_usd",
    )
    valores = {campo: dados.get(campo) for campo in campos}
    valores["ts"] = valores["ts"] or _agora()
    for campo in ("timeout", "exit_confiavel"):
        if valores[campo] is not None:
            valores[campo] = int(bool(valores[campo]))
    valores["bruto_json"] = _json_bruto(dados)
    nomes = (*campos, "bruto_json")
    marcadores = ", ".join("?" for _ in nomes)
    with con:
        cursor = con.execute(
            f"INSERT INTO execucoes ({', '.join(nomes)}) VALUES ({marcadores})",
            [valores[nome] for nome in nomes],
        )
    return int(cursor.lastrowid)


def execucoes(
    con: sqlite3.Connection,
    pessoa: str | None = None,
    inicio: str | None = None,
    fim: str | None = None,
) -> list[dict[str, Any]]:
    filtros = []
    parametros: list[Any] = []
    if pessoa:
        filtros.append("pessoa = ?")
        parametros.append(pessoa)
    if inicio:
        filtros.append("ts >= ?")
        parametros.append(inicio)
    if fim:
        filtros.append("ts <= ?")
        parametros.append(fim)
    onde = f" WHERE {' AND '.join(filtros)}" if filtros else ""
    linhas = con.execute(
        f"SELECT * FROM execucoes{onde} ORDER BY ts DESC, id DESC", parametros
    ).fetchall()
    return [dict(linha) for linha in linhas]


def gravar_estado_conta(con: sqlite3.Connection, dados: Mapping[str, Any]) -> None:
    valores = {
        campo: dados.get(campo)
        for campo in (
            "pessoa", "runtime", "estado", "ultimo_smoke_ts",
            "ultimo_smoke_ok", "cooldown_ate", "quota_reset_ts", "motivo",
        )
    }
    if valores["ultimo_smoke_ok"] is not None:
        valores["ultimo_smoke_ok"] = int(bool(valores["ultimo_smoke_ok"]))
    with con:
        con.execute(
            """
            INSERT INTO contas (
                pessoa, runtime, estado, ultimo_smoke_ts, ultimo_smoke_ok,
                cooldown_ate, quota_reset_ts, motivo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pessoa, runtime) DO UPDATE SET
                estado = excluded.estado,
                ultimo_smoke_ts = excluded.ultimo_smoke_ts,
                ultimo_smoke_ok = excluded.ultimo_smoke_ok,
                cooldown_ate = excluded.cooldown_ate,
                quota_reset_ts = excluded.quota_reset_ts,
                motivo = excluded.motivo
            """,
            list(valores.values()),
        )
        con.execute(
            "INSERT INTO eventos (ts, tipo, pessoa, runtime, detalhe) VALUES (?, ?, ?, ?, ?)",
            (
                str(dados.get("ts") or _agora()),
                "estado_conta",
                valores["pessoa"],
                valores["runtime"],
                str(valores["motivo"] or valores["estado"]),
            ),
        )
