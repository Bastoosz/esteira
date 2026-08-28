#!/usr/bin/env bash
# Aderência ao design system Andrade Maia.
#
# O _adherence.oxlintrc.json do DS mira JSX. Aqui cobrimos Jinja/HTML/CSS com
# as três regras que pegam a maior parte dos desvios, mais a regra de itálico.
#
# Escape para caso legítimo: termine a linha com  /* ds-ok */  ou  <!-- ds-ok -->
set -uo pipefail
ALVO="${1:-.}"
REL=$(mktemp)

alvos() {
  grep -rIl --include='*.html' --include='*.jinja' --include='*.css' \
       --include='*.jsx' --include='*.tsx' '' "$ALVO" 2>/dev/null \
  | grep -v -E '(static/ds/|node_modules|/tokens/|\.venv|/refs/|tokens\.css)'
}

# $1 = rótulo, $2 = arquivo, $3 = saída do grep
registrar() { while IFS= read -r l; do [ -n "$l" ] && echo "$2|$l|$1" >> "$REL"; done <<< "$3"; }

sem_escape() { grep -v -E '(ds-ok)'; }

while IFS= read -r f; do
  [ -z "$f" ] && continue

  registrar "hex cru" "$f" "$(grep -nE '#[0-9a-fA-F]{3,8}\b' "$f" \
    | grep -v -E '(var\(|--am-|@font-face)' | sem_escape)"

  registrar "px cru" "$f" "$(grep -nE '(padding|margin|gap|font-size|width|height|top|left|right|bottom)[^;:]*:[^;]*[0-9]+px' "$f" \
    | grep -v -E '(var\(|--|@media|100%|1px)' | sem_escape)"

  registrar "fonte fora do DS" "$f" "$(grep -niE 'font-family[[:space:]]*:' "$f" \
    | grep -viE '(Montserrat|Sansation|var\(--font)' | sem_escape)"

  # A palavra estrangeira só é desvio quando NÃO está marcada. Por isso
  # apagamos primeiro os trechos já marcados (<i>, <em>, class="foreign") e
  # só então procuramos. A versão anterior fazia o contrário — procurava e
  # depois tentava excluir linhas com '<i' — e não funcionava: o casamento
  # é >...< , então o fragmento achado é ">upload<", que nunca contém a tag
  # que o envolve. Resultado: <p><i>upload</i></p> era reprovado, e o gate
  # ficava impossível de passar em qualquer página que citasse a palavra.
  #
  # O sed apaga o CONTEÚDO da linha mas nunca a linha, para o número de
  # linha do grep continuar valendo. Por isso 'ds-ok' vira linha em branco
  # aqui em vez de ser filtrado depois: esta regra usa grep -o, então o
  # sem_escape nunca via o comentário de escape.
  registrar "estrangeirismo sem itálico" "$f" "$(
    sed -E 's/.*ds-ok.*//
            s#<(i|em)\b[^>]*>[^<]*</(i|em)>##g
            s#<([a-z]+)\b[^>]*class="[^"]*\bforeign\b[^"]*"[^>]*>[^<]*</\1>##g' \
        "$f" 2>/dev/null \
    | grep -nioE ">[^<]*\b(upload|download|dashboard|login|logout|preview|deploy|status|feedback|report|export|import|link)\b[^<]*<")"

done < <(alvos)

N=$(wc -l < "$REL" | tr -d ' ')
if [ "$N" -gt 0 ]; then
  echo "[ds] $N desvio(s):"
  sort "$REL" | awk -F'|' '{printf "  ✗ [%s] %s:%s\n", $3, $1, $2}' | head -40
  echo ""
  echo "Use os tokens: var(--am-*), var(--font-*), var(--space-*)."
  echo "Caso legítimo: termine a linha com /* ds-ok */"
  rm -f "$REL"; exit 1
fi
rm -f "$REL"
echo "[ds] ok"
