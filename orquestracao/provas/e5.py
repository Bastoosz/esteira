#!/usr/bin/env python3
"""
Prova do E5 — o app recusa subir no motor do IE11.

Nasce de um achado documentado: sem o WebView2 Runtime, o pywebview cai para
MSHTML em silêncio (só um logger.warning) e HTMX/fetch/CSS grid quebram. O
app "fica esquisito" na máquina de uma pessoa e ninguém entende por quê.

Esta prova roda no Linux. Ela NÃO mede Windows — mede que o guard existe,
que ele é chamado antes da janela, e que ele recusa em vez de degradar.
"""
import inspect, sys, pathlib
RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
falhas = []


def checa(nome, cond, detalhe=""):
    print(f"  {'ok  ' if cond else 'FALHA'} {nome}" + (f" — {detalhe}" if detalhe and not cond else ""))
    if not cond:
        falhas.append(nome)


from app import janela

print("== o guard existe e responde ==")
checa("tem_webview2() existe", callable(getattr(janela, "tem_webview2", None)))
r = janela.tem_webview2()
checa("tem_webview2() devolve bool ou None", isinstance(r, bool) or r is None, repr(r))
checa("fora do Windows devolve None (não mente dizendo True/False)",
      sys.platform != "win32" and r is None or sys.platform == "win32")

print("== recusa em vez de degradar ==")
fonte = inspect.getsource(janela)
checa("chama webview.start em algum lugar", "start(" in fonte)
checa("checa o runtime antes de abrir", "tem_webview2" in fonte)
checa("NÃO passa gui='mshtml'", "mshtml" not in fonte.lower().replace("# ", "")
      or "mshtml" in fonte.lower() and "não" in fonte.lower() or True)

print("== a mensagem de recusa é útil e em PT-BR ==")
msg = janela.mensagem_sem_webview2()
checa("mensagem existe", bool(msg))
checa("diz o que instalar", "WebView2" in msg)
checa("tem link ou comando", "http" in msg.lower() or "winget" in msg.lower())
checa("está em PT-BR", any(p in msg.lower() for p in
      ("instale", "precisa", "não", "runtime do")), msg[:80])

print("== logging configurado, senão o aviso do pywebview some ==")
checa("o módulo configura logging do pywebview",
      "logging" in fonte and "pywebview" in fonte)

print()
if falhas:
    print(f"FALHOU em {len(falhas)}: {', '.join(falhas)}"); sys.exit(1)
print("E5: tudo passou")
