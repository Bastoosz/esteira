#!/usr/bin/env bash
# Gate do projeto. Um comando, saída 0 = verde.
# Projeto sem check.sh que funciona não entra na esteira.
set -euo pipefail

echo "[1/4] sintaxe"
python -m compileall -q . 2>&1 | grep -v '^$' && exit 1 || true

echo "[2/4] lint"
command -v ruff >/dev/null && ruff check . || echo "  (ruff não instalado, pulando)"

echo "[3/4] testes"
if [ -d tests ]; then pytest -q; else echo "  (sem tests/)"; fi

echo "[4/4] segredo no código"
if grep -rInE '(sk-[A-Za-z0-9]{20,}|api[_-]?key\s*=\s*["'"'"'][^"'"'"']{16,})' \
     --include='*.py' --include='*.js' --include='*.json' . \
     | grep -v -E '(\.env\.example|config\.py.*getenv)'; then
  echo "  ✗ possível segredo no código"; exit 1
fi

echo "check.sh: ok"
