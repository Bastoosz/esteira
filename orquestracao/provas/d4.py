#!/usr/bin/env python3
"""
Prova do D4 — semear o hub com o que já existe no disco.

O ponto do item: o consumo de ontem tem que aparecer sem ninguém digitar
nada. Se semear exigir digitação, não é semeadura, é cadastro.
"""
import json, sys, tempfile, pathlib
RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
falhas = []


def checa(nome, cond, detalhe=""):
    print(f"  {'ok  ' if cond else 'FALHA'} {nome}" + (f" — {detalhe}" if detalhe and not cond else ""))
    if not cond:
        falhas.append(nome)


from esteira.hub import db, semear

tmp = pathlib.Path(tempfile.mkdtemp()) / "hub.db"
con = db.abrir(tmp); db.migrar(con)

print("== fontes que existem de verdade neste repo ==")
fontes = {
    "orquestracao/despachos.jsonl": RAIZ / "orquestracao/despachos.jsonl",
    "logs/contas-estado.json": RAIZ / "logs/contas-estado.json",
}
for nome, p in fontes.items():
    checa(f"{nome} existe para semear", p.exists(), "não existe — semeadura não teria o que ler")

print("== semeia sem digitação ==")
n = semear.tudo(con, raiz=RAIZ)
checa("semear.tudo() devolve quantos gravou", isinstance(n, int), str(type(n)))
linhas = db.execucoes(con)
checa("gravou execuções do disco", len(linhas) > 0, f"{len(linhas)} linhas")

print("== idempotente: semear duas vezes não duplica ==")
antes = len(db.execucoes(con))
semear.tudo(con, raiz=RAIZ)
depois = len(db.execucoes(con))
checa("segunda semeadura não duplica", antes == depois, f"{antes} -> {depois}")

print("== o despacho de ontem aparece ==")
desp = RAIZ / "orquestracao/despachos.jsonl"
if desp.exists():
    ids = set()
    for l in desp.read_text(encoding="utf-8").splitlines():
        if l.strip():
            ids.add(json.loads(l).get("task_id"))
    achados = {r.get("task_id") for r in db.execucoes(con)}
    faltando = ids - achados
    checa("todo task_id do despachos.jsonl está no hub", not faltando, f"faltou {sorted(faltando)[:5]}")

print("== nada de segredo entrou ==")
bruto = json.dumps(db.execucoes(con), ensure_ascii=False, default=str).lower()
vazou = [p for p in ("sk-", "token", "secret", "senha", "password", "credential") if p in bruto]
checa("nenhuma palavra de segredo nas linhas semeadas", not vazou, str(vazou))
con.close()

print()
if falhas:
    print(f"FALHOU em {len(falhas)}: {', '.join(falhas)}"); sys.exit(1)
print("D4: tudo passou")
