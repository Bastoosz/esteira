"""
Chamada direta de modelo, sem agente. Só modelos FREE do OpenRouter.

Por que este arquivo existe: subir um agente (OpenCode, Antigravity) para
fazer "texto entra, JSON sai" é caro em tempo, frágil de parsear e usa uma
ferramenta com sistema de arquivos para uma tarefa que não toca arquivo.

Divisão que vale internalizar:

    tarefa toca arquivo   ->  agente  (esteira-delegate)
    texto entra/texto sai ->  este módulo

A regra do PADROES.md ("proibido modelo pago via API") é imposta AQUI,
em código, não só na documentação: qualquer id de modelo que não termine
em ':free' é recusado antes de sair a requisição.
"""
import json, os, re
import requests
import config

URL = "https://openrouter.ai/api/v1/chat/completions"


class ModeloPagoRecusado(Exception):
    pass


def _validar(modelo):
    if not modelo.endswith(":free"):
        raise ModeloPagoRecusado(
            f"'{modelo}' não é free. Só modelos com sufixo ':free' são "
            f"permitidos aqui — ver PADROES.md. Trabalho grande vai nas "
            f"assinaturas Claude/Codex, não na API paga."
        )
    return modelo


def chamar(prompt, sistema=None, modelos=None, max_tokens=1500, temperatura=0.0):
    """
    Tenta a lista de modelos free em ordem. Devolve (texto, modelo_usado).
    Modelo free cai, fica lento e muda de nome — por isso fallback é o
    comportamento padrão, não uma feature.
    """
    # A política vem antes de tudo: recusa modelo pago mesmo sem chave,
    # mesmo em teste, mesmo se alguém passar --modelo na mão.
    lista = [_validar(m) for m in (modelos or config.MODELOS_FREE)]

    chave = os.getenv("OPENROUTER_API_KEY", "")
    if not chave:
        raise RuntimeError("OPENROUTER_API_KEY não definida")

    msgs = ([{"role": "system", "content": sistema}] if sistema else []) + \
           [{"role": "user", "content": prompt}]

    erros = []
    for modelo in lista:
        try:
            r = requests.post(
                URL,
                headers={"Authorization": f"Bearer {chave}",
                         "Content-Type": "application/json"},
                json={"model": modelo, "messages": msgs,
                      "max_tokens": max_tokens, "temperature": temperatura},
                timeout=90,
            )
            r.raise_for_status()
            d = r.json()
            return d["choices"][0]["message"]["content"], modelo
        except Exception as e:
            erros.append(f"{modelo}: {e}")
            continue
    raise RuntimeError("nenhum modelo free respondeu:\n  " + "\n  ".join(erros))


def chamar_json(prompt, sistema=None, **kw):
    """Mesma coisa, exigindo JSON de volta. Valida — não confia."""
    sistema = (sistema or "") + (
        "\n\nResponda APENAS com um objeto JSON válido. "
        "Sem markdown, sem cercas de código, sem explicação antes ou depois."
    )
    texto, modelo = chamar(prompt, sistema, **kw)
    limpo = re.sub(r"^```(?:json)?|```$", "", texto.strip(), flags=re.M).strip()
    try:
        return json.loads(limpo), modelo
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", limpo, re.S)
        if m:
            return json.loads(m.group(0)), modelo
        raise ValueError(f"{modelo} não devolveu JSON:\n{texto[:500]}")
