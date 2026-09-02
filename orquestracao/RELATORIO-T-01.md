# Relatório T-01

## O que fiz

- Criei `demands/1002/` chamando `Demanda.criar(...)`, com projeto
  `_exemplo`, dono `nicolas` e pedido pequeno de conversão CSV para XLSX.
- Registrei plano, premissas e uma pergunta obrigatória não jurídica para
  exercitar pausa e retomada.
- Executei diretamente o pre-flight e transicionei a demanda até `PRONTA`,
  sem chamar `worker.ciclo()` nem iniciar uma rodada.
- Escrevi `orquestracao/roteiros/ciclo-dia3.md` com a prova ordenada do ciclo.

## O que NÃO fiz

- Não executei o worker, o Claude, a rodada 1, commit nem push.
- Não alterei a demanda 1001, código da esteira, configuração, credenciais
  ou contas.
- Não implementei o conversor; isso pertence à prova futura do worker.

## Premissas

- `manter todos` é o padrão mais seguro porque não descarta registros.
- O board estará acessível em `127.0.0.1:5000` na prova, salvo alteração
  explícita de `BOARD_PORT`.
- A prova integral será rodada sem executores concorrentes escrevendo na raiz.

## O que quebrou pelo caminho

- O pre-flight não encontrou `OPENROUTER_API_KEY`. O fallback previsto em
  `preflight.rodar` gravou `modelo: nenhum` e marcou as seis respostas como
  `talvez`; a demanda seguiu corretamente para `PRONTA`.
- A primeira auditoria tentou usar `jq`, que não está instalado nesta
  máquina. Removi essa dependência do roteiro e usei o Python da `.venv`.

## Defeitos ou riscos de código observados e não corrigidos

- `worker.commit()` usa `git add -A` na raiz. Uma rodada concorrente pode
  incluir alterações de outros executores no commit; o roteiro exige execução
  isolada. Nenhum código foi alterado nesta tarefa.

## Prova exigida

Comando executado na raiz do repositório, exatamente como pedido:

```text
estado= PRONTA
abertas= []
proxima_da_fila= 1002
```
