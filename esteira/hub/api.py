"""Validação e respostas HTTP dos endpoints do hub."""

from __future__ import annotations

import datetime as dt
from typing import Any

from flask import request

from esteira.hub import db


def _payload(
    campos_obrigatorios: tuple[str, ...],
) -> tuple[dict[str, Any] | None, tuple[dict, int] | None]:
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return None, ({"ok": False, "erro": "payload JSON inválido"}, 400)
    faltantes = [
        campo
        for campo in campos_obrigatorios
        if not isinstance(dados.get(campo), str) or not dados[campo].strip()
    ]
    if faltantes:
        return None, ({"ok": False, "erro": f"campos obrigatórios inválidos: {', '.join(faltantes)}"}, 400)
    return dados, None


def _numero(dados: dict[str, Any], campo: str, inteiro: bool = False) -> bool:
    valor = dados.get(campo)
    if valor is None:
        return True
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return False
    return not inteiro or isinstance(valor, int)


def _textos_opcionais(dados: dict[str, Any], campos: tuple[str, ...]) -> bool:
    return all(
        dados.get(campo) is None or isinstance(dados[campo], str)
        for campo in campos
    )


def postar_telemetria():
    dados, erro = _payload(("pessoa", "runtime", "tier"))
    if erro:
        return erro
    assert dados is not None
    inteiros = ("codigo", "arquivos_mudados", "log_bytes")
    numeros_validos = (
        _numero(dados, "duracao_s")
        and _numero(dados, "custo_nocional_usd")
        and all(_numero(dados, campo, inteiro=True) for campo in inteiros)
    )
    textos_validos = _textos_opcionais(
        dados, ("ts", "task_id", "demanda", "cwd", "veredito")
    )
    if not numeros_validos or not textos_validos:
        return {"ok": False, "erro": "campo de telemetria inválido"}, 400
    for campo in ("timeout", "exit_confiavel"):
        if campo in dados and not isinstance(dados[campo], bool):
            return {"ok": False, "erro": f"{campo} deve ser booleano"}, 400

    con = db.abrir()
    try:
        db.migrar(con)
        id_ = db.gravar_execucao(con, dados)
    finally:
        con.close()
    return {"ok": True, "id": id_}, 201


def postar_estado_conta():
    dados, erro = _payload(("pessoa", "runtime", "estado"))
    if erro:
        return erro
    assert dados is not None
    if "ultimo_smoke_ok" in dados and not isinstance(dados["ultimo_smoke_ok"], bool):
        return {"ok": False, "erro": "ultimo_smoke_ok deve ser booleano"}, 400
    if not _textos_opcionais(dados, ("ultimo_smoke_ts", "motivo")):
        return {"ok": False, "erro": "campo textual inválido"}, 400
    for campo in ("cooldown_ate", "quota_reset_ts"):
        if dados.get(campo) is not None and not isinstance(
            dados[campo], (str, int, float)
        ):
            return {"ok": False, "erro": f"{campo} inválido"}, 400

    con = db.abrir()
    try:
        db.migrar(con)
        db.gravar_estado_conta(con, dados)
    finally:
        con.close()
    return {"ok": True}, 201


def _data_query(nome: str) -> tuple[str | None, str | None]:
    valor = request.args.get(nome)
    if not valor:
        return None, None
    try:
        normalizado = valor.replace("Z", "+00:00")
        instante = dt.datetime.fromisoformat(normalizado)
        if len(valor) == 10 and nome == "fim":
            instante = instante.replace(hour=23, minute=59, second=59)
        if instante.tzinfo is None:
            instante = instante.replace(tzinfo=dt.timezone.utc)
        return instante.astimezone(dt.timezone.utc).isoformat(timespec="seconds"), None
    except ValueError:
        return None, f"{nome} deve estar no formato ISO 8601"


def obter_consumo():
    pessoa = request.args.get("pessoa", type=str)
    inicio, erro_inicio = _data_query("inicio")
    fim, erro_fim = _data_query("fim")
    if erro_inicio or erro_fim:
        return {"ok": False, "erro": erro_inicio or erro_fim}, 400
    if inicio and fim and inicio > fim:
        return {"ok": False, "erro": "inicio deve ser anterior a fim"}, 400

    con = db.abrir()
    try:
        db.migrar(con)
        linhas = db.execucoes(con, pessoa=pessoa, inicio=inicio, fim=fim)
    finally:
        con.close()
    return {
        "ok": True,
        "filtros": {"pessoa": pessoa, "inicio": inicio, "fim": fim},
        "total": len(linhas),
        "execucoes": linhas,
    }
