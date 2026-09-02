#!/usr/bin/env bash
# Prova do E1 — as tres telas do app.
# Escrita pelo maestro. O executor faz passar, nao redefine.
set -uo pipefail
cd "$(dirname "$0")/../.."
falhas=0
ck() { if [ "$2" = "0" ]; then echo "  ok   $1"; else echo "  FALHA $1 ${3:-}"; falhas=$((falhas+1)); fi; }

echo "== aderencia ao design system =="
bash scripts/check_ds.sh app/ >/dev/null 2>&1; ck "check_ds.sh em app/" "$?"

echo "== as tres telas respondem =="
.venv/bin/python - <<'PY'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.cwd()))
import importlib
falhou = 0
try:
    mod = importlib.import_module("app.app")
    app = getattr(mod, "app")
except Exception as e:
    print(f"  FALHA importar app.app — {e}"); sys.exit(1)
c = app.test_client()
for rota, nome in (("/", "tela 1 esteira"), ("/consumo", "tela 2 consumo"), ("/contas", "tela 3 contas")):
    try:
        r = c.get(rota)
        ok = r.status_code == 200
        print(f"  {'ok  ' if ok else 'FALHA'} {nome} ({rota}) http {r.status_code}")
        falhou += 0 if ok else 1
    except Exception as e:
        print(f"  FALHA {nome} — {e}"); falhou += 1

# hub fora do ar: 'sem dado', nunca zero
import re
r = c.get("/consumo")
h = r.get_data(as_text=True)
tem_sem_dado = bool(re.search(r'sem dado', h, re.I))
print(f"  {'ok  ' if tem_sem_dado else 'FALHA'} sem hub, a tela diz 'sem dado' (zero e uma afirmacao)")
falhou += 0 if tem_sem_dado else 1
sys.exit(1 if falhou else 0)
PY
ck "as tres telas e o 'sem dado'" "$?"

echo "== o app nao reimplementa runtime =="
if grep -rnE 'subprocess\.(run|Popen)|shlex\.split' app/ 2>/dev/null | grep -v 'esteira-maestro\|esteira ' ; then
  ck "app nao chama CLI de agente por conta propria" 1 "(ver linhas acima)"
else
  ck "app nao chama CLI de agente por conta propria" 0
fi

echo
[ "$falhas" -eq 0 ] && { echo "E1: tudo passou"; exit 0; } || { echo "FALHOU em $falhas"; exit 1; }
