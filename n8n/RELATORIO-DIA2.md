# Relatório — Dia 2 (F1 e F2)

## Nós usados e motivo

### F1 — `esteira-comms-out`

- **Webhook**: recebe o envelope `v=1` em `POST /webhook/esteira-comm`.
- **Code — validar**: valida os campos exatos do envelope e transforma qualquer `to` diferente de `team` em ramo de erro.
- **Switch**: roteia os seis `type`; `progress` termina sem enviar e valor inválido falha sem Outlook.
- **Code — montar**: renderiza o Markdown essencial em HTML, monta opções/default, assunto e linha de corte obrigatória.
- **Outlook — draft/create**: cria o rascunho e devolve os identificadores reais do Graph.
- **Data Table**: persiste `internetMessageId`, `conversationId` e `reply_to` para o casamento do F2.
- **IF + Code + Read/Write Files + Outlook attachment + Aggregate**: somente `preview` lê todos os caminhos locais, anexa ao mesmo rascunho e aguarda o lote.
- **Outlook — draft/send**: envia uma vez, com ou sem anexos.
- **IF + Teams**: cria aviso no canal para `question`, `preview`, `blocked` e `done`; `preflight` não cria card.
- **Stop And Error**: impede de forma visível qualquer tentativa de envio para `requester` ou outro destinatário.

### F2 — `esteira-comms-in`

- **Outlook Trigger**: inicia a cada nova mensagem não lida.
- **HTTP Request com OAuth do Outlook**: busca no Graph o corpo e `internetMessageHeaders`, ausentes da seleção do trigger.
- **Data Table**: carrega as correlações gravadas pelo F1.
- **Code — casar**: tenta, em ordem, headers, conversa e regex; limpa HTML, corta a linha obrigatória, remove linhas citadas com `>` e aplica `trim`.
- **IF**: separa mensagens identificadas das não identificadas.
- **HTTP Request**: faz `POST` no `reply_to` com apenas `resposta` e `autor`.
- **Outlook — move**: move o caso sem casamento para `Esteira/nao-identificado`.
- **Teams**: avisa o canal sobre a mensagem não identificada.

## Saída real de `import:workflow`

Os comandos pedidos foram executados primeiro contra a configuração padrão da instância. O sandbox permite ler, mas não gravar, o SQLite dessa instância; por isso ambos chegaram ao importador e falharam por infraestrutura:

```text
Importing 1 workflows...
An error occurred while importing workflows. See log messages for details.
SQLITE_READONLY: attempt to write a readonly database
SQLITE_READONLY: attempt to write a readonly database
saida=1
Importing 1 workflows...
An error occurred while importing workflows. See log messages for details.
SQLITE_READONLY: attempt to write a readonly database
SQLITE_READONLY: attempt to write a readonly database
saida=1
```

A prova foi repetida com o mesmo binário n8n 2.36.8 e os mesmos comandos, alterando somente `N8N_USER_FOLDER` para um diretório temporário gravável. Na repetição final, `N8N_DIAGNOSTICS_ENABLED=false` evitou apenas o ruído de telemetria. Saída real de F1:

```text
Importing 1 workflows...
Successfully imported 1 workflow.
saida=0
```

Saída real de F2:

```text
Importing 1 workflows...
Successfully imported 1 workflow.
saida=0
```

## Placeholders para configuração humana

- credencial `Outlook — Esteira`;
- credencial `Teams — Esteira`;
- endereço interno da equipe (`equipe@CONFIGURAR.invalid`);
- IDs do Team e canal;
- ID da pasta `Esteira/nao-identificado`;
- Data Table `esteira_comms` e suas oito colunas.

## Não resolvido

- O download alternativo de anexos pelo raw do GitHub não foi implementado. F1 cobre a opção preferencial indicada no contrato: leitura de `anexos[].caminho` na mesma máquina do worker/n8n. URL remota é recusada antes do envio para não produzir preview sem anexo.
- Sem credenciais e IDs reais não foi possível executar uma entrega Outlook/Teams ponta a ponta; a prova exigida nesta rodada é a importação real dos JSONs pelo n8n 2.36.8.
