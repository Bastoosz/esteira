# Plano — Esteira Desktop, bloco de 2026-09-03

## O que entendi

O escopo passou de "esteira que roda por CLI" para "esteira que quatro devs
**veem e operam**". O que muda é o **rosto**: um executável Windows por
pessoa, um hub na máquina dedicada, e telas que mostram esteira, consumo e
contas. O que **não** muda é o miolo — `runner.rodar` continua sendo o
runtime, git continua sendo a verdade da demanda, e nenhuma decisão migra
para dentro do app.

Abordagem em uma linha: **primeiro o dado existir no hub, depois a tela que
o mostra** — app que exibe dado inexistente é maquete, e maquete esconde
exatamente o tipo de falha que derrubou esta casa três vezes esta semana.

## O que a medição de hoje mudou no plano

Não planejei em cima de suposição. Rodei os CLIs antes de escrever briefing —
é a regra que foi mais violada ontem.

### `opencode stats` não tem `--json`. Não vamos parsear tabela.

    opencode stats --days 7
    ┌──────────────────────────┐
    │        OVERVIEW          │
    │ Sessions            24   │
    ...

Saída é tabela ASCII desenhada, e `--json` não existe (conferido em
`opencode --help` e `opencode stats --help`). Parser de tabela desenhada
quebra na primeira mudança de largura de coluna, em silêncio, e vira número
errado na tela — pior que número ausente.

**Decisão:** o consumo do `opencode` vem do que o **runner já mede**
(execuções, duração, código de saída, arquivos mudados, conta). A saída do
`opencode stats` entra como **texto bruto**, com data de captura, para quem
quiser olhar. Nunca parseada em número.

### `claude` e `codex` dão dado estruturado de verdade

`claude -p --output-format json` devolve, medido hoje:

    duration_ms, duration_api_ms, ttft_ms, session_id, num_turns,
    usage{input_tokens, output_tokens, cache_creation_input_tokens,
          cache_read_input_tokens}, total_cost_usd, is_error, modelUsage,
    stop_reason, permission_denials, subagent_stats

`codex exec --json` imprime eventos em JSONL (`--json  Print events to
stdout as JSONL`).

**Decisão:** o esquema do D1 guarda os campos **universais** como colunas
(duração, código, tokens de entrada/saída) e o resto num `bruto_json` por
execução. Campo de fornecedor vira coluna só quando dois runtimes o tiverem.

### `total_cost_usd` existe e é veneno se mal nomeado

O `claude` devolve `total_cost_usd = 0.1456365` numa chamada de assinatura.
Em assinatura isso **não é dinheiro gasto** — é preço de tabela do que teria
custado por API. Se aparecer na tela como "custo", alguém vai somar o mês e
levar um susto falso.

**Decisão:** a coluna se chama `custo_nocional_usd`, a tela mostra como
*proxy de volume*, e **não existe alerta de gasto**. O teto desta casa é
turno, tempo e rodada — `PADROES.md` e `BUILD.md`.

## Estado da bancada hoje

    agy       cota esgotada, resets in 132h37m  → 3 vagas úteis, não 4
    claude    conta de produção com OAuth expirado (bloqueio de ontem)
    codex     OK
    opencode  OK

O `agy` não resetou (era 137h ontem, é 132h hoje — bate). A bancada opera
com `codex` × 2 e `opencode` × 1.

## Premissas que assumi

1. **O hub mora no `board.py` + `esteira/hub/`**, não num serviço novo. O
   board já é o processo da máquina dedicada, já tem 8 rotas e já lê estado
   do disco. Servidor novo seria peça a mais para autenticar, supervisionar
   e reiniciar.
2. **SQLite, não Postgres.** O `BUILD.md` manda adotar Postgres quando uma
   pergunta analítica doer no `jq`. Ela não doeu.
3. **`app/` é pasta nova no mesmo repo**, não repositório separado. O app
   importa `esteira/` — separar agora criaria versionamento cruzado antes
   de existir usuário.
4. **Windows não está disponível para medição neste bloco.** Tudo que for
   específico de Windows (WebView2, SmartScreen, Credential Manager) entra
   como **roteiro a verificar**, marcado como não medido — igual ao T-04.
   Briefing que afirmar comportamento de Windows sem máquina é briefing
   errado.
5. A política de conta continua `fixa`/`nicolas`. Rodízio não entra.

## O que NÃO vou fazer neste bloco

- **Não vou empacotar o `.exe`.** Sem máquina Windows para rodar o binário,
  empacotar é produzir artefato que ninguém consegue provar. E1 entrega as
  telas rodando por HTTP; o empacotamento (E3) espera máquina.
- **Não vou centralizar credencial.** É o único ponto em que contrario o
  pedido, e está argumentado na §8 do prompt: já falhou aqui (a cópia de
  `nicolas:claude` venceu em silêncio), não transporta tecnicamente (o `agy`
  usa o Credential Manager do usuário) e é o ponto de contrato de assinatura.
  O hub guarda **identidade e saúde**, nunca segredo. Se a decisão for
  centralizar mesmo assim, é decisão de negócio: escalo antes de implementar.
- **Não vou parsear a tabela do `opencode stats`.** Ver acima.
- **Não vou mover decisão para o app.** Botão sem comando de CLI equivalente
  não entra. O app chama `esteira` e `esteira-maestro`.
- **Nada da lista proibida:** roteamento com aprendizado, DAG, *registry* em
  banco, *broker*, Temporal, Vault, RAG, teto em dólar, merge automático.
- **Não vou tocar em `demands/`, `esteira/worker.py` nem `esteira/vigia.py`**
  além da instrumentação de telemetria do D3, que é código existente ganhando
  medição — a exceção que o `BUILD.md` admite.
