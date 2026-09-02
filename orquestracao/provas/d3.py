#!/usr/bin/env python3
"""
Prova do D3 — runner e maestro reportam ao hub, best-effort.

A regra que esta prova defende é a mais importante do item:

    HUB FORA DO AR NÃO PODE DERRUBAR EXECUÇÃO.

O padrão já existe nesta casa e funcionou: a `sentinela.py` tentou falar com
o n8n desligado, tratou a falha e saiu 0. O reporte copia esse padrão — e
acrescenta fila local, para que o dado não se perca, só atrase.
"""
import json, sys, tempfile, pathlib, time

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

falhas = []


def checa(nome, cond, detalhe=""):
    print(f"  {'ok  ' if cond else 'FALHA'} {nome}" + (f" — {detalhe}" if detalhe and not cond else ""))
    if not cond:
        falhas.append(nome)


from esteira.hub import reporte

tmp = pathlib.Path(tempfile.mkdtemp())
fila_local = tmp / "pendentes.jsonl"

print("== hub fora do ar: enfileira e NÃO levanta ==")
try:
    r = reporte.enviar({"pessoa": "nicolas", "runtime": "codex", "duracao_s": 5,
                        "codigo": 0, "arquivos_mudados": 2},
                       url="http://127.0.0.1:9/nao-existe", fila=fila_local)
    checa("enviar() com hub morto não levanta exceção", True)
    checa("enviar() devolve que falhou", r is False or (isinstance(r, tuple) and not r[0]))
except Exception as e:
    checa("enviar() com hub morto não levanta exceção", False, f"{type(e).__name__}: {e}")

checa("gravou na fila local", fila_local.exists() and fila_local.read_text().strip() != "")

print("== a fila local acumula, não sobrescreve ==")
for i in range(3):
    reporte.enviar({"pessoa": "nicolas", "runtime": "codex", "duracao_s": i},
                   url="http://127.0.0.1:9/nao-existe", fila=fila_local)
linhas = [l for l in fila_local.read_text().splitlines() if l.strip()]
checa("quatro registros pendentes", len(linhas) == 4, f"{len(linhas)}")
checa("cada linha é JSON válido", all(json.loads(l) for l in linhas))

print("== nada de segredo no que é reportado ==")
bruto = fila_local.read_text().lower()
vazou = [p for p in ("token", "secret", "senha", "password", "credential",
                     "api_key", "apikey", "authorization", "sk-")
         if p in bruto]
checa("nenhuma palavra de segredo no payload", not vazou, str(vazou))

print("== com hub de pé: envia e esvazia a fila ==")
import threading, http.server, socketserver

recebidos = []


class Alvo(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            recebidos.append(json.loads(self.rfile.read(n) or b"{}"))
        except Exception:
            recebidos.append({"_invalido": True})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, *a):
        pass


with socketserver.TCPServer(("127.0.0.1", 0), Alvo) as srv:
    porta = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{porta}/telemetria"

    r = reporte.enviar({"pessoa": "nicolas", "runtime": "codex", "duracao_s": 9},
                       url=url, fila=fila_local)
    checa("enviar() com hub de pé devolve sucesso", r is True or (isinstance(r, tuple) and r[0]))
    checa("o hub recebeu", len(recebidos) >= 1, f"{len(recebidos)}")

    n = reporte.drenar(url=url, fila=fila_local)
    time.sleep(0.2)
    restantes = [l for l in fila_local.read_text().splitlines() if l.strip()] if fila_local.exists() else []
    checa("drenar() reenviou os pendentes", n >= 4, f"drenou {n}")
    checa("fila local esvaziou", not restantes, f"{len(restantes)} sobraram")
    srv.shutdown()

print("== o runner continua funcionando com o hub morto ==")
import os
os.environ["ESTEIRA_HUB_URL"] = "http://127.0.0.1:9/nao-existe"
from esteira import runner
import config

with tempfile.TemporaryDirectory() as ws:
    try:
        res = runner.rodar("opencode", "Escreva OK em prova.txt e nada mais.",
                           cwd=ws, log_path=tmp / "r.log", timeout_s=180)
        checa("runner.rodar não levanta com hub morto", True)
        checa("runner.rodar devolve Resultado", hasattr(res, "codigo"))
    except Exception as e:
        checa("runner.rodar não levanta com hub morto", False, f"{type(e).__name__}: {e}")

print()
if falhas:
    print(f"FALHOU em {len(falhas)}: {', '.join(falhas)}")
    sys.exit(1)
print("D3: tudo passou")
