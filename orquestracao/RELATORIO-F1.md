# Relatório F1 — login guiado

## O que foi feito

- Criado `esteira/login.py`, que lê as pessoas pelo registro central de
  `esteira.contas`, monta comandos interativos e reconhece mensagens de
  autenticação expirada.
- Criado `bin/esteira-login`, com listagem em JSON, exibição do comando e fluxo
  interativo seguido do `smoke_test` do runtime.
- `ativar()` recusa a ativação quando o smoke falha. Quando passa, devolve a
  marcação autorizada para que um humano a aplique em `contas.yaml`.

## O que não foi feito

- Nenhuma credencial foi aberta, lida, impressa, copiada ou movida.
- `contas.yaml` não foi alterado; o próprio arquivo determina que a escrita é
  humana.
- Não foram alterados `esteira/contas.py`, `esteira/runner.py`, o hub, arquivos
  `.env` nem as provas.

## Premissas

- `claude` e `codex` devem usar, respectivamente, `CLAUDE_CONFIG_DIR` e
  `CODEX_HOME`, obtidos dos mapeamentos e funções existentes em
  `esteira.contas`.
- O processo de login deve herdar entrada e saída do terminal. Por isso a CLI
  usa execução sem captura de stdin ou stdout.
- Uma conta somente fica elegível para a marcação humana depois que o comando
  interativo termina com sucesso e o smoke correspondente passa.

## O que quebrou

Nada conhecido durante a implementação.

## Descobertas sobre `agy` e `opencode`

O spike medido nesta máquina mostra que `opencode` usa os diretórios XDG da
máquina e que `agy` usa o diretório global `~/.gemini`. `esteira.contas` não
possui variável de diretório nem conta individual para esses runtimes. Portanto,
o comando de login de ambos é simples (`opencode` ou `agy`) e a autenticação é
tratada como pertencente à máquina, não a uma pessoa. Nenhuma variável de
ambiente foi inventada para simular um isolamento que o spike não confirmou.
