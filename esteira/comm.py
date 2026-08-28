"""
Envelope de comunicação. O agente não tem e-mail; o n8n é a secretária.

O agente escreve o papel, o worker põe na bandeja (POST), o n8n manda.
A resposta volta pelo endpoint do worker — nunca pelo resume URL do n8n,
para que uma execução do n8n morrer não deixe a pergunta órfã.
"""
import json, requests, datetime as dt
import config

TIPOS = ("question", "preview", "blocked", "done", "progress", "preflight")


def envelope(demanda, tipo, titulo, corpo_md, opcoes=None, default=None,
             anexos=None, msg_id=None, urgencia="normal"):
    assert tipo in TIPOS, f"tipo inválido: {tipo}"
    if tipo == "question" and not default:
        raise ValueError(
            "pergunta sem default trava a demanda para sempre. "
            "Toda question precisa de --default."
        )
    msg_id = msg_id or f"{demanda.id}-{tipo}-{int(dt.datetime.now().timestamp())}"
    return {
        "v": 1,
        "message_id": msg_id,
        "demand_id": demanda.id,
        "projeto": demanda.meta.get("projeto", ""),
        "titulo_demanda": demanda.meta.get("titulo", ""),
        "type": tipo,
        "to": "team",                     # NUNCA "requester"
        "urgencia": urgencia,
        "titulo": titulo,
        "body_md": corpo_md,
        "opcoes": opcoes or [],
        "default": default,
        "anexos": anexos or [],
        "reply_to": f"{config.WORKER_BASE_URL}/answer/{demanda.id}/{msg_id}",
        "rodada": demanda.rodada,
        "criado_em": dt.datetime.now().isoformat(timespec="seconds"),
    }


def enviar(env):
    """Falha de envio não pode derrubar a execução. O estado já está no disco."""
    try:
        r = requests.post(config.N8N_COMM_URL, json=env, timeout=15)
        r.raise_for_status()
        return True, ""
    except Exception as e:
        return False, str(e)
