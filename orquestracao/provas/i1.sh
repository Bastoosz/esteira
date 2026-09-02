#!/usr/bin/env bash
# Prova do I1 — refs/ferramentas.md.
set -uo pipefail
cd "$(dirname "$0")/../.."
F=refs/ferramentas.md
falhas=0
ck() { if [ "$2" = "0" ]; then echo "  ok   $1"; else echo "  FALHA $1 ${3:-}"; falhas=$((falhas+1)); fi; }

[ -f "$F" ]; ck "arquivo existe" "$?"
[ -f "$F" ] || { echo "FALHOU"; exit 1; }

# as quatro perguntas que o prompt exige por ferramenta
for termo in "dono" "chave" "cai" "serve"; do
  grep -qi "$termo" "$F"; ck "responde '$termo'" "$?"
done

# tem que citar o que existe de fato no repo
for t in OPENROUTER Escavador n8n; do
  grep -qi "$t" "$F"; ck "cita $t" "$?"
done

# inferencia marcada como inferencia
grep -qiE 'inferência|inferencia|não confirmado|nao confirmado|a confirmar' "$F"
ck "marca o que e inferencia" "$?"

# nunca um segredo de verdade
if grep -qEi '(sk-[A-Za-z0-9]{20,}|["'"'"'][A-Za-z0-9_-]{32,}["'"'"'])' "$F"; then
  ck "nenhum segredo no arquivo" 1
else
  ck "nenhum segredo no arquivo" 0
fi

bash scripts/check_ds.sh refs/ >/dev/null 2>&1; ck "check_ds.sh em refs/" "$?"

echo
[ "$falhas" -eq 0 ] && { echo "I1: tudo passou"; exit 0; } || { echo "FALHOU em $falhas"; exit 1; }
