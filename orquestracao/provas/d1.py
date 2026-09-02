#!/usr/bin/env python3
"""
Prova do D1 — hub: esquema e endpoints.

Escrita pelo maestro, não pelo executor. A prova é o contrato do que
"feito" significa; quem implementa faz ela passar, não a redefine.

Sai 0 se tudo passar. Qualquer falha sai != 0 e o item volta para `pronta`.
"""
import json, sqlite3, sys, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

falhas = []


def checa(nome, cond, detalhe=""):
    print(f"  {'ok  ' if cond else 'FALHA'} {nome}" + (f" — {detalhe}" if detalhe and not cond else ""))
    if not cond:
        falhas.append(nome)


print("== esquema ==")
from esteira.hub import db

tmp = pathlib.Path(tempfile.mkdtemp()) / "hub.db"
con = db.abrir(tmp)
db.migrar(con)
tabelas = set(db.tabelas(con))
checa("as tres tabelas existem", {"execucoes", "contas", "eventos"} <= tabelas, str(tabelas))

# migrar duas vezes não pode quebrar: o hub reinicia
db.migrar(con)
checa("migrar e idempotente", True)

db.gravar_execucao(con, {"pessoa": "nicolas", "runtime": "codex", "tier": "codex",
                         "task_id": "D1", "duracao_s": 12, "codigo": 0,
                         "arquivos_mudados": 3, "veredito": "FEITO"})
con.close()

# persistência de verdade: reabrir o arquivo
con2 = db.abrir(tmp)
linhas = db.execucoes(con2)
checa("execucao persistiu depois de fechar e reabrir", len(linhas) == 1, f"{len(linhas)} linhas")

print("== nada de segredo no esquema ==")
cols = set()
for t in ("execucoes", "contas", "eventos"):
    cols |= {c.lower() for c in db.colunas(con2, t)}
proibidas = {c for c in cols if any(p in c for p in
             ("token", "secret", "senha", "password", "credential", "auth", "apikey", "api_key"))}
checa("nenhuma coluna com cara de segredo", not proibidas, str(proibidas))
con2.close()

print("== endpoints ==")
import board
c = board.app.test_client()

r = c.post("/telemetria", json={"pessoa": "nicolas", "runtime": "codex", "tier": "codex",
                                "duracao_s": 7, "codigo": 0, "arquivos_mudados": 1})
checa("POST /telemetria aceita", r.status_code in (200, 201), f"http {r.status_code}")

r = c.post("/contas/estado", json={"pessoa": "nicolas", "runtime": "codex",
                                   "estado": "viva", "ultimo_smoke_ok": True})
checa("POST /contas/estado aceita", r.status_code in (200, 201), f"http {r.status_code}")

r = c.get("/api/consumo?pessoa=nicolas")
checa("GET /api/consumo responde 200", r.status_code == 200, f"http {r.status_code}")
try:
    corpo = r.get_json()
    checa("GET /api/consumo devolve JSON", corpo is not None)
except Exception as e:
    checa("GET /api/consumo devolve JSON", False, str(e))

print("== payload invalido nao derruba ==")
r = c.post("/telemetria", json={"lixo": True})
checa("payload invalido devolve 4xx, nao 500", 400 <= r.status_code < 500, f"http {r.status_code}")

print("== rotas antigas continuam de pe ==")
for rota in ("/", "/numeros", "/orquestracao"):
    r = c.get(rota)
    checa(f"regressao {rota}", r.status_code == 200, f"http {r.status_code}")

print()
if falhas:
    print(f"FALHOU em {len(falhas)}: {', '.join(falhas)}")
    sys.exit(1)
print("D1: tudo passou")
