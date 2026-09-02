"""
Maestro — fila, vagas e o laço `tick`.

Isto NÃO é um agent loop. Não há decisão de modelo aqui, não há
roteamento, não há retentativa automática. É contabilidade: uma fila em
jsonl, quatro vagas em json, e um veredito que vem do disco.

As duas peças difíceis já existiam e não se reescrevem aqui:

    runner.rodar   roda um CLI com conta, timeout e log
    _foto          assinatura do escopo — o oráculo objetivo

REGRA QUE GOVERNA O ARQUIVO
    A prosa do executor não é o veredito.
    O veredito é (a) o que mudou no disco e (b) a prova que rodou.

Foi medido: o relatório de um worker disse que os testes não rodaram; à
mão, 822 passaram. Os dois estavam certos — o sandbox do codex não tem
rede, o shell tem. Se você algum dia ler o stdout de um CLI para decidir
algo aqui, criou o bug que vai te assombrar.
"""
import fcntl, glob, json, os, signal, subprocess, sys, time
import datetime as dt
from pathlib import Path

import config

DIR = config.BASE_DIR / "orquestracao"
FILA = DIR / "fila.jsonl"
ESTADO = DIR / "estado.json"
DESPACHOS = DIR / "despachos.jsonl"
JOURNAL = DIR / "JOURNAL.md"
LOCK = DIR / ".tick.lock"
ESTADO_LOCK = DIR / ".estado.lock"

# Tiers que a bancada despacha. `claude*` é trabalho do maestro, não vaga.
TIERS_VAGA = ("codex", "opencode", "agy")


def agora():
    return dt.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- oráculo
def foto(padrao, raiz=None):
    """
    Assinatura do que existe no escopo agora: caminho -> tamanho:mtime.

    Mesma forma do `_foto` do bin/esteira-delegate, de propósito: é o que
    permite julgar opencode e agy, que reclamam de crédito, trabalham, e
    devolvem código de saída que não vale nada.

    `padrao` aceita vários globs separados por vírgula. Glob que começa com
    `/` é tratado como absoluto.

    O QUE ESTE ORÁCULO NÃO VÊ — e foi medido, não suposto:

    1. **Escrita fora dos globs do escopo.** Em 02/09 o opencode criou
       `~/bin/esteira-venv-python` numa tarefa de escopo `deploy/**`. A
       foto não viu, `fora_do_escopo()` não acusou, e o unit só falharia
       na máquina de outra pessoa. Por isso todo briefing tem que dizer
       "não escreva fora do repo", e é o revisor humano que confere.
    2. **Mudança que preserva tamanho E segundo do mtime.** O mtime é
       truncado a segundo. Reescrita rápida do mesmo conteúdo em bytes
       iguais é invisível. Na prática não morde (executor demora mais que
       um segundo), mas não é garantia — é probabilidade.

    Ou seja: disco mexeu é prova de que ALGO foi feito. Disco não mexeu
    NÃO é prova de que nada foi feito. O veredito final é a prova rodando.
    """
    raiz = Path(raiz or config.BASE_DIR)
    itens = {}
    for parte in (padrao or "**/*").split(","):
        parte = parte.strip()
        if not parte:
            continue
        alvo = parte if parte.startswith("/") else str(raiz / parte)
        for p in glob.glob(alvo, recursive=True):
            pp = Path(p)
            if pp.is_file() and ".git" not in pp.parts:
                st = pp.stat()
                itens[p] = f"{st.st_size}:{int(st.st_mtime)}"
    return itens


def diff_foto(antes, depois):
    mudou = sorted(k for k in depois if antes.get(k) != depois[k])
    sumiu = sorted(set(antes) - set(depois))
    return mudou, sumiu


def fora_do_escopo(caminhos, padrao, raiz=None):
    """Arquivo que mudou e não casa com nenhum glob do escopo."""
    if not padrao:
        return []
    raiz = Path(raiz or config.BASE_DIR)
    globs = [g.strip() for g in padrao.split(",") if g.strip()]
    fora = []
    for c in caminhos:
        try:
            rel = str(Path(c).relative_to(raiz))
        except ValueError:
            # fora da raiz do repo: sempre violação, e sempre reportado
            fora.append(str(c))
            continue
        if not any(Path(rel).match(g) or rel.startswith(g.split("*")[0])
                   for g in globs):
            fora.append(rel)
    return fora


# ------------------------------------------------------------------- io
def ler_fila():
    if not FILA.exists():
        return []
    out = []
    for linha in FILA.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            out.append(json.loads(linha))
    return out


