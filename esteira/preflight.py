"""
Pre-flight: 6 perguntas fechadas antes de qualquer trabalho.

Texto entra, JSON sai. Não toca arquivo. Logo: modelo free direto, sem
agente. ~3 segundos, sem parsear log de CLI.

Não bloqueia. Informa.
"""
import config
from esteira import llm, comm

SISTEMA = ("Você é um triador técnico de um escritório de advocacia. "
           "Seja conservador: na dúvida responda 'talvez'.")

PROMPT = """Leia a demanda e responda cada item com "sim", "nao" ou "talvez",
mais uma frase curta em "nota" dizendo o que especificamente vai ser preciso.

{perguntas}

Formato: {{"credencial":{{"r":"nao","nota":""}}, "certificado":{{...}}, ...}}

DEMANDA:
---
{demanda}
---"""


def rodar(demanda):
    perguntas = "\n".join(f'- "{k}": {p}' for k, p in config.PREFLIGHT_PERGUNTAS)
    texto = (demanda.dir / "README.md").read_text(encoding="utf-8")[:6000]

    try:
        dados, modelo = llm.chamar_json(
            PROMPT.format(perguntas=perguntas, demanda=texto), SISTEMA)
    except Exception as e:
        # Free caiu ou devolveu lixo: marca tudo como 'talvez'. Conservador
        # de propósito — pre-flight que falha em silêncio é pior que ausente.
        demanda.log("pre-flight", f"falhou ({e}); assumindo 'talvez' em tudo")
        dados = {k: {"r": "talvez", "nota": "pre-flight não respondeu"}
                 for k, _ in config.PREFLIGHT_PERGUNTAS}
        modelo = "nenhum"

    alertas = [k for k, v in dados.items()
               if isinstance(v, dict) and v.get("r") in ("sim", "talvez")]
    resultado = {"respostas": dados, "alertas": alertas, "modelo": modelo}
    demanda.escrever_json("preflight.json", resultado)
    demanda.log("pre-flight", f"[{modelo}] alertas: {', '.join(alertas) or 'nenhum'}")
    return resultado


def avisar(demanda, resultado):
    if not resultado["alertas"]:
        return
    mapa = dict(config.PREFLIGHT_PERGUNTAS)
    linhas = ["Esta demanda provavelmente vai esbarrar em algo. O agente "
              "vai começar mesmo assim — isto é só um aviso.\n"]
    for k in resultado["alertas"]:
        v = resultado["respostas"][k]
        linhas.append(f"- **{mapa.get(k, k)}** → _{v.get('r')}_ — {v.get('nota','')}")
    comm.enviar(comm.envelope(
        demanda, "preflight",
        f"#{demanda.id} pode precisar de algo — {demanda.meta.get('titulo','')}",
        "\n".join(linhas)))
