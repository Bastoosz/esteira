"""Importa para o hub a telemetria histórica que já existe no disco."""

from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from esteira.hub import db


_MARCAS_DE_SEGREDO = (
    "sk-",
    "token",
    "secret",
    "senha",
    "password",
    "credential",
    "authorization",
    "api_key",
    "apikey",
)


def _parece_conter_segredo(dados: Mapping[str, Any]) -> bool:
    bruto = json.dumps(dados, ensure_ascii=False, default=str).casefold()
    return any(marca in bruto for marca in _MARCAS_DE_SEGREDO)


def _ler_jsonl(caminho: Path) -> Iterable[dict[str, Any]]:
    try:
        linhas = caminho.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for linha in linhas:
        if not linha.strip():
            continue
        try:
            dados = json.loads(linha)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(dados, dict):
            yield dados


def _conta_tecnica(conta: Any, tier: Any) -> tuple[str, str | None]:
    """Separa ``pessoa:runtime`` sem atribuir uma pessoa quando ela falta."""
    if not isinstance(conta, str) or not conta:
        return "", tier if isinstance(tier, str) and tier else None
    pessoa, separador, runtime = conta.partition(":")
    if separador and runtime:
        return pessoa, runtime
    return conta, tier if isinstance(tier, str) and tier else None


def _chave_despacho(dados: Mapping[str, Any]) -> tuple[Any, ...] | None:
    pessoa, runtime = _conta_tecnica(dados.get("conta"), dados.get("tier"))
    del pessoa
    ts, task_id = dados.get("ts"), dados.get("task_id")
    if not ts or not task_id or not runtime:
        return None
    return ("despacho", str(ts), str(task_id), runtime)


def _chave_demanda(
    dados: Mapping[str, Any], demanda: str
) -> tuple[Any, ...] | None:
    ts, rodada, runtime = dados.get("ts"), dados.get("rodada"), dados.get("tier")
    if not ts or rodada is None or not runtime:
        return None
    return ("demanda", str(ts), demanda, rodada, runtime)


def _chaves_existentes(con: sqlite3.Connection) -> set[tuple[Any, ...]]:
    chaves: set[tuple[Any, ...]] = set()
    for linha in db.execucoes(con):
        try:
            bruto = json.loads(linha.get("bruto_json") or "{}")
        except (json.JSONDecodeError, TypeError):
            bruto = {}
        origem = bruto.get("_origem") if isinstance(bruto, dict) else None
        if origem == "despachos":
            chave = _chave_despacho(bruto)
        elif origem == "demanda":
            chave = _chave_demanda(bruto, str(bruto.get("_demanda", "")))
        else:
            chave = None
        if chave is not None:
            chaves.add(chave)
    return chaves


def _semear_despachos(
    con: sqlite3.Connection, raiz: Path, existentes: set[tuple[Any, ...]]
) -> int:
    gravados = 0
    caminho = raiz / "orquestracao" / "despachos.jsonl"
    for original in _ler_jsonl(caminho):
        if _parece_conter_segredo(original):
            continue
        chave = _chave_despacho(original)
        if chave is None or chave in existentes:
            continue
        pessoa, runtime = _conta_tecnica(original.get("conta"), original.get("tier"))
        bruto = dict(original)
        bruto["_origem"] = "despachos"
        db.gravar_execucao(
            con,
            {
                "ts": original.get("ts"),
                "pessoa": pessoa,
                "runtime": runtime,
                "tier": original.get("tier"),
                "task_id": original.get("task_id"),
                "duracao_s": original.get("duracao_s"),
                "codigo": original.get("codigo"),
                "timeout": original.get("timeout"),
                "exit_confiavel": original.get("exit_confiavel"),
                "arquivos_mudados": original.get("arquivos_mudados"),
                "bruto_json": bruto,
            },
        )
        existentes.add(chave)
        gravados += 1
    return gravados


