# n8n — só as bordas

O n8n **não guarda estado** e **não decide nada**. Ele é a secretária:
monta o e-mail, manda, escuta a resposta e entrega no worker.

O estado da pergunta vive em `demands/<id>/questions/N.json`, versionado
em git. Se uma execução do n8n morrer, a pergunta não fica órfã.

Quatro fluxos. Não mais.

| # | Fluxo | Gatilho |
|---|---|---|
| F1 | `esteira-comms-out` | Webhook `POST /webhook/esteira-comm` |
| F2 | `esteira-comms-in` | Outlook (Graph), nova mensagem na caixa da esteira |
| F3 | `esteira-intake` | Outlook, nova mensagem na caixa de demandas |
| F4 | `esteira-digest` | Schedule, 8h em dia útil |

---

## F1 — comms-out

    Webhook  →  Switch (type)  →  monta e-mail  →  Outlook: enviar  →  Teams: card

Recebe o envelope descrito em `../esteira/comm.py`.

Assunto: `[esteira #{{demand_id}}-{{n}}] {{titulo}}`
Corpo: `{{body_md}}` renderizado, com as opções como lista, depois:

    Se ninguém responder, o agente segue com: <default>

    --- responda acima desta linha ---
    demanda #<id> · rodada <n> · <titulo_demanda>

**A linha de corte é obrigatória.** O F2 descarta tudo abaixo dela.
Sem isso o agente recebe a thread citada inteira, mais assinatura de
rodapé, como se fosse instrução.

Roteamento por `type`:

| type | e-mail | Teams | espera resposta |
|---|---|---|---|
| `preflight` | sim | — | não |
| `question` | sim | card | sim |
| `preview` | sim, com anexos | card | sim |
| `blocked` | sim | card marcado | sim |
| `done` | sim | card | não |
| `progress` | — | — | não |

Anexos: baixe de `anexos[].caminho` (o worker roda na mesma máquina) ou
do raw do GitHub no branch da demanda.

**Regra dura:** `to` só aceita `team`. Se algum dia chegar `requester`,
o Switch cai no ramo de erro. O agente não fala com o demandante.

---

## F2 — comms-in

    Outlook trigger  →  Code: casar mensagem  →  IF casou  →  POST reply_to
                                              └→ pasta "não identificado"

Casamento, em ordem:

1. cabeçalhos `In-Reply-To` / `References` contra o `Message-ID` que o F1
   enviou (o cliente de e-mail copia sozinho — é o caminho principal)
2. `conversationId` do Graph
3. regex `\[esteira #(\d+)-(\d+)\]` no assunto

Nenhum dos três casou → não invente. Move para a pasta
`Esteira/nao-identificado` e manda um card no Teams.

Corte do corpo: tudo antes de `--- responda acima desta linha ---`,
depois remove citação (`>`), depois `trim`.

    POST {{reply_to}}
    { "resposta": "<texto>", "autor": "<remetente>" }

O `reply_to` aponta para o **worker**, nunca para o resume URL do n8n.
O endpoint é idempotente: entrega duplicada é descartada.

---

## F3 — intake

    Outlook trigger  →  Code: normalizar  →  POST /intake  →  Outlook: confirmação

Normalize para:

    { "titulo": "<assunto sem prefixo>", "corpo": "<corpo limpo>",
      "remetente": "<email>", "projeto": "<mapeado>", "dono": "<id da pessoa>",
      "anexos": [...], "idempotency_key": "<internetMessageId>" }

Mapeamento de projeto, em ordem: prefixo `[projeto]` no assunto →
tabela remetente→projeto → `_triagem` (card no Teams: "de qual projeto é?").

`dono` define em qual assinatura Claude a demanda vai rodar. Se não der
para inferir, cai na política `fixa`.

**`idempotency_key` é obrigatório.** E-mail duplica. Sempre.

---

## F4 — digest

Todo dia útil às 8h, um e-mail: o que está travado, o que espera resposta
há mais de 4 horas, o que foi entregue ontem, e quais contas estão de molho
ou não autenticadas.

É o que impede uma demanda de ficar esquecida por uma semana num volume
de 2-3 por semana.
