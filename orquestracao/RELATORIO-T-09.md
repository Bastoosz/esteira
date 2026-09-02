# Relatório T-09 — referências n8n

## O que foi feito

- Criados `refs/n8n/esteira-comms-out.json` (F1) e
  `refs/n8n/esteira-comms-in.json` (F2) a partir das fontes indicadas.
- Substituídos os identificadores de fluxo por identificadores sintéticos
  iniciados por `ref-`; removidos versão interna, metadados da instância,
  `webhookId` e identificadores internos de credenciais.
- Mantidos nomes de credenciais e identificadores estruturais dos nós.
- Substituídos valores dependentes do ambiente por marcadores.
- Documentado, em português, o que cada nó relevante ensina sobre o *schema*,
  inclusive saídas numeradas em `connections`.
- Anotados n8n `2.36.8`, origem, data e *commit* da fonte.

## O que não foi feito

- Nenhum arquivo de produção em `n8n/` foi alterado.
- Nenhum fluxo foi ativado ou executado.
- Nenhuma credencial, conta, `.env` ou banco da instância em `~/.n8n` foi
  lido ou alterado.
- F3 e F4 não foram incluídos, pois não fazem parte do escopo T-09.

## Premissas

- Os dois JSONs apontados na demanda são as exportações canônicas da instância.
- Identificadores dos nós descrevem o grafo portátil. O identificador superior
  é obrigatório para importação no n8n 2.36.8, então foi substituído por um
  valor sintético; `versionId`, `webhookId`, metadados e identificadores
  internos de credenciais foram removidos.
- Referências de credencial por nome devem permanecer, conforme a demanda.

## O que quebrou ou estava indisponível

- Em `2026-09-02`, o binário informou a versão `2.36.8`, mas
  `http://localhost:5678` recusou conexão (`HTTP 000`). Por isso não foi
  possível comparar as fontes com a interface da instância em execução.
- A prova de importação foi isolada em diretório descartável para cumprir a
  proibição de tocar o banco do n8n em `~/.n8n`.
- A primeira prova sem `id` superior falhou com `SQLITE_CONSTRAINT: NOT NULL
  constraint failed: workflow_entity.id`. A referência foi corrigida com
  identificadores sintéticos e a prova foi repetida.