def _semear_demandas(
    con: sqlite3.Connection, raiz: Path, existentes: set[tuple[Any, ...]]
) -> int:
    gravados = 0
    for caminho in sorted((raiz / "demands").glob("*/execucoes.jsonl")):
        demanda = caminho.parent.name
        for original in _ler_jsonl(caminho):
            if _parece_conter_segredo(original):
                continue
            chave = _chave_demanda(original, demanda)
            if chave is None or chave in existentes:
                continue
            pessoa = original.get("conta")
            if pessoa is None:
                pessoa = ""
            if not isinstance(pessoa, str):
                continue
            bruto = dict(original)
            bruto.update({"_origem": "demanda", "_demanda": demanda})
            db.gravar_execucao(
                con,
                {
                    "ts": original.get("ts"),
                    "pessoa": pessoa,
                    "runtime": original.get("tier"),
                    "tier": original.get("tier"),
                    "demanda": demanda,
                    "duracao_s": original.get("duracao_s"),
                    "codigo": original.get("codigo"),
                    "timeout": original.get("timeout"),
                    "bruto_json": bruto,
                },
            )
            existentes.add(chave)
            gravados += 1
    return gravados


def _estado_atual(con: sqlite3.Connection, pessoa: str, runtime: str) -> dict[str, Any] | None:
    linha = con.execute(
        "SELECT * FROM contas WHERE pessoa = ? AND runtime = ?", (pessoa, runtime)
    ).fetchone()
    return dict(linha) if linha is not None else None


def _estado_igual(atual: Mapping[str, Any] | None, novo: Mapping[str, Any]) -> bool:
    if atual is None:
        return False
    campos = (
        "pessoa",
        "runtime",
        "estado",
        "ultimo_smoke_ts",
        "ultimo_smoke_ok",
        "cooldown_ate",
        "quota_reset_ts",
        "motivo",
    )
    for campo in campos:
        existente, recebido = atual.get(campo), novo.get(campo)
        if existente == recebido:
            continue
        if campo == "cooldown_ate" and existente is not None and recebido is not None:
            try:
                if math.isclose(float(existente), float(recebido), rel_tol=0, abs_tol=1e-5):
                    continue
            except (TypeError, ValueError):
                pass
        return False
    return True


def _semear_contas(con: sqlite3.Connection, raiz: Path) -> int:
    caminho = raiz / "logs" / "contas-estado.json"
    try:
        documento = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return 0
    if not isinstance(documento, dict) or _parece_conter_segredo(documento):
        return 0

    secoes = {
        nome: valor if isinstance(valor, dict) else {}
        for nome, valor in (
            ("cooldown", documento.get("cooldown")),
            ("ultimo_uso", documento.get("ultimo_uso")),
            ("contador", documento.get("contador")),
        )
    }
    chaves = set().union(*(secao.keys() for secao in secoes.values()))
    gravados = 0
    for chave in sorted(chaves):
        if not isinstance(chave, str):
            continue
        pessoa, separador, runtime = chave.partition(":")
        if not separador or not pessoa or not runtime:
            continue
        cooldown = secoes["cooldown"].get(chave)
        novo = {
            "pessoa": pessoa,
            "runtime": runtime,
            "estado": "cooldown" if cooldown is not None else "desconhecido",
            "ultimo_smoke_ts": None,
            "ultimo_smoke_ok": None,
            "cooldown_ate": cooldown,
            "quota_reset_ts": None,
            "motivo": None,
        }
        if _estado_igual(_estado_atual(con, pessoa, runtime), novo):
            continue
        db.gravar_estado_conta(con, novo)
        gravados += 1
    return gravados


def tudo(con: sqlite3.Connection, raiz: str | Path) -> int:
    """Semeia todas as fontes conhecidas e devolve quantas linhas mudou."""
    raiz = Path(raiz)
    db.migrar(con)
    existentes = _chaves_existentes(con)
    return (
        _semear_despachos(con, raiz, existentes)
        + _semear_demandas(con, raiz, existentes)
        + _semear_contas(con, raiz)
    )
