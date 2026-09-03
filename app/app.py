"""Vitrine da Esteira: lê o hub por HTTP e nunca inventa estado."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, render_template


app = Flask(__name__)

HUB_URL = os.getenv("ESTEIRA_HUB_URL", "http://localhost:5000").rstrip("/")
HUB_TIMEOUT_S = 2

ESTADOS_PT = {
    "ativa": "viva",
    "active": "viva",
    "cooldown": "de molho",
    "quota_exhausted": "sem cota",
    "sem_cota": "sem cota",
    "executando": "em execução",
    "running": "em execução",
    "pending": "pendente",
    "passed": "passada",
    "failed": "falhou",
}


def _buscar(caminho: str, parametros: dict[str, str] | None = None) -> Any | None:
    """Devolve JSON do hub ou None; indisponibilidade é dado desconhecido."""
    consulta = f"?{urlencode(parametros)}" if parametros else ""
    requisicao = Request(
        f"{HUB_URL}{caminho}{consulta}",
        headers={"Accept": "application/json"},
    )
    try:
        with urlopen(requisicao, timeout=HUB_TIMEOUT_S) as resposta:
            if not 200 <= resposta.status < 300:
                return None
            return json.loads(resposta.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _buscar_em_paralelo(caminhos: dict[str, str]) -> dict[str, Any | None]:
    with ThreadPoolExecutor(max_workers=len(caminhos)) as executor:
        futuros = {nome: executor.submit(_buscar, caminho) for nome, caminho in caminhos.items()}
        return {nome: futuro.result() for nome, futuro in futuros.items()}


def _lista(resposta: Any, *chaves: str) -> list[dict[str, Any]] | None:
    """Aceita a lista direta ou envelopes comuns sem converter falha em lista vazia."""
    candidata = resposta
    if isinstance(resposta, dict):
        candidata = next((resposta[chave] for chave in chaves if chave in resposta), None)
    if not isinstance(candidata, list) or not candidata:
        return None
    return [item for item in candidata if isinstance(item, dict)] or None


def _dados_esteira() -> dict[str, list[dict[str, Any]] | None]:
    respostas = _buscar_em_paralelo(
        {
            "contas": "/api/contas",
            "demandas": "/api/demandas",
            "vagas": "/api/vagas",
        }
    )
    return {
        "contas": _lista(respostas["contas"], "contas", "itens", "dados"),
        "demandas": _lista(respostas["demandas"], "demandas", "itens", "dados"),
        "vagas": _lista(respostas["vagas"], "vagas", "itens", "dados"),
    }


def _dados_consumo() -> dict[str, Any]:
    resposta = _buscar("/api/consumo")
    if isinstance(resposta, list):
        return {"linhas": _lista(resposta), "serie": None}
    if not isinstance(resposta, dict):
        return {"linhas": None, "serie": None}
    return {
        "linhas": _lista(resposta, "consumo", "linhas", "resumo", "itens", "dados"),
        "serie": _lista(resposta, "serie", "serie_diaria", "dias"),
    }


def _dados_contas() -> list[dict[str, Any]] | None:
    return _lista(_buscar("/api/contas"), "contas", "itens", "dados")


@app.template_filter("estado_pt")
def estado_pt(valor: Any) -> Any:
    if not isinstance(valor, str):
        return valor
    chave = valor.strip().lower().replace(" ", "_")
    return ESTADOS_PT.get(chave, valor.replace("_", " ").lower())


@app.get("/")
def esteira():
    return render_template("esteira.html", **_dados_esteira())


@app.get("/consumo")
def consumo():
    return render_template("consumo.html", **_dados_consumo())


@app.get("/contas")
def contas():
    return render_template("contas.html", contas=_dados_contas())


@app.get("/_painel/esteira")
def painel_esteira():
    return render_template("_partials/esteira.html", **_dados_esteira())


@app.get("/_painel/consumo")
def painel_consumo():
    return render_template("_partials/consumo.html", **_dados_consumo())


@app.get("/_painel/contas")
def painel_contas():
    return render_template("_partials/contas.html", contas=_dados_contas())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("ESTEIRA_APP_PORT", "8000")))
