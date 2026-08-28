# Sub-task: fluxo n8n

Escopo: `entregavel/workflow.json`.

## Regra número um

**Copie e adapte um exemplo de `refs/n8n/`.** Não gere JSON de fluxo do
zero — schema de nó, conexões e posição erram com facilidade e o
resultado não abre no n8n.

## Regras

- Nome do fluxo: `[esteira #<id>] <descrição curta>`
- Sempre criado **inativo**
- Credencial referenciada por nome, nunca embutida
- Integra com Outlook, Teams ou 365 → a credencial declarada é
  `dashboards`. É ela que a equipe usa para testar.
- Primeira execução segura: nó de limite (máx 5 itens) e destinatário de
  teste configurável no topo do fluxo
- Sem loop sem condição de parada. Sem exceção.

## Saída

`entregavel/workflow.json` + seção em `plano.md` com: o que o fluxo faz,
qual gatilho, o que configurar antes de ativar, o que testar primeiro.
