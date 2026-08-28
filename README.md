# Esteira — Andrade Maia

Um **fazedor de V1s com qualidade**.

Demanda chega por e-mail → o agente monta uma primeira versão → a equipe
revisa e continua. O agente não entrega produto final e nunca fala com o
demandante.

## Como isso funciona, em uma tela

    Outlook ──► n8n (F3 intake) ──► demands/<id>/  (git é a verdade)
                                        │
                                   worker (1 por vez)
                                        │
                    Claude Code na assinatura do dono da demanda
                                        │
              ┌─────────────────────────┼──────────────────┐
              ▼                         ▼                  ▼
     esteira-delegate           esteira-ask          esteira-provar
   (codex/opencode/agy)       exit 42, PARA        gera o artefato real
                                    │                      │
                              n8n (F1) ──► Outlook ──► vocês
                                    │
                              vocês respondem o e-mail
                                    │
                              n8n (F2) ──► worker /answer
                                    │
                              execução NOVA lê a pasta

Nada fica esperando na memória. Retomar depois de 10 minutos ou de 3 dias
é o mesmo código — e é por isso que reiniciar a máquina não perde nada.

## O que roda onde

| Peça | Onde |
|---|---|
| n8n | Docker, na máquina dedicada |
| worker + vigia | host (systemd), fora do Docker |
| CLIs de agente | host — autenticar CLI dentro de container com assinatura é dor |
| board | host, Flask na porta 5000, acesso pela rede do escritório |

**Nenhuma porta aberta para fora.** Tudo sai da máquina: n8n lê a caixa
(saída), manda e-mail (saída), o agente fala com localhost, o git empurra
para o GitHub (saída).

## Subir

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env          # ajuste os comandos dos CLIs
    cp -r projects/_exemplo projects/<seu-projeto>

    # autenticar cada conta num diretório próprio
    mkdir -p ~/.esteira-auth/joao/claude ~/.esteira-auth/joao/codex
    CLAUDE_CONFIG_DIR=~/.esteira-auth/joao/claude claude
    CODEX_HOME=~/.esteira-auth/joao/codex codex
    # marque ativo: true em contas.yaml

    python board.py                          # http://localhost:5000
    python -m esteira.worker                 # outro terminal
    python -m esteira.vigia                  # outro terminal

Só o board sobe por padrão com a demanda de exemplo `1001` para você ver
o formato. Apague `demands/1001/` quando for valer.

## Contas — leia antes de ligar rodízio

`contas.yaml` **não contém segredo**: só o caminho do diretório onde cada
CLI guarda a própria autenticação.

Política em `config.py` → `POLITICA_CONTA`:

- **`dona`** (padrão) — a demanda roda na conta do dono. Defensável,
  atribuível, e é o que o board mostra.
- **`fixa`** — tudo numa conta. Mais simples para começar.
- **`rodizio`** — round-robin. **Confirme os termos das assinaturas Claude
  e Codex antes de ligar.** Assinatura individual usada como capacidade
  compartilhada por um servidor é provavelmente fora dos termos, e conta
  suspensa no meio de um projeto é um problema de verdade.

Aritmética que vale checar antes: 2-3 demandas por semana × ~3 rodadas
≈ 9 execuções semanais. Uma assinatura aguenta. Você provavelmente
precisa de **atribuição**, que já está pronta, e não de roteamento.

## Os tetos são em turno e tempo, não em dinheiro

As assinaturas são fixas. O que limita é rate limit e tempo. Ver
`MAX_TURNOS`, `TIMEOUT_RODADA_S`, `MAX_RODADAS` em `config.py`.

## Três tempos de vida dos arquivos

| | Onde vive | Destino |
|---|---|---|
| **fixo** | `AGENTS.md`, `PADROES.md`, `STACKS.md`, `projects/*/`, `papeis/` | nunca apaga — **compacta** ao passar do teto |
| **durável** | `demands/<id>/README.md`, `plano.md`, `feedback/`, `outbox/` | `_arquivo/` 30 dias depois de fechar |
| **efêmero** | `journal.md`, `notas.jsonl`, `runs/*.log` | vive só no branch `agent/<id>`; morre com o branch |

Auto-exclusão para efêmero. Auto-compactação para fixo. Nunca apague
conhecimento automaticamente; nunca guarde log automaticamente.

A exclusão é `git branch -D`, não um cron que você vai ter medo de rodar.

## O ciclo que faz a qualidade subir

Nota do agente → alguém clica **fixar** no board → vira linha em
`projects/<id>/context/armadilhas.md` → o próximo agente já sabe.

É esse loop, e não modelo melhor, que aumenta a taxa de acerto.

## A métrica que importa

    O primeiro commit humano depois da V1 foi ADITIVO ou CORRETIVO?

Só adicionou linhas → a V1 prestou. Apagou e reescreveu → não prestou.
Sai de graça de um `git diff --numstat`. Está na coluna final de `/numeros`.

## Antes do dia 1

Duas coisas que não estão neste repo e valem mais que ele:

1. **`template-stack1-flask-htmx`** e **`template-stack2-fastapi`**, com o
   design system já ligado e os partials Jinja prontos (button, input,
   select, checkbox, card, badge, tabela, upload, vazio, erro). O agente
   preenche estrutura pronta em vez de inventar. Sua própria definição de
   qualidade — "não mexer no layout nem na estrutura" — depende disso.
2. **`refs/n8n/`** com 5 ou 6 fluxos reais de vocês. Ver `refs/README.md`.

## Sobre o Orca

O Orca (Stably) é um ADE de desktop: roda vários CLIs de agente em
paralelo, cada um em worktree git próprio, com as assinaturas de vocês.

**Como IDE para construir a esteira: ótimo, e nada aqui precisa mudar.**
Isso vai no prompt inicial da sessão, não no repo.

**Como runtime da esteira: cuidado.** Ele sobrepõe parte do que o worker
já faz (worktree, rodar CLI, acompanhar uso) e foi desenhado para ter um
humano dirigindo. A esteira precisa rodar sozinha às 2h da manhã. Se for
tentar, confirme a invocação headless (`orca serve`) antes e preencha
`CMD_ORCA` no `.env`.

**Risco concreto se rodarem juntos na mesma máquina:** Orca e worker vão
criar worktrees nos mesmos repositórios ao mesmo tempo. Mantenha o
workspace da esteira (`workspace/`) fora de qualquer pasta que o Orca
gerencie, e não abra no Orca um repo que a esteira está tocando.

Recomendação: **Orca como IDE, worker como runtime.** Escolha um dos dois
para dirigir; não os dois pela metade.
