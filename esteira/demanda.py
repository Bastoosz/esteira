"""
A demanda é uma PASTA. Não há banco. O git é a verdade.

    demands/<id>/
      demanda.json      estado
      README.md         a demanda como chegou
      preflight.json    o que o pre-flight detectou
      plano.md          plano da rodada atual
      journal.md        registro (append-only)
      notas.jsonl       observações do agente
      decisoes.jsonl    decisões técnicas
      questions/N.json  perguntas
      answers/N.md      respostas
      feedback/rN.md    o que os humanos pediram
      rodadas/N/        artefatos da rodada
      outbox/           arquivos que vão anexos
      runs/N.log        transcript cru (efêmero, fica só no branch)
"""
import json, time, datetime as dt
from pathlib import Path
import config

ESTADOS = [
    "NOVA",              # chegou, ainda não passou pelo pre-flight
    "PRE_FLIGHT",        # rodando checklist
    "PRONTA",            # pode ser executada
    "EXECUTANDO",
    "ESPERANDO_HUMANO",  # esteira-ask; aguarda answers/
    "EM_REVISAO",        # preview enviado, aguardando aval
    "ASSUMIDA",          # humano pegou (falar com advogado, etc.)
    "TRAVADA",           # vigia detectou; precisa de decisão
    "ENTREGUE",
    "CANCELADA",
]


def agora():
    return dt.datetime.now().isoformat(timespec="seconds")


class Demanda:
    def __init__(self, id_):
        self.id = str(id_)
        self.dir = config.DEMANDS_DIR / self.id

    # ---------- criação ----------
    @classmethod
    def criar(cls, id_, titulo, projeto, corpo, origem="email", remetente=""):
        d = cls(id_)
        for sub in ("questions", "answers", "feedback", "rodadas", "outbox", "runs"):
            (d.dir / sub).mkdir(parents=True, exist_ok=True)
        d.escrever_json("demanda.json", {
            "id": d.id, "titulo": titulo, "projeto": projeto,
            "origem": origem, "remetente": remetente,
            "estado": "NOVA", "rodada": 0,
            "criada_em": agora(), "atualizada_em": agora(),
            "branch": f"{config.GIT_BRANCH_PREFIX}{d.id}",
            "pid": None, "run_iniciado_em": None,
        })
        (d.dir / "README.md").write_text(
            f"# {titulo}\n\n_{origem} · {remetente} · {agora()}_\n\n{corpo}\n",
            encoding="utf-8")
        (d.dir / "journal.md").write_text(f"# Journal — demanda {d.id}\n\n", encoding="utf-8")
        d.log("sistema", "demanda criada")
        return d

    # ---------- estado ----------
    @property
    def meta(self):
        return self.ler_json("demanda.json") or {}

    def set(self, **kw):
        m = self.meta
        m.update(kw)
        m["atualizada_em"] = agora()
        self.escrever_json("demanda.json", m)
        return m

    @property
    def estado(self):
        return self.meta.get("estado", "NOVA")

    @property
    def rodada(self):
        return int(self.meta.get("rodada", 0))

    def transicao(self, novo, motivo=""):
        assert novo in ESTADOS, f"estado inválido: {novo}"
        antigo = self.estado
        self.set(estado=novo)
        self.log("sistema", f"{antigo} -> {novo}" + (f" ({motivo})" if motivo else ""))

    # ---------- io ----------
    def ler_json(self, nome):
        p = self.dir / nome
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def escrever_json(self, nome, obj):
        p = self.dir / nome
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    def append_jsonl(self, nome, obj):
        obj = {"ts": agora(), **obj}
        with (self.dir / nome).open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        return obj

    def ler_jsonl(self, nome):
        p = self.dir / nome
        if not p.exists():
            return []
        out = []
        for linha in p.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                try:
                    out.append(json.loads(linha))
                except json.JSONDecodeError:
                    pass
        return out

    # ---------- journal ----------
    def log(self, ator, texto):
        """Registro automático. O agente não precisa lembrar de chamar."""
        with (self.dir / "journal.md").open("a", encoding="utf-8") as f:
            f.write(f"- `{agora()}` **{ator}** — {texto}\n")

    @property
    def ultimo_sinal(self):
        """Quando o journal foi tocado pela última vez. Base do vigia."""
        p = self.dir / "journal.md"
        return p.stat().st_mtime if p.exists() else 0

    # ---------- perguntas ----------
    def proxima_pergunta_id(self):
        return len(list((self.dir / "questions").glob("*.json"))) + 1

    def perguntas_abertas(self):
        abertas = []
        for q in sorted((self.dir / "questions").glob("*.json")):
            n = q.stem
            if not (self.dir / "answers" / f"{n}.md").exists():
                abertas.append(json.loads(q.read_text(encoding="utf-8")))
        return abertas

    def responder(self, n, texto, autor="equipe"):
        (self.dir / "answers" / f"{n}.md").write_text(
            f"<!-- {autor} · {agora()} -->\n\n{texto.strip()}\n", encoding="utf-8")
        self.log(autor, f"respondeu pergunta {n}")

    # ---------- listagem ----------
    @classmethod
    def todas(cls):
        if not config.DEMANDS_DIR.exists():
            return []
        out = []
        for p in sorted(config.DEMANDS_DIR.iterdir()):
            if p.is_dir() and not p.name.startswith("_") and (p / "demanda.json").exists():
                out.append(cls(p.name))
        return out

    @classmethod
    def proxima_da_fila(cls):
        for d in cls.todas():
            if d.estado == "PRONTA":
                return d
            if d.estado == "ESPERANDO_HUMANO" and not d.perguntas_abertas():
                return d
        return None

    @classmethod
    def novo_id(cls):
        ids = [int(d.id) for d in cls.todas() if d.id.isdigit()]
        return str(max(ids) + 1 if ids else 1001)
