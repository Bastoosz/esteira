# Como importar os fluxos do Dia 2

## Importação

Pela interface do n8n, use **Workflows → Import from File** e importe, nesta ordem:

1. `esteira-comms-out.json`
2. `esteira-comms-in.json`

Os workflows chegam inativos. Configure os itens abaixo, salve e só então ative F1 e F2.

## Configuração manual obrigatória

1. Crie uma credencial OAuth2 do Outlook chamada `Outlook — Esteira` e selecione-a em todos os nós Outlook e no HTTP Request `Buscar cabeçalhos completos no Graph`. Ela precisa ler, criar/enviar e mover mensagens.
2. Crie uma credencial OAuth2 do Teams chamada `Teams — Esteira` e selecione-a nos dois nós Teams. Use OAuth delegado: postagem em canal não funciona com Service Principal no nó desta versão.
3. Em F1, substitua `equipe@CONFIGURAR.invalid` nos dois nós de envio e em `Criar rascunho no Outlook` pelo e-mail interno da equipe.
4. Nos dois fluxos, selecione o Team e o canal nos nós Teams, substituindo `CONFIGURAR_TEAM_ID` e `CONFIGURAR_CHANNEL_ID`.
5. No Outlook, crie a pasta `Esteira/nao-identificado`. Em F2, selecione essa pasta em `Mover para Esteira nao-identificado`, substituindo `CONFIGURAR_ID_PASTA_NAO_IDENTIFICADO`.
6. Crie uma Data Table chamada `esteira_comms` com estas colunas:

   - `logical_message_id` (String)
   - `internet_message_id` (String)
   - `conversation_id` (String)
   - `demand_id` (String)
   - `rodada` (Number)
   - `reply_to` (String)
   - `assunto` (String)
   - `criado_em` (String)

   Depois, abra `Registrar correlação` em F1 e `Carregar correlações` em F2 e confirme que ambos apontam para essa tabela. A tabela é o estado de correlação entre os fluxos; o estado da pergunta continua no worker.

## Comportamento e placeholders

- F1 recebe `POST /webhook/esteira-comm`. O webhook de teste do editor tem URL diferente; para o caminho contratado, ative o workflow e use a URL de produção.
- Os valores `CONFIGURAR_*` e o endereço `.invalid` são placeholders deliberados. Nenhum segredo ou token está nos JSONs.
- Os cards são mensagens HTML de canal com aparência de aviso. O tipo `blocked` recebe marcação vermelha por emoji/texto.
- Em `preview`, `anexos[].caminho` deve ser um caminho local legível pelo processo do n8n no mesmo host. Vários anexos são aceitos e anexados ao mesmo rascunho.
- Download pelo raw do GitHub ficou como placeholder funcional não implementado nesta V1: caminhos `http://` ou `https://` param com erro explícito antes do envio. Use o caminho local produzido pelo worker.
- O F2 busca os cabeçalhos completos diretamente no Microsoft Graph porque o Outlook Trigger 1 não oferece `internetMessageHeaders` na lista de campos selecionáveis.
- O casamento é feito estritamente nesta ordem: `In-Reply-To`/`References`, `conversationId`, regex do assunto. Se nada casar, não há POST ao worker.

## Teste mínimo apó configurar

Envie um envelope `question` de uma demanda de teste para F1. Responda acima da linha de corte e confira:

1. assunto no formato `[esteira #<id>-<rodada>] <título>`;
2. corpo com opções, default e linha de corte;
3. uma linha criada em `esteira_comms`;
4. F2 chamando o `reply_to` com `resposta` e `autor`;
5. uma mensagem sem correlação sendo movida, sem POST, e avisada no Teams.
