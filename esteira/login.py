"""Login interativo dos runtimes usados pela esteira.

Este módulo conduz cada CLI ao diretório de configuração correto. Ele não
transporta segredos e não persiste alterações no registro de contas: a marcação
em ``contas.yaml`` continua sendo uma decisão humana.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from esteira import contas


RUNTIMES = ("claude", "codex", "opencode", "agy")


def pessoas() -> list[dict[str, Any]]:
    """Devolve as pessoas declaradas no registro oficial de contas."""
    return list(contas._registro().get("pessoas", []))


def _pessoa(pessoa: str | dict[str, Any]) -> dict[str, Any]:
    pessoa_id = pessoa.get("id") if isinstance(pessoa, dict) else pessoa
    encontrada = next((item for item in pessoas() if item.get("id") == pessoa_id), None)
    if encontrada is None:
        raise ValueError(f"pessoa desconhecida: {pessoa_id}")
    return encontrada


def _conta(pessoa: str | dict[str, Any], runtime: str) -> dict[str, str]:
    cadastro = _pessoa(pessoa)
    registro = (cadastro.get("contas") or {}).get(runtime)
    if not registro or not registro.get("config_dir"):
        raise ValueError(f"{cadastro['id']} não possui conta {runtime}")
    return {
        "chave": f"{cadastro['id']}:{runtime}",
        "pessoa_id": cadastro["id"],
        "nome": cadastro.get("nome", cadastro["id"]),
        "tipo": runtime,
        "config_dir": str(Path(registro["config_dir"]).expanduser()),
    }


def comando(pessoa: str | dict[str, Any], runtime: str) -> list[str]:
    """Monta o comando interativo, sem acessar nenhum arquivo de segredo."""
    if runtime not in RUNTIMES:
        raise ValueError(f"runtime desconhecido: {runtime}")

    cadastro = _pessoa(pessoa)
    if runtime not in contas.VAR_CONFIG:
        # O spike não confirmou isolamento por pessoa para estes runtimes.
        return [runtime]

    conta = _conta(cadastro, runtime)
    ambiente = contas.env_para(conta)
    variavel = contas.VAR_CONFIG[runtime]
    return ["env", f"{variavel}={ambiente[variavel]}", runtime]


def ativar(
    pessoa: str | dict[str, Any], runtime: str, *, smoke_passou: bool
) -> dict[str, Any]:
    """Autoriza a marcação humana somente após um smoke bem-sucedido."""
    cadastro = _pessoa(pessoa)
    if runtime not in RUNTIMES:
        raise ValueError(f"runtime desconhecido: {runtime}")
    if runtime in contas.VAR_CONFIG:
        _conta(cadastro, runtime)
    if not smoke_passou:
        raise RuntimeError("conta não pode ser ativada: smoke test falhou")
    return {"pessoa": cadastro["id"], "runtime": runtime, "ativo": True}


_EXPIRACAO = re.compile(
    r"(?:"
    r"(?:oauth|auth(?:entication)?|credential|session|token)s?[^\n]{0,80}"
    r"(?:expired|has expired|expiration)"
    r"|(?:expired|expiration)[^\n]{0,80}"
    r"(?:oauth|auth(?:entication)?|credential|session|token)s?"
    r"|(?:oauth|auth(?:entication)?)[^\n]{0,80}could not be refreshed"
    r")",
    re.IGNORECASE,
)


def precisa_relogin(texto: str) -> bool:
    """Indica se a saída relata expiração de autenticação."""
    return bool(_EXPIRACAO.search(texto or ""))


def conta_para_smoke(pessoa: str | dict[str, Any], runtime: str) -> dict[str, str] | None:
    """Traduz um cadastro no formato esperado por ``runner.smoke_test``."""
    return _conta(pessoa, runtime) if runtime in contas.VAR_CONFIG else None


def tier_para(runtime: str) -> str:
    """Obtém o tier a partir do mapeamento central de contas."""
    for tier, tipo in contas.TIER_CONTA.items():
        if tipo == runtime:
            return tier
    if runtime in RUNTIMES:
        return runtime
    raise ValueError(f"runtime desconhecido: {runtime}")
