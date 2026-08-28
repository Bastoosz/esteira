# Plano de construção — para rodar no Claude Code

Este repo é o esqueleto: contratos, documentos e as peças que carregam
decisão. Falta ligar nas ferramentas reais.

Ordem importa. Cada item é entregável em horas, não dias.

## Dia 0 — antes de tocar nesse repo

- [ ] **`template-stack1-flask-htmx`** com o DS ligado e 9 partials Jinja
      (button, input, select, checkbox, card, badge, tabela, upload,
      vazio/erro). Traduza os `.jsx` do DS — o `.prompt.md` de cada
      componente já documenta variantes e props.
      Os componentes do DS são React; a Stack 1 é Jinja. Os **tokens**
      atravessam sem mudança; os componentes não.
- [ ] Copiar para o template só: `tokens/`, `styles.css`, `assets/fonts/`,
      `assets/logos/`, `assets/icons/`. Dá ~4 MB (o zip inteiro tem 64 MB,
      quase tudo duplicata em `uploads/`).
- [ ] Escolher **um** projeto real e escrever `projects/<id>/` de verdade:
      `AGENTS.md`, `check.sh` que funciona, `context/dominio.md`.
      `check.sh` que não roda = projeto que não entra na esteira.

## Dia 1 — fundação

- [ ] `git init` + remote privado no GitHub. Sem isso não há durabilidade.
- [ ] `pip install -r requirements.txt`; `python board.py` sobe e mostra a 1001
- [ ] Autenticar **uma** conta (`POLITICA_CONTA=fixa`) e rodar
      `python -c "import sys;sys.path.insert(0,'.');from esteira import runner;print(runner.smoke_test('lead'))"`
- [ ] `esteira/runner.py` — conferir `RUNTIMES` em `config.py` contra os
      CLIs de fato instalados. **É aqui que mora a fragilidade.** Regra que
      não se quebra: nunca lê a prosa do CLI para saber o que aconteceu.

## Dia 2 — a conversa

- [ ] F1 `esteira-comms-out` no n8n (só `question` e `preflight`)
- [ ] Linha `--- responda acima desta linha ---` no corpo. Obrigatória.
- [ ] F2 `esteira-comms-in`: casar por `In-Reply-To`/`References`, fallback
      `conversationId`, fallback regex no assunto, senão pasta "não
      identificado" + card no Teams
- [ ] Testar `POST /answer/1001/1001-1` na mão antes de plugar o n8n

## Dia 3 — o ciclo fechado

- [ ] `python -m esteira.worker` roda a 1001 de verdade
- [ ] `esteira-ask` sai com 42, worker parqueia, resposta retoma
- [ ] `python -m esteira.vigia` como serviço; testar matando o processo do
      agente na mão e vendo o card de travamento chegar
- [ ] `systemd`: worker e vigia com `Restart=always`

## Dia 4 — entregar

- [ ] `esteira-provar` gerando artefato real (XLSX, e-mail renderizado, print)
- [ ] `esteira-deliver` recusando sem artefato em `outbox/` — confirmar
- [ ] F1 com `preview` + anexos
- [ ] `check_ds.sh` no `check.sh` do projeto

## Dia 5 — n8n como entregável

- [ ] `papeis/subtask-n8n.md` + `refs/n8n/` com os fluxos reais
- [ ] `esteira-deliver` sobe `workflow.json` via API do n8n no projeto
      `rascunhos`, **sempre inativo**, credencial `dashboards`
- [ ] Card no Teams: "está no n8n em rascunhos/#<id>, abre e testa"

## Dia 6 — intake

- [ ] F3 `esteira-intake` com `idempotency_key` = `internetMessageId`
- [ ] Mapeamento remetente → projeto → `dono`
- [ ] F4 `esteira-digest` às 8h
- [ ] `smoke_todas()` de hora em hora, alertando o **dono** da conta

## Dias 7 a 10 — as demandas reais

Rodar 4 ou 5 demandas de verdade.

**Todo ajuste vai no `AGENTS.md`, no `PADROES.md` e no `armadilhas.md` —
não no código.** Se você estiver mexendo no worker no dia 8, algo está
errado: ou o contrato está mal desenhado, ou você está construindo a
coisa errada.

## Depois — só quando doer

| Adote | Gatilho |
|---|---|
| `POLITICA_CONTA=rodizio` | você bateu em rate limit de verdade **e** confirmou os termos |
| Postgres | você quis fazer uma pergunta analítica e o `jq` doeu |
| 2 demandas simultâneas | a fila engasgou por 2 semanas seguidas |
| Container por demanda | o agente vai rodar código de terceiros |
| Revisão cruzada (`subtask-revisao`) | ≥50% dos findings se provarem úteis num teste de 10 PRs |

Nada disso "para estar pronto".

## O que NÃO construir

Roteamento de modelo com aprendizado · DAG de agentes · agente efêmero com
ciclo de vida · registry em banco · message broker · Temporal · Vault · RAG ·
teto em dólar · merge automático (nunca, em versão nenhuma).
