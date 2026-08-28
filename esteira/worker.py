"""
Worker. Loop simples: pega uma demanda pronta, roda o agente, trata o
código de saída, para. Uma por vez.

Nada fica esperando resposta humana. Perguntou -> encerra. A retomada é
uma execução NOVA que lê a pasta. É por isso que retomar depois de 10
minutos ou de 3 dias é exatamente o mesmo código.
"""
import subprocess, time, os
from pathlib import Path
import config
from esteira.demanda import Demanda
from esteira import runner, comm, preflight, contas


def montar_prompt(d):
    """Contexto reconstruído do durável. Sem histórico de conversa."""
    projeto = d.meta.get("projeto", "_exemplo")
    partes = [
        (config.BASE_DIR / "AGENTS.md"),
        (config.BASE_DIR / "PADROES.md"),
        (config.BASE_DIR / "STACKS.md"),
        (config.PAPEIS_DIR / "orquestrador.md"),
        (config.PROJECTS_DIR / projeto / "AGENTS.md"),
    ]
    for nome in ("dominio.md", "decisoes.md", "armadilhas.md"):
        partes.append(config.PROJECTS_DIR / projeto / "context" / nome)

    blocos = []
    for p in partes:
        if p.exists():
            blocos.append(f"\n\n===== {p.relative_to(config.BASE_DIR)} =====\n{p.read_text(encoding='utf-8')}")

    blocos.append(f"\n\n===== DEMANDA #{d.id} =====\n" +
                  (d.dir / "README.md").read_text(encoding="utf-8"))

    pf = d.ler_json("preflight.json")
    if pf and pf.get("alertas"):
        blocos.append("\n\n===== PRE-FLIGHT — atenção =====\n" +
                      "\n".join(f"- {k}: {pf['respostas'][k]}" for k in pf["alertas"]))

    plano = d.dir / "plano.md"
    if plano.exists():
        blocos.append(f"\n\n===== SEU PLANO (rodada anterior) =====\n{plano.read_text(encoding='utf-8')}")

    fbs = sorted((d.dir / "feedback").glob("*.md"))
    if fbs:
        blocos.append("\n\n===== FEEDBACK — leia isto antes de tudo =====")
        for f in fbs:
            blocos.append(f"\n--- {f.name} ---\n{f.read_text(encoding='utf-8')}")

    qs = sorted((d.dir / "questions").glob("*.json"))
    if qs:
        blocos.append("\n\n===== PERGUNTAS E RESPOSTAS =====")
        for q in qs:
            a = d.dir / "answers" / f"{q.stem}.md"
            blocos.append(f"\nP{q.stem}: {q.read_text(encoding='utf-8')}")
            blocos.append(f"R{q.stem}: {a.read_text(encoding='utf-8') if a.exists() else '(sem resposta)'}")

    blocos.append(
        f"\n\n===== AGORA =====\n"
        f"Rodada {d.rodada + 1}. Seu workspace é o diretório atual.\n"
        f"A pasta da demanda está em {d.dir}.\n"
        f"Comece escrevendo plano.md. Depois execute.\n"
        f"Máximo {config.MAX_TURNOS} turnos.\n"
    )
    return "".join(blocos)


def preparar_workspace(d):
    ws = config.WORKSPACE_DIR / d.id
    ws.mkdir(parents=True, exist_ok=True)
    if not (ws / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=ws, check=False)
        subprocess.run(["git", "checkout", "-q", "-b", d.meta["branch"]], cwd=ws, check=False)
    return ws


def executar(d):
    rodada = d.rodada + 1
    d.set(rodada=rodada, run_iniciado_em_ts=time.time(), assinaturas=[])
    d.transicao("EXECUTANDO", f"rodada {rodada}")
    (d.dir / "rodadas" / str(rodada)).mkdir(parents=True, exist_ok=True)

    ws = preparar_workspace(d)
    prompt = montar_prompt(d)
    log = d.dir / "runs" / f"{rodada}.log"

    env_extra = {"ESTEIRA_DEMANDA": d.id, "ESTEIRA_DIR": str(config.BASE_DIR),
                 "PATH": os.environ.get("PATH", "") + f":{config.BASE_DIR / 'bin'}"}

    conta = contas.escolher("lead", dono_id=d.meta.get("dono"))
    quem = conta["nome"] if conta else "?"
    d.set(conta_atual={"nome": quem, "tipo": conta["tipo"], "chave": conta["chave"]} if conta else None)
    d.log("worker", f"iniciando rodada {rodada} no Claude de {quem}")

    res = runner.rodar("lead", prompt, cwd=ws, log_path=log,
                       timeout_s=config.TIMEOUT_RODADA_S, extra_env=env_extra,
                       conta=conta, on_start=lambda pid: d.set(pid=pid))
    d.set(pid=None)
    d.append_jsonl("execucoes.jsonl", {
        "rodada": rodada, "tier": "lead", "conta": quem,
        "codigo": res.codigo, "duracao_s": round(res.duracao_s),
        "timeout": res.timeout,
    })

    if res.perguntou:
        d.transicao("ESPERANDO_HUMANO", "agente perguntou")
    elif res.bloqueado:
        d.transicao("TRAVADA", "bloqueado por acesso externo")
    elif res.timeout:
        d.transicao("TRAVADA", "timeout da rodada")
    elif res.ok:
        # esteira-deliver já mudou o estado para EM_REVISAO.
        if d.estado == "EXECUTANDO":
            d.transicao("TRAVADA", "encerrou sem entregar nem perguntar")
    else:
        d.transicao("TRAVADA", f"código de saída {res.codigo}")

    d.log("worker", f"rodada {rodada} terminou: {res}")
    commit(d, f"chore: rodada {rodada} da demanda {d.id}")
    return res


def commit(d, mensagem):
    """Git é a verdade. Comita a cada passo; empurra se houver remote."""
    for caminho in (config.BASE_DIR, config.WORKSPACE_DIR / d.id):
        if not (Path(caminho) / ".git").exists():
            continue
        subprocess.run(["git", "add", "-A"], cwd=caminho, check=False,
                       capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", mensagem], cwd=caminho,
                       check=False, capture_output=True)
        subprocess.run(["git", "push", "-q", config.GIT_REMOTE, "HEAD"],
                       cwd=caminho, check=False, capture_output=True, timeout=60)


def ciclo():
    for d in Demanda.todas():
        if d.estado == "NOVA":
            d.transicao("PRE_FLIGHT")
            try:
                r = preflight.rodar(d)
                preflight.avisar(d, r)
            except Exception as e:
                d.log("pre-flight", f"falhou: {e}")
            d.transicao("PRONTA")
            return

    ocupadas = [d for d in Demanda.todas() if d.estado == "EXECUTANDO"]
    if len(ocupadas) >= config.DEMANDAS_SIMULTANEAS:
        return

    d = Demanda.proxima_da_fila()
    if d is None:
        return
    if d.rodada >= config.MAX_RODADAS:
        d.transicao("TRAVADA", f"chegou em {config.MAX_RODADAS} rodadas")
        return
    executar(d)


if __name__ == "__main__":
    config.LOGS_DIR.mkdir(exist_ok=True)
    print("worker de pé. ctrl-c para parar.")
    while True:
        try:
            ciclo()
        except Exception as e:
            with (config.LOGS_DIR / "worker.log").open("a") as f:
                f.write(f"{time.time()} erro: {e!r}\n")
        time.sleep(config.WORKER_INTERVALO_S)
