# Armadilhas

> Cresce sozinho: toda nota que alguém "fixar" no board cai aqui.
> É o conhecimento tribal que o agente não tem como adivinhar.
> Teto: 150 linhas.

- A aplicação ativa está em `frontend/src/amplia/`. A pasta
  `frontend/src/components/` contém componentes shadcn legados; desenvolver ali
  pode produzir uma interface que não aparece no produto vivo.
- O repositório contém documentação de épocas diferentes. A *wiki* ainda cita
  5 *workers*, 17 ferramentas e integrações removidas, enquanto o `README.md`
  atual descreve 8 *workers*, 18 ferramentas e JUIT em uso. Confira código,
  dependências e `README.md` antes de repetir números.
- As Edge Functions Supabase não são o backend principal. São contingência do
  chat; uma correção aplicada apenas nelas não corrige o caminho normal na AWS.
- O tráfego público entra pelo Cloudflare Tunnel. Métricas de requisição do ALB
  podem ficar zeradas e não são fonte confiável de tráfego ou escala da API.
- O Postgres usa PgBouncer em modo transacional. Reativar cache de *prepared
  statements* pode causar `prepared statement does not exist` e deixar documento
  preso em “indexando”.
- Documento com estado genérico “pronto” não garante texto, busca ou evidência.
  Consulte as capacidades do contrato antes de habilitar uma ação na interface.
- Resultado jurídico vazio e falha do provedor são estados diferentes. Os ADRs de
  2026-08-12 sobre resultados tipados e confiabilidade do acervo ainda estão
  marcados como `PROPOSED — PENDING LEADERSHIP APPROVAL`; não os trate como
  arquitetura já aprovada.
- Os testes Python carregam `tiktoken.get_encoding("cl100k_base")` na coleta. Em
  ambiente sem cache e sem rede, a suíte falha antes de executar testes porque
  tenta baixar o vocabulário da OpenAI.
- `REGRA-JURIDICA`: o modo de contestação identifica “prazos críticos”, mas não
  foi encontrada regra humana validada para contagem de prazo, suspensão de
  expediente, prazo em dobro ou calendário de tribunal. Não implemente nem infira.
- `REGRA-JURIDICA`: Análise de Impugnação, Comparador de Provas e revisão de
  dialeticidade classificam enfrentamento ou suficiência. Preserve evidência,
  incerteza e correção manual; qualquer mudança de critério exige humano jurídico.
