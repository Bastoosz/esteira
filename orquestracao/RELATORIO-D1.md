# Relatório D1 — Hub SQLite e telemetria

## O que foi feito

- Criei `esteira/hub/` com acesso SQLite, migração idempotente e camada de validação HTTP.
- Criei as tabelas `execucoes`, `contas` e `eventos`, com índices para as consultas por pessoa/período e para eventos por data.
- Configurei `PRAGMA journal_mode=WAL` e `PRAGMA busy_timeout=5000` em toda conexão.
- Acrescentei ao `board.py`, sem alterar as rotas anteriores:
  - `POST /telemetria`;
  - `POST /contas/estado`;
  - `GET /api/consumo`, com filtros opcionais `pessoa`, `inicio` e `fim` (datas ISO 8601).
- Payloads HTTP ausentes, não-JSON, sem os campos obrigatórios ou com tipos inválidos retornam HTTP 400.
- O estado de conta usa *upsert* pela chave `(pessoa, runtime)` e também registra a mudança em `eventos`.
- Campos evidentes de credencial recebidos dentro do payload bruto são substituídos por `[REMOVIDO]` antes da persistência. Métricas de quantidade, como `input_tokens`, permanecem no JSON bruto.

## Premissas

- A variável esperada no `.env` é `ESTEIRA_HUB_DB`, contendo o caminho do arquivo SQLite. Não alterei o `.env` nem `config.py`.
- Sem essa variável, o padrão é `data/hub.db`, pasta que já está ignorada pelo Git.
- O período de consumo é inclusivo e informado pelos parâmetros `inicio` e `fim`, ambos em ISO 8601.
- `custo_nocional_usd` é apenas uma medida de volume por execução; não foi agregado nem tratado como despesa.

## O que não foi feito

- Não alterei `config.py`, `.env`, credenciais, `runner.py`, `worker.py`, `vigia.py`, `contas.py`, `maestro.py`, `demands/**`, `templates/**` ou a prova.
- Não criei servidor nem porta adicional; os endpoints usam o Flask que já existe no board.
- Não criei parser para a saída tabular do OpenCode.
- Não criei alerta, teto ou soma mensal de custo nocional.

## O que quebrou

Nada detectado. A prova oficial passou e a checagem adicional confirmou `journal_mode=wal`, `busy_timeout=5000` e o *upsert* de contas.

## Inconsistência encontrada na prova/briefing

O esquema descrito no briefing exige as colunas `tokens_entrada` e `tokens_saida`, mas a prova rejeita qualquer coluna cujo nome contenha `token`. Os dois requisitos não podem ser satisfeitos ao mesmo tempo.

Para cumprir a regra dura de não criar coluna com nome de segredo e obter a saída 0 exigida, essas duas colunas não foram criadas. As métricas continuam preservadas em `bruto_json`. Não alterei nem contornei `db.colunas()` para esconder o esquema real.

## Prova oficial

Comando executado:

```console
.venv/bin/python orquestracao/provas/d1.py ; echo "saida=$?"
```

Saída completa:

```text
== esquema ==
  ok   as tres tabelas existem
  ok   migrar e idempotente
  ok   execucao persistiu depois de fechar e reabrir
== nada de segredo no esquema ==
  ok   nenhuma coluna com cara de segredo
== endpoints ==
  ok   POST /telemetria aceita
  ok   POST /contas/estado aceita
  ok   GET /api/consumo responde 200
  ok   GET /api/consumo devolve JSON
== payload invalido nao derruba ==
  ok   payload invalido devolve 4xx, nao 500
== rotas antigas continuam de pe ==
  ok   regressao /
  ok   regressao /numeros
  ok   regressao /orquestracao

D1: tudo passou
saida=0
```
