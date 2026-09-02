#!/usr/bin/env bash
# Prova do G1 — F1 do n8n enviando por amknowledge@andrademaia.com.
set -uo pipefail
cd "$(dirname "$0")/../.."
export PATH="$HOME/.nvm/versions/node/v24.18.0/bin:$PATH"
F=n8n/esteira-comms-out.json
falhas=0
ck() { if [ "$2" = "0" ]; then echo "  ok   $1"; else echo "  FALHA $1 ${3:-}"; falhas=$((falhas+1)); fi; }

grep -q 'amknowledge@andrademaia.com' "$F"; ck "o fluxo cita a caixa amknowledge" "$?"
grep -q 'CONFIGURAR.invalid' "$F" && ck "nao sobrou placeholder CONFIGURAR.invalid" 1 || ck "nao sobrou placeholder CONFIGURAR.invalid" 0
grep -q 'amknowledge' n8n/COMO-IMPORTAR.md; ck "COMO-IMPORTAR documenta a caixa" "$?"

# a linha de corte e a regra dura de destinatario continuam de pe
grep -q 'responda acima desta linha' "$F"; ck "linha de corte preservada" "$?"
grep -q "to !== 'team" "$F"; ck "regra dura to==team preservada" "$?"

# credencial nunca no JSON
if grep -qiE '"(value|token|password|clientSecret|apiKey|accessToken)"[[:space:]]*:[[:space:]]*"[^"={]{8,}"' "$F"; then
  ck "nenhum segredo no JSON" 1
else
  ck "nenhum segredo no JSON" 0
fi

# e continua importando de verdade
timeout 240 n8n import:workflow --input="$F" >/dev/null 2>&1; ck "n8n import:workflow sai 0" "$?"

echo
[ "$falhas" -eq 0 ] && { echo "G1: tudo passou"; exit 0; } || { echo "FALHOU em $falhas"; exit 1; }
