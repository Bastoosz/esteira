"""
Board — Stack 1 (Flask + Jinja2 + HTMX + tokens do design system AM).

Só LÊ e MOSTRA. Nenhum agente roda aqui dentro: tarefa acima de 5 segundos
não fica num request HTTP. O worker é processo separado.

    python board.py     →  http://localhost:5000
"""
import subprocess, time, datetime as dt
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, abort

import config
from esteira.demanda import Demanda
from esteira import contas

app = Flask(__name__)

GRUPOS = [
    ("Executando",     ["EXECUTANDO"]),
    ("Esperando você",  ["ESPERANDO_HUMANO", "EM_REVISAO"]),
    ("Travado",        ["TRAVADA"]),
    ("Fila",           ["NOVA", "PRE_FLIGHT", "PRONTA"]),
    ("Assumido",       ["ASSUMIDA"]),
]


def _humano(segundos):
    s = int(segundos)
    if s < 60:   return f"{s}s"
    if s < 3600: return f"{s // 60}min"
    if s < 86400: return f"{s // 3600}h{(s % 3600) // 60:02d}"
    return f"{s // 86400}d"


def _cartao(d):
    m = d.meta
    silencio = time.time() - d.ultimo_sinal
    notas = d.ler_jsonl("notas.jsonl")
    eventos = []
    j = d.dir / "journal.md"
    if j.exists():
        eventos = [l[2:] for l in j.read_text(encoding="utf-8").splitlines()
                   if l.startswith("- ")][-6:][::-1]
    conta = m.get("conta_atual") or {}
    return {
        "id": d.id,
        "titulo": m.get("titulo", ""),
        "projeto": m.get("projeto", ""),
        "estado": d.estado,
        "rodada": d.rodada,
        "dono": m.get("dono", ""),
        "conta": conta.get("nome", ""),
        "conta_tipo": conta.get("tipo", ""),
        "silencio": silencio,
        "silencio_txt": _humano(silencio),
        "vivo": d.estado == "EXECUTANDO" and silencio < config.SEM_SINAL_ALERTA_S,
        "eventos": eventos,
        "notas": notas[-4:][::-1],
        "perguntas": d.perguntas_abertas(),
        "anexos": [f.name for f in sorted((d.dir / "outbox").glob("*"))],
        "alertas": (d.ler_json("preflight.json") or {}).get("alertas", []),
    }


@app.route("/")
def inicio():
    cartoes = [_cartao(d) for d in Demanda.todas()]
    por_grupo = []
    for titulo, estados in GRUPOS:
        itens = [c for c in cartoes if c["estado"] in estados]
        if itens:
            por_grupo.append((titulo, itens))
    entregues = [c for c in cartoes if c["estado"] == "ENTREGUE"]
    return render_template("board.html", grupos=por_grupo, entregues=entregues,
                           contas=contas.resumo(), agora=dt.datetime.now())


@app.route("/_live")
def live():
    """Partial recarregado por HTMX a cada 3s. Só o que muda."""
    cartoes = [_cartao(d) for d in Demanda.todas()]
    por_grupo = []
    for titulo, estados in GRUPOS:
        itens = [c for c in cartoes if c["estado"] in estados]
        if itens:
            por_grupo.append((titulo, itens))
    return render_template("_partials/grupos.html", grupos=por_grupo,
                           agora=dt.datetime.now())


@app.route("/d/<id_>")
def detalhe(id_):
    d = Demanda(id_)
    if not d.dir.exists():
        abort(404)
    j = d.dir / "journal.md"
    return render_template("detalhe.html", c=_cartao(d), d=d,
                           journal=j.read_text(encoding="utf-8") if j.exists() else "",
                           plano=(d.dir / "plano.md").read_text(encoding="utf-8")
                                 if (d.dir / "plano.md").exists() else "",
                           execucoes=d.ler_jsonl("execucoes.jsonl"),
                           delegacoes=d.ler_jsonl("delegacoes.jsonl"),
                           decisoes=d.ler_jsonl("decisoes.jsonl"))


