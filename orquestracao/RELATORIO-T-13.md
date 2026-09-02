# RELATORIO — T-13: rota /orquestracao no board

## O que foi feito

Adicionei a rota `GET /orquestracao` em `board.py` (linha 126) que:

1. Lê `orquestracao/estado.json` e passa como variável `estado` ao template.
2. Lê `orquestracao/fila.jsonl` (jsonl, linha a linha), monta lista `fila`, e passa ao template.
3. Se os arquivos não existem, devolve dict vazio e lista vazia — o template trata com `{% else %}` no `for`, resultando em "fila vazia".
4. Resposta 200 com `templates/orquestracao.html` renderizado.

Também adicionei `json` no import do topo do arquivo (linha 9).

## O que NÃO foi feito

- Nenhum template foi criado ou editado (o T-11 já provou o `orquestracao.html`).
- Nenhuma rota existente foi alterada — `/`, `/_live`, `/d/<id_>`, `/numeros`, `/answer/...`, `/acao/...`, `/fixar/...` continuam idênticas.
- Nenhum arquivo fora de `board.py` foi modificado.
- Nenhum botão de despacho/colheita/mudança de estado foi adicionado (board só lê e mostra).

## Premissas assumidas

- `config.BASE_DIR` aponta para a raiz do repo (definido em `config.py` como `Path(__file__).resolve().parent`). Correto — verificado.
- O template espera `estado` como dict e `fila` como lista de dicts. Confirmado no `orquestracao.html` (linhas 6 e 36).

## Regressão

- `GET /` → 200 ✓
- `GET /numeros` → 200 ✓

## Prova

```
GET /orquestracao -> 200 10737 bytes
as 4 vagas: True
itens da fila: 20
regressao / -> 200
regressao /numeros -> 200
```

## Nota

A página `/orquestracao` existe e funciona, mas não está linkada no menu de navegação do `base.html`. Isso é escopo de outro item — o menu precisa ser editado separadamente.
