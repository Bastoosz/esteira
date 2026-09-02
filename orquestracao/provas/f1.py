#!/usr/bin/env python3
"""
Prova do F1 — login guiado.

A regra da casa que esta prova defende: `ativo: true` só depois do
smoke passar. Conta marcada ativa sem autenticação faz a demanda morrer
no meio, não na largada — e foi exatamente o que aconteceu aqui.

E a regra nova: o app NUNCA copia credencial de um lugar para outro.
"""
import inspect, sys, pathlib
RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
falhas = []


def checa(nome, cond, detalhe=""):
    print(f"  {'ok  ' if cond else 'FALHA'} {nome}" + (f" — {detalhe}" if detalhe and not cond else ""))
    if not cond:
        falhas.append(nome)


from esteira import login

print("== a lista de pessoas sai do contas.yaml, não é digitada ==")
pessoas = login.pessoas()
checa("pessoas() devolve lista não vazia", bool(pessoas), str(pessoas)[:80])
checa("nicolas está na lista", any(p.get("id") == "nicolas" for p in pessoas))

print("== o comando de login é montado, não adivinhado ==")
for runtime, var in (("claude", "CLAUDE_CONFIG_DIR"), ("codex", "CODEX_HOME")):
    c = login.comando("nicolas", runtime)
    checa(f"comando({runtime}) cita {var}", var in " ".join(c) or var in str(c), str(c)[:90])
    checa(f"comando({runtime}) aponta para ~/.esteira-auth", ".esteira-auth" in str(c), str(c)[:90])

print("== NUNCA copia credencial ==")
fonte = ""
for mod in (login,):
    try:
        fonte += inspect.getsource(mod)
    except Exception:
        pass
proibido = [t for t in ("shutil.copy", "shutil.copyfile", "shutil.copy2",
                        ".credentials.json", "auth.json")
            if t in fonte]
checa("o módulo não copia arquivo de credencial", not proibido, str(proibido))

print("== ativo: true só depois do smoke ==")
sig = inspect.signature(login.ativar)
checa("ativar() existe", callable(login.ativar))
try:
    login.ativar("nicolas", "claude", smoke_passou=False)
    checa("ativar() recusa sem smoke", False, "não levantou")
except Exception:
    checa("ativar() recusa sem smoke", True)

print("== detecta OAuth expirado e propõe relogin ==")
amostra = ("Failed to authenticate: OAuth session expired and could not be refreshed")
checa("precisa_relogin() reconhece a mensagem real", login.precisa_relogin(amostra) is True)
checa("precisa_relogin() não dá falso positivo", login.precisa_relogin("tudo certo, OK") is False)

print()
if falhas:
    print(f"FALHOU em {len(falhas)}: {', '.join(falhas)}"); sys.exit(1)
print("F1: tudo passou")