@app.route("/numeros")
def numeros():
    """10 demandas/mês não tem conteúdo estatístico. É tabela, não gráfico."""
    linhas = []
    for d in Demanda.todas():
        m = d.meta
        execs = d.ler_jsonl("execucoes.jsonl")
        linhas.append({
            "id": d.id, "titulo": m.get("titulo", ""), "projeto": m.get("projeto", ""),
            "estado": d.estado, "rodadas": d.rodada,
            "perguntas": len(list((d.dir / "questions").glob("*.json"))),
            "delegacoes": len(d.ler_jsonl("delegacoes.jsonl")),
            "contas": sorted({e.get("conta", "?") for e in execs}),
            "criada": m.get("criada_em", "")[:10],
            "primeiro_commit_humano": m.get("commit_humano", ""),
        })
    return render_template("numeros.html", linhas=linhas, contas=contas.resumo())


@app.route("/answer/<id_>/<msg_id>", methods=["POST"])
def responder(id_, msg_id):
    """
    Endpoint que o n8n chama quando a resposta chega por e-mail.
    O reply_to do envelope aponta para AQUI, não para o resume URL do n8n —
    assim uma execução do n8n morrer não deixa a pergunta órfã.
    """
    d = Demanda(id_)
    if not d.dir.exists():
        abort(404)
    dados = request.get_json(silent=True) or request.form
    texto = (dados.get("resposta") or dados.get("texto") or "").strip()
    autor = dados.get("autor", "equipe")
    if not texto:
        return {"ok": False, "erro": "resposta vazia"}, 400

    n = msg_id.split("-")[-1]
    if (d.dir / "answers" / f"{n}.md").exists():
        return {"ok": True, "nota": "resposta já registrada (idempotente)"}
    d.responder(n, texto, autor)
    if not d.perguntas_abertas():
        d.transicao("PRONTA", "todas as perguntas respondidas")
    return {"ok": True}


@app.route("/acao/<id_>/<acao>", methods=["POST"])
def acao(id_, acao):
    d = Demanda(id_)
    if not d.dir.exists():
        abort(404)
    if acao == "continuar":
        d.transicao("PRONTA", "humano mandou continuar")
    elif acao == "recomecar":
        d.set(rodada=max(0, d.rodada - 1))
        d.transicao("PRONTA", "humano mandou recomeçar a rodada")
    elif acao == "assumir":
        d.transicao("ASSUMIDA", "humano assumiu")
    elif acao == "devolver":
        d.transicao("PRONTA", "humano devolveu para a esteira")
    elif acao == "cancelar":
        d.transicao("CANCELADA", "humano cancelou")
    elif acao == "aprovar":
        d.transicao("ENTREGUE", "aprovado")
    elif acao == "mudancas":
        texto = request.form.get("texto", "").strip()
        n = len(list((d.dir / "feedback").glob("*.md"))) + 1
        (d.dir / "feedback" / f"r{n}.md").write_text(
            f"<!-- rodada {d.rodada} -->\n\n{texto}\n", encoding="utf-8")
        d.log("equipe", f"pediu mudanças: {texto[:80]}")
        d.transicao("PRONTA", "mudanças pedidas")
    else:
        abort(400)
    return redirect(request.referrer or url_for("inicio"))


@app.route("/fixar/<id_>/<int:idx>", methods=["POST"])
def fixar(id_, idx):
    """Nota efêmera vira conhecimento permanente do projeto."""
    d = Demanda(id_)
    notas = d.ler_jsonl("notas.jsonl")
    if idx >= len(notas):
        abort(404)
    texto = notas[idx]["texto"]
    projeto = d.meta.get("projeto", "_exemplo")
    alvo = config.PROJECTS_DIR / projeto / "context" / "armadilhas.md"
    alvo.parent.mkdir(parents=True, exist_ok=True)
    if not alvo.exists():
        alvo.write_text("# Armadilhas\n\n", encoding="utf-8")
    with alvo.open("a", encoding="utf-8") as f:
        f.write(f"- {texto}  \n  _(demanda #{d.id}, {dt.date.today()})_\n")
    d.log("equipe", f"fixou nota em {projeto}/context/armadilhas.md")
    return redirect(request.referrer or url_for("inicio"))


@app.template_filter("curto")
def curto(s, n=90):
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + "…"


if __name__ == "__main__":
    config.LOGS_DIR.mkdir(exist_ok=True)
    app.run(host="0.0.0.0", port=config.BOARD_PORT, debug=config.DEBUG)