def escrever_fila(itens):
    FILA.parent.mkdir(parents=True, exist_ok=True)
    with FILA.open("w", encoding="utf-8") as f:
        for i in itens:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")


def ler_estado():
    if ESTADO.exists():
        try:
            return json.loads(ESTADO.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"atualizado_em": agora(),
            "vagas": [{"vaga": n, "tier": t, "task_id": None, "pid": None,
                       "iniciado_em": None, "escopo": None, "conta": None}
                      for n, t in ((1, "codex"), (2, "codex"),
                                   (3, "opencode"), (4, "agy"))]}


def escrever_estado(e):
    e["atualizado_em"] = agora()
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")


def journal(texto, motivo=""):
    """O porquê. Os comandos já registram o que aconteceu."""
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    if not JOURNAL.exists():
        JOURNAL.write_text("# Journal da orquestração\n\n"
                           "O que os comandos não registram: o motivo.\n\n",
                           encoding="utf-8")
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(f"- `{agora()}` {texto}" + (f" — **por quê:** {motivo}" if motivo else "") + "\n")


class trava:
    """
    Lock de arquivo em volta de read-modify-write.

    Existe porque quatro despachos em paralelo mexem no MESMO estado.json e
    na MESMA fila.jsonl. Sem isto, dois processos leem o mesmo estado, cada
    um reserva a vaga que acha livre, e um sobrescreve o outro — o tipo de
    perda que ninguém nota até faltar um despacho no fim do dia.

    Reentrante no mesmo processo: `tick` já segura o lock quando chama
    `dispatch`, que segura de novo.
    """
    _fh = None
    _n = 0

    def __enter__(self):
        cls = type(self)
        if cls._n == 0:
            DIR.mkdir(parents=True, exist_ok=True)
            cls._fh = ESTADO_LOCK.open("w")
            fcntl.flock(cls._fh, fcntl.LOCK_EX)
        cls._n += 1
        return self

    def __exit__(self, *exc):
        cls = type(self)
        cls._n -= 1
        if cls._n == 0 and cls._fh is not None:
            fcntl.flock(cls._fh, fcntl.LOCK_UN)
            cls._fh.close()
            cls._fh = None
        return False


def item(fila, task_id):
    return next((i for i in fila if i["id"] == task_id), None)


def marcar(task_id, **kw):
    with trava():
        fila = ler_fila()
        it = item(fila, task_id)
        if it is None:
            return None
        it.update(kw)
        escrever_fila(fila)
        return it


# -------------------------------------------------------------- vereditos
def _vivo(pid):
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def escopos_ativos(estado):
    return [v["escopo"] for v in estado["vagas"] if v["task_id"] and v["escopo"]]


def cruza(escopo, ativos):
    """Dois escopos cruzam se compartilham qualquer glob. Conservador."""
    meus = {g.strip() for g in (escopo or "").split(",") if g.strip()}
    for a in ativos:
        outros = {g.strip() for g in (a or "").split(",") if g.strip()}
        if meus & outros:
            return True
        # prefixo de diretório em comum também conta
        for m in meus:
            for o in outros:
                if m.split("/")[0] == o.split("/")[0] and m.split("/")[0] not in ("", "**"):
                    return True
    return False


def prereq_ok(it, fila):
    return all((item(fila, p) or {}).get("estado") == "feito"
               for p in it.get("prereq", []))


