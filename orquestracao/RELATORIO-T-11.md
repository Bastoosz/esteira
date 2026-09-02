# RELATORIO-T-11

## O que fez
- Criado `templates/orquestracao.html` estendendo `base.html`.
- Mostra as 4 vagas (número, tier, task em voo, conta, escopo, desde quando). Vaga sem task aparece como "livre".
- Mostra a fila completa em tabela (id, estado, tier, título, pré-requisito).
- Destaca linha com estado `escalada` via classe `travado`.
- `check_ds.sh` sai 0. Template renderiza sem erro (10065 bytes).

## O que NÃO fez
- Não alterou nenhum arquivo fora de `templates/`.
- Não escreveu JavaScript; live update fica a cargo do HTMX do `base.html` (a rota em `board.py` que sirva a rota com HTMX pode adicionar `hx-get` depois).
- Não leu arquivos dentro do template — `estado` e `fila` são passados como variáveis.

## O que assumiu
- `estado` é um dict com chave `vagas` (lista de dicts com campos `vaga`, `tier`, `task_id`, `pid`, `iniciado_em`, `escopo`, `conta`).
- `fila` é uma lista de dicts com campos `id`, `titulo`, `tier`, `estado`, `prereq` (lista, pode ser vazia).
- `board.py` vai servir a rota e injetar `agora` no contexto (padrão do `base.html`).

## O que quebrou
- Nada. Ambas as provas saíram 0.
