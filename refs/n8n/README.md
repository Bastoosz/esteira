# Fluxos n8n de referência

Estes arquivos registram o *schema* real dos fluxos F1 e F2 para que o
próximo agente copie formatos já aceitos pelo n8n, em vez de adivinhar
`typeVersion`, parâmetros, posições e `connections`.

- n8n: `2.36.8`
- origem: exportações `n8n/esteira-comms-out.json` e
  `n8n/esteira-comms-in.json`
- *commit* da fonte: `4db024df7db30aa9e39c5694312372c260ec7465`
- data da referência: `2026-09-02`

Os arquivos são modelos importáveis, não cópias prontas para ativação. Antes
de usar, configure destinatários, tabela, pasta, time, canal, credenciais e o
endereço do trabalhador conforme o ambiente de destino.

## F1 — `esteira-comms-out.json`

Fluxo de saída: recebe uma comunicação, roteia o tipo, monta o e-mail, registra
a correlação, trata anexos e publica um cartão quando necessário.

| Nó | O que ensina |
|---|---|
| `Receber comunicação da esteira` | Forma de um nó `webhook` com método, caminho e resposta imediata. O `webhookId` da instância foi removido; o caminho funcional permaneceu. |
| `Validar envelope e destinatário` | Como um nó `code` lê `$json`, valida campos e devolve itens no formato `{ json: ... }`. |
| `Rotear por type` | Como um nó `switch` em modo de expressão escolhe uma saída pelo campo `rota`; `numberOutputs: 7` declara as sete saídas. |
| `Montar e-mail em HTML` | Como um nó `code` transforma dados, usa expressões do n8n e preserva o item para os nós seguintes. |
| `Criar rascunho no Outlook` | Forma do `microsoftOutlook`: autenticação, recurso, operação, campos adicionais e referência de credencial somente por nome. |
| `Registrar correlação` | Forma do `dataTable`, incluindo seletor por nome, mapeamento de colunas e descrição do *schema*. O valor `comms` é um marcador local. |
| `Tem anexos de preview?` | Como um nó `if` declara condição booleana estrita e oferece saída verdadeira e falsa. |
| `Separar caminhos dos anexos` | Como `$input` implícito chega ao `code` por `$json` e como um item de entrada pode virar vários itens de saída. |
| `Ler anexos do disco` | Forma do `readWriteFile` para produzir dado binário a partir de um caminho calculado. |
| `Adicionar anexo ao rascunho` | Como o Outlook recebe binário e referencia o resultado de outro nó com `$('Criar rascunho no Outlook').first()`. |
| `Aguardar todos os anexos` | Como o `aggregate` reúne vários itens antes de continuar. |
| `Enviar e-mail com anexos` e `Enviar e-mail sem anexos` | Como dois ramos usam o mesmo rascunho e convergem no aviso posterior. |
| `Precisa avisar no Teams?` | Outra referência de bifurcação booleana, inclusive com a segunda saída deliberadamente vazia. |
| `Publicar card no Teams` | Forma do `microsoftTeams`, com time e canal como marcadores e credencial referenciada por nome. |
| `Ignorar progress` | Como encerrar um ramo válido com um retorno explícito. |
| `Recusar envio proibido` | Forma do `stopAndError` com mensagem calculada. |

Em `connections`, cada chave é o nome do nó de origem. Dentro de `main`, a
posição do vetor é a saída numerada do nó: no `Rotear por type`, por exemplo,
os vetores de índice 0 a 6 correspondem às sete rotas. O `index` do objeto de
destino indica a entrada numerada no nó seguinte. Essa estrutura também mostra
como dois ramos podem apontar para o mesmo destino.

## F2 — `esteira-comms-in.json`

Fluxo de entrada: consulta mensagens do Outlook, recupera cabeçalhos, procura a
correlação e envia a resposta ao trabalhador ou separa a mensagem não
identificada.

| Nó | O que ensina |
|---|---|
| `Outlook: nova mensagem` | Forma do `microsoftOutlookTrigger`, incluindo frequência, evento, campos retornados e filtro. |
| `Buscar cabeçalhos completos no Graph` | Como um `httpRequest` usa uma credencial predefinida e monta a URL com uma expressão. |
| `Carregar correlações` | Como ler todas as linhas de uma `dataTable`, ordenar e passar os itens adiante. |
| `Casar mensagem e cortar corpo` | Como um `code` recebe todos os itens com `$input.all()`, consulta a saída de outro nó por nome e devolve um único resultado normalizado. |
| `Mensagem identificada?` | Como a saída 0 representa verdadeiro e a saída 1 representa falso nas `connections`. |
| `POST no reply_to do worker` | Forma de um `httpRequest` com corpo JSON calculado e tipo de conteúdo explícito. |
| `Mover para Esteira nao-identificado` | Como o Outlook move uma mensagem usando seletores de identificador. `PASTA` é um marcador. |
| `Avisar não identificado no Teams` | Como publicar HTML no Teams após o ramo falso. `TIME` e `CANAL` são marcadores. |

## Sanitização

Foram removidos o identificador original do fluxo, `versionId`, `meta`,
`webhookId` e os identificadores internos das credenciais. O n8n 2.36.8 exige
um `id` superior na importação; por isso cada arquivo recebeu um identificador
sintético iniciado por `ref-`, que não pertence à instância de origem. Os
identificadores dos nós foram mantidos porque pertencem à estrutura portátil
do fluxo e ajudam o n8n a representar o grafo; não identificam a instância. Os
nomes `Outlook — Esteira` e `Teams — Esteira` também ficaram: são referências
por nome, não credenciais nem segredos, e ensinam o formato correto.

Valores específicos do ambiente foram trocados pelos marcadores `comms`,
`PASTA`, `TIME` e `CANAL`. As expressões iniciadas por `={{ ... }}` apenas leem
dados da execução ou resultados de outros nós. Elas não contêm valor de
credencial, *token*, senha, segredo de cliente, chave de API nem *token* de
acesso.