# -------------------------------------------------------------- despacho
def dispatch(task_id, vaga=None, timeout_s=None):
    """
    Despacha um item da fila. Bloqueante: quem chama decide se roda em
    segundo plano. Devolve o registro do despacho.
    """
    from esteira import runner, contas

    fila = ler_fila()
    it = item(fila, task_id)
    if it is None:
        raise SystemExit(f"[maestro] task {task_id} não está na fila")
    if it["tier"] not in TIERS_VAGA:
        raise SystemExit(f"[maestro] tier '{it['tier']}' não é de vaga; "
                         f"é trabalho do maestro")
    if not prereq_ok(it, fila):
        raise SystemExit(f"[maestro] {task_id} tem pré-requisito não fechado: "
                         f"{it.get('prereq')}")

    briefing = DIR / "briefings" / f"{task_id}.md"
    if not briefing.exists():
        raise SystemExit(f"[maestro] sem briefing em {briefing}. "
                         f"Briefing é arquivo, não argumento solto.")

    conta = contas.escolher(it["tier"])
    log = DIR / "logs" / f"{task_id}.log"

    # Seção crítica: escolher a vaga, conferir cruzamento de escopo e
    # reservar tem que ser atômico. Dois despachos em paralelo lendo o
    # mesmo estado reservariam a mesma vaga.
    with trava():
        estado = ler_estado()
        if vaga is None:
            livre = next((v for v in estado["vagas"]
                          if v["tier"] == it["tier"] and not v["task_id"]), None)
            if livre is None:
                raise SystemExit(f"[maestro] nenhuma vaga livre de tier {it['tier']}")
            vaga = livre["vaga"]
        v = next(x for x in estado["vagas"] if x["vaga"] == vaga)
        if v["task_id"]:
            raise SystemExit(f"[maestro] vaga {vaga} já tem {v['task_id']} em voo")

        ativos = [e for e in escopos_ativos(estado) if e != it["escopo"]]
        if cruza(it["escopo"], ativos):
            raise SystemExit(f"[maestro] escopo '{it['escopo']}' cruza com vaga ativa. "
                             f"Dois executores no mesmo arquivo é como se perde trabalho "
                             f"sem ninguém notar.")

        v.update(task_id=task_id, escopo=it["escopo"], iniciado_em=agora(),
                 conta=(conta or {}).get("chave"))
        escrever_estado(estado)
        marcar(task_id, estado="em_voo", vaga=vaga, despachado_em=agora())

    antes = foto(it["escopo"])

    t0 = time.time()
    res = runner.rodar(it["tier"], briefing.read_text(encoding="utf-8"),
                       cwd=config.BASE_DIR, log_path=log,
                       timeout_s=timeout_s or config.TIMEOUT_RODADA_S,
                       conta=conta,
                       on_start=lambda pid: _anotar_pid(vaga, pid))

    depois = foto(it["escopo"])
    mudou, sumiu = diff_foto(antes, depois)
    fora = fora_do_escopo(mudou, it["escopo"])

    reg = {
        "ts": agora(), "task_id": task_id, "vaga": vaga, "tier": it["tier"],
        "conta": (conta or {}).get("chave"), "codigo": res.codigo,
        "duracao_s": round(res.duracao_s), "timeout": res.timeout,
        "exit_confiavel": res.exit_confiavel,
        "arquivos_mudados": len(mudou), "arquivos_removidos": len(sumiu),
        "fora_do_escopo": fora, "log": str(log),
        # veredito PARCIAL: disco mexeu. A prova ainda tem que rodar.
        "tocou_disco": bool(mudou or sumiu),
    }
    with DESPACHOS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")

    with trava():
        estado = ler_estado()
        v = next(x for x in estado["vagas"] if x["vaga"] == vaga)
        v.update(task_id=None, pid=None, iniciado_em=None, escopo=None, conta=None)
        escrever_estado(estado)

    marcar(task_id, estado="a_colher", codigo=res.codigo,
           tocou_disco=reg["tocou_disco"], arquivos_mudados=len(mudou),
           duracao_s=round(res.duracao_s), fora_do_escopo=fora)
    journal(f"`{task_id}` voltou de {it['tier']} — código {res.codigo}, "
            f"{len(mudou)} arquivo(s) mudado(s), {round(time.time()-t0)}s",
            "a prova ainda não rodou; estado a_colher")
    return reg


def _anotar_pid(vaga, pid):
    with trava():
        e = ler_estado()
        v = next((x for x in e["vagas"] if x["vaga"] == vaga), None)
        if v:
            v["pid"] = pid
            escrever_estado(e)


# --------------------------------------------------------------- colher
def colher(task_id=None):
    """
    Fecha o que voltou. NÃO lê o relatório do executor: roda a prova.

    Classifica em FEITO / REFAZER / ESCALAR:
      não tocou o disco            -> REFAZER (suspeite do ambiente)
      tocou fora do escopo         -> ESCALAR (violação; humano olha)
      tocou e a prova passou       -> FEITO
      tocou e a prova falhou       -> REFAZER
      duas voltas erradas          -> ESCALAR (o maestro faz a terceira)
    """
    fila = ler_fila()
    alvos = [i for i in fila
             if i.get("estado") == "a_colher" and (task_id is None or i["id"] == task_id)]
    out = []
    for it in alvos:
        tentativas = int(it.get("tentativas", 0)) + 1
        if not it.get("tocou_disco"):
            veredito, nota = "REFAZER", ("nada mudou no disco — suspeite do ambiente "
                                         "antes da tarefa: modelo free fora do ar, "
                                         "credencial vencida, CLI sem link")
        elif it.get("fora_do_escopo"):
            veredito, nota = "ESCALAR", (f"tocou fora do escopo: "
                                         f"{it['fora_do_escopo'][:5]}")
        else:
            veredito, nota = "FEITO", "disco mexeu dentro do escopo; rode a prova"
        if veredito == "REFAZER" and tentativas >= 2:
            veredito, nota = "ESCALAR", (f"{tentativas} voltas sem fechar — "
                                         f"o maestro faz a terceira, não delega")
        novo = {"FEITO": "a_provar", "REFAZER": "pronta", "ESCALAR": "escalada"}[veredito]
        marcar(it["id"], estado=novo, tentativas=tentativas,
               veredito_colheita=veredito, nota_colheita=nota)
        journal(f"`{it['id']}` colhido: **{veredito}**", nota)
        out.append({"task_id": it["id"], "veredito": veredito, "nota": nota,
                    "estado": novo, "tentativas": tentativas})
    return out


