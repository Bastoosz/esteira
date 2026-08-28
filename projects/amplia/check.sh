#!/usr/bin/env bash
# Gate local do AMPLIA. Um comando, saída 0 = verde.
set -euo pipefail

AMPLIA="${1:-/home/nicolas/orca/AMPLIA.APP_vers-o-2}"
BACKEND="$AMPLIA/backend"
FRONTEND="$AMPLIA/frontend"
TEMP_DIR=$(mktemp -d /tmp/amplia-check.XXXXXX)
trap 'rm -rf "$TEMP_DIR"' EXIT

if [ ! -f "$BACKEND/pyproject.toml" ] || [ ! -f "$FRONTEND/package.json" ]; then
  echo "✗ caminho inválido: não encontrei backend/pyproject.toml e frontend/package.json em $AMPLIA"
  exit 1
fi

echo "[1/4] sintaxe"
if command -v python3 >/dev/null 2>&1; then
  AMPLIA_BACKEND="$BACKEND" python3 - <<'PY'
import ast
import os
from pathlib import Path

raiz = Path(os.environ["AMPLIA_BACKEND"])
arquivos = [
    caminho
    for caminho in raiz.rglob("*.py")
    if not any(parte in {".git", ".venv"} for parte in caminho.parts)
]
for caminho in arquivos:
    ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
print(f"  backend: {len(arquivos)} arquivos Python válidos")
PY
else
  echo "  backend (pulando: python3 não instalado)"
fi
if command -v npm >/dev/null 2>&1 && [ -d "$FRONTEND/node_modules" ]; then
  (cd "$FRONTEND" && npm run typecheck)
else
  echo "  frontend (pulando: dependências ausentes; rode npm ci em frontend/)"
fi

echo "[2/4] lint"
if command -v uv >/dev/null 2>&1 && [ -d "$BACKEND/.venv" ]; then
  (cd "$BACKEND" && UV_CACHE_DIR="$TEMP_DIR/uv" RUFF_CACHE_DIR="$TEMP_DIR/ruff" \
    uv run --offline ruff check .)
else
  echo "  backend (pulando: uv ou backend/.venv ausente)"
fi
if command -v npm >/dev/null 2>&1 && [ -d "$FRONTEND/node_modules" ]; then
  (cd "$FRONTEND" && npm run lint)
else
  echo "  frontend (pulando: dependências ausentes; rode npm ci em frontend/)"
fi

echo "[3/4] testes"
if command -v uv >/dev/null 2>&1 && [ -d "$BACKEND/.venv" ]; then
  if (cd "$BACKEND" && UV_CACHE_DIR="$TEMP_DIR/uv" \
      TIKTOKEN_CACHE_DIR="$TEMP_DIR/tiktoken" uv run --offline python -c \
      'import tiktoken; tiktoken.get_encoding("cl100k_base")') >/dev/null 2>&1; then
    (cd "$BACKEND" && UV_CACHE_DIR="$TEMP_DIR/uv" \
      TIKTOKEN_CACHE_DIR="$TEMP_DIR/tiktoken" PYTHONDONTWRITEBYTECODE=1 \
      uv run --offline pytest tests/ -q -p no:cacheprovider)
  else
    echo "  backend (pulando: recurso tiktoken cl100k_base indisponível sem rede)"
  fi
else
  echo "  backend (pulando: uv ou backend/.venv ausente)"
fi
if command -v npm >/dev/null 2>&1 && [ -d "$FRONTEND/node_modules" ]; then
  (cd "$FRONTEND" && npm run test)
else
  echo "  frontend (pulando: dependências ausentes; rode npm ci em frontend/)"
fi
if command -v deno >/dev/null 2>&1; then
  (cd "$BACKEND" && deno test --allow-env supabase/functions/_shared/emailPolicy.test.ts)
else
  echo "  fallback Deno (pulando: deno não instalado)"
fi

echo "[4/4] segredo no código"
SEGREDOS="$TEMP_DIR/segredos.txt"
find "$BACKEND" "$FRONTEND" -type f \
  \( -name '*.py' -o -name '*.js' -o -name '*.jsx' -o -name '*.ts' \
     -o -name '*.tsx' -o -name '*.json' -o -name '*.tf' \) \
  -not -path '*/.git/*' -not -path '*/.venv/*' -not -path '*/node_modules/*' \
  -not -path '*/dist/*' -not -path '*/tests/*' -not -name '*.test.*' \
  -not -name '*.lock' -not -name '.env' -print0 \
  | xargs -0 grep -IlE \
    'sk-[A-Za-z0-9_-]{20,}|sk-or-v1-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}' \
    >"$SEGREDOS" 2>/dev/null || true
if [ -s "$SEGREDOS" ]; then
  echo "  ✗ possível segredo em:"
  sed 's/^/    /' "$SEGREDOS"
  exit 1
fi
echo "  nenhum padrão de credencial encontrado"

echo "check.sh: ok"
