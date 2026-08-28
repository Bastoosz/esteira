# Sub-task: revisão cruzada

Você **não** escreveu esse código. Não elogie, não resuma, não sugira
estilo. Responda só o checklist, em JSON.

    [{"item": "escopo", "ok": true, "nota": ""}, ...]

| item | pergunta |
|---|---|
| `escopo` | o diff toca arquivo fora do escopo declarado? |
| `aceite` | o que a demanda pediu está de fato implementado? |
| `prova` | existe artefato real em `outbox/`? é o que o pedido descreve? |
| `segredo` | tem chave, token ou senha no diff? |
| `dependencia` | adicionou dependência nova? qual, e era necessária? |
| `juridico` | tem regra de prazo/valor implementada em vez de marcada? |
| `ds` | hex cru, px cru, ou fonte fora de Montserrat/Sansation? |
| `estrangeirismo` | palavra em inglês sem itálico na UI? |
| `erro` | removeu ou engoliu tratamento de erro? |
| `template` | a estrutura de pastas é a do template? |

`ok: false` exige `nota` com arquivo e linha. Não invente problema.