# --------------------------------------------------------------- doctor
def doctor():
    """
    Smoke dos runtimes E das contas. As duas coisas, e não é firula.

    PONTO CEGO QUE ISTO CONSERTA, medido em 02/09: testar o tier `lead`
    SEM conta usa o `~/.claude` do host, que está válido, e imprime OK —
    enquanto a credencial da esteira em `~/.esteira-auth/nicolas/claude`
    estava com o OAuth expirado:

        Failed to authenticate: OAuth session expired and could not be refreshed

    Um doctor que diz OK com a conta de produção morta é pior que doctor
    nenhum. Por isso cada tier com conta individual é testado uma vez sem
    conta (o CLI existe e responde?) e uma vez POR CONTA ativa (a
    assinatura que vai pagar a execução ainda autentica?).
    """
    from esteira import runner, contas
    linhas = []
    for tier in ("lead", "codex", "opencode", "agy"):
        tipo = contas.TIER_CONTA.get(tier)
        try:
            ok, r = runner.smoke_test(tier)
            linhas.append({"tier": tier, "conta": None, "ok": bool(ok),
                           "codigo": r.codigo, "duracao_s": round(r.duracao_s),
                           "exit_confiavel": r.exit_confiavel,
                           "nota": "sem conta — só diz se o CLI existe e responde"})
        except Exception as e:
            linhas.append({"tier": tier, "conta": None, "ok": False,
                           "codigo": None, "erro": str(e)[:160]})
        if not tipo:
            continue
        ativas = contas.disponiveis(tipo)
        if not ativas:
            linhas.append({"tier": tier, "conta": "(nenhuma)", "ok": False,
                           "codigo": None,
                           "erro": f"nenhuma conta '{tipo}' ativa e fora de cooldown"})
        for c in ativas:
            try:
                ok, r = runner.smoke_test(tier, c)
                linhas.append({"tier": tier, "conta": c["chave"], "ok": bool(ok),
                               "codigo": r.codigo, "duracao_s": round(r.duracao_s),
                               "exit_confiavel": r.exit_confiavel})
            except Exception as e:
                linhas.append({"tier": tier, "conta": c["chave"], "ok": False,
                               "codigo": None, "erro": str(e)[:160]})
    return {"runtimes": linhas, "contas": contas.resumo(),
            "politica": config.POLITICA_CONTA}


# ----------------------------------------------------------------- tick
def tick(despachar=True):
    """
    Idempotente e seguro em cron: lock de arquivo. Rodar duas vezes junto
    não despacha duas vezes.

    Este tick NÃO despacha em segundo plano — despacho é bloqueante de
    propósito. Em cron, use `--sem-despachar` e despache à mão, ou aceite
    que o tick demora o tempo da tarefa.
    """
    DIR.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as trava:
        try:
            fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"erro": "outro tick em andamento", "colhido": [], "despachado": []}

        colhido = colher()
        despachado = []
        if despachar:
            fila = ler_fila()
            estado = ler_estado()
            for v in estado["vagas"]:
                if v["task_id"]:
                    continue
                ativos = escopos_ativos(ler_estado())
                cand = next((i for i in ler_fila()
                             if i.get("estado") == "pronta"
                             and i["tier"] == v["tier"]
                             and prereq_ok(i, ler_fila())
                             and not cruza(i["escopo"], ativos)), None)
                if cand is None:
                    continue
                try:
                    reg = dispatch(cand["id"], vaga=v["vaga"])
                    despachado.append(reg)
                except SystemExit as e:
                    journal(f"não despachou `{cand['id']}`", str(e))
        return {"colhido": colhido, "despachado": despachado}
