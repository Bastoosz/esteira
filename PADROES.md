# Padrões — Esteira Andrade Maia

## O que estamos fazendo

Um **fazedor de V1s com qualidade**. Não um fazedor de produtos.

A V1 existe para que (a) o advogado veja algo concreto e reaja, e (b) a
equipe continue a partir dela. Nada mais.

## Ordem de preferência — pare no primeiro que resolve

1. **Fluxo n8n** — automação, integração, disparo, agendamento, notificação
2. **Script Python** — processamento, planilha, dado, relatório, conversão
3. **Python + interface (Stack 1)** — só quando alguém precisa usar pela tela
4. **Stack 2** — só com aval humano explícito. Nunca escolha sozinho.
5. **Qualquer outra coisa** — pergunte antes

## Valores, em ordem de desempate

    funciona  >  estável  >  simples  >  elegante

Entrega rápida ganha de solução completa. Sempre.

## Proibido sem perguntar

- banco de dados novo
- serviço pago, assinatura ou conta nova
- framework que a equipe não usa
- dependência pesada quando a biblioteca padrão resolve
- reescrever algo que já funciona
- escolher Stack 2

## Modelos — não negociável

| Uso | Ferramenta |
|---|---|
| Agente líder (planeja, integra, revisa) | **Claude Code** (assinatura) |
| Implementação alternativa / revisão cruzada | **Codex** (assinatura) |
| Sub-tasks | **OpenCode** e **Antigravity** (modelos free por padrão) |
| Sub-tasks avulsas via API | **OpenRouter — só modelos free** |
| LLM dentro do código que você **escreve** | OpenRouter, conforme o Guia de Stacks |

Regra de manutenção: **id de modelo free não é configuração estável, é
validade.** Eles saem do ar sem aviso e o CLI falha de um jeito que parece
bug da esteira. Antes de investigar qualquer coisa em `opencode`/`agy`,
rode `opencode models | grep -- -free` e confirme que o id do `.env` ainda
existe. Isso é ajuste de `.env`, nunca de código.

Medido, não suposto: **em cinco dias morreram dois ids** —
`deepseek-v4-flash-free` e depois `hy3-free`, que tinha sido verificado em
28/08 e já não existia em 02/09. Não é evento raro; é manutenção.

Por isso o `.env` carrega uma **lista de reserva** em comentário, e não só
o id em uso. Quando o do momento cair, troque pelo próximo — sem
investigação, sem tocar código.

E a prova de um candidato é **de disco, não de texto**: peça um arquivo e
confira se ele apareceu. Modelo que responde "ok" e não escreve nada passa
num teste de texto e falha em produção — é o mesmo modo de falha do `agy`
sem `--dangerously-skip-permissions`.

**Proibido: modelo pago via API do OpenRouter para rodar o agente.**
O trabalho grande vai nas assinaturas Claude e Codex da equipe. Elas são
fixas — o que limita é rate limit e tempo, não dinheiro. Por isso os tetos
são em **turnos, tempo e rodadas**, nunca em dólar.

## Contas da equipe

São 4 pessoas, cada uma com assinatura Claude e Codex. O registro está em
`contas.yaml` — que **não contém segredo**, só o caminho do diretório onde
cada CLI guarda a própria autenticação.

Política em `config.py` → `POLITICA_CONTA`:

| valor | comportamento | quando usar |
|---|---|---|
| `dona` | roda na conta do dono da demanda | **padrão** |
| `fixa` | tudo numa conta | para começar, mais simples |
| `rodizio` | round-robin entre as ativas | só depois de confirmar os termos das assinaturas |

Toda execução registra em qual conta rodou. O board mostra "rodando no
Claude do João". Quem está pagando a execução tem direito de saber.

## O que invalida uma V1

Independente de passar no `check.sh`:

- layout fora do design system
- estrutura de pastas fora do template
- dado saindo mal formatado
- entrega que não chega onde deveria (e-mail, arquivo, tela)
- faltando informação que o pedido mencionava
- regra jurídica inventada pelo agente

## Português

Nomes técnicos em inglês. Comentário, UI, mensagem de erro, prompt e
documentação em **PT-BR**.

Regra dura de marca: **toda palavra estrangeira em itálico** — `<i>` ou
`.foreign`. Vale para "upload", "download", "dashboard", "login",
"preview", "deploy". O `check_ds.sh` verifica.

## Definição de pronto (rodada)

- [ ] `plano.md` escrito, com premissas listadas
- [ ] `check.sh` verde
- [ ] `check_ds.sh` verde
- [ ] artefato real gerado em `outbox/` via `esteira-provar`
- [ ] `journal.md` conta a história de forma legível
- [ ] regra jurídica, se houver, marcada como `REGRA-JURIDICA` e não implementada
