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

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    cp .env.example .env          # ajuste os comandos dos CLIs
    cp -r projects/_exemplo projects/<seu-projeto>

    # NENHUM código Python lê o .env. Carregue você:
    set -a; . ./.env; set +a      # ou EnvironmentFile= no systemd (Dia 3)

    # autenticar cada conta num diretório próprio
    mkdir -p ~/.esteira-auth/<pessoa>/claude ~/.esteira-auth/<pessoa>/codex
    chmod 700 ~/.esteira-auth ~/.esteira-auth/<pessoa>
    CLAUDE_CONFIG_DIR=~/.esteira-auth/<pessoa>/claude claude   # faz login
    CODEX_HOME=~/.esteira-auth/<pessoa>/codex codex            # faz login
    # marque ativo: true em contas.yaml SÓ depois do smoke passar:
    .venv/bin/python -c "import sys;sys.path.insert(0,'.');\
from esteira import runner,contas;\
print(runner.smoke_test('lead', contas.disponiveis('claude')[0]))"

    .venv/bin/python board.py                # http://localhost:5000
    .venv/bin/python -m esteira.worker       # outro terminal
    .venv/bin/python -m esteira.vigia        # outro terminal

Diretório de autenticação PRÓPRIO da esteira, não o `~/.claude` da pessoa:
apontar para o do dia a dia faz o agente herdar settings, hooks e plugins
do humano — comportamento que ninguém declarou e que você vai debugar às
2h da manhã. Isso foi medido: o mesmo smoke com `CODEX_HOME` do host roda
12 hooks; com o diretório da esteira, zero.

Efeito colateral do isolamento, para você não estranhar: sem o
`config.toml` do host, o codex usa o modelo padrão da conta e não o que
você pinou para si. Se a esteira precisar de um modelo específico, isso
vai no `CMD_CODEX` (`-m`), não no `config.toml` de ninguém.

### Se a credencial foi COPIADA em vez de logada

Dá para semear o diretório copiando `~/.claude/.credentials.json` e
`~/.codex/auth.json` (modo 600). Funciona, e foi assim no Dia 1.

**O preço:** a cópia é um retrato. Quando o CLI do dia a dia renova o
token, a cópia da esteira **não** renova — ela vence sozinha, em silêncio,
e a demanda quebra no meio em vez de na largada. Não existe aviso.

Duas defesas, nesta ordem:

1. `smoke_todas()` de hora em hora, alertando o dono da conta
   (`SMOKE_INTERVALO_S` em `config.py`, previsto para o Dia 6). Enquanto
   isso não sobe, a cópia é dívida.
2. Quando vencer, não copie de novo: faça o login de verdade dentro do
   diretório, que é o que renova sozinho.

       CLAUDE_CONFIG_DIR=~/.esteira-auth/nicolas/claude claude
       CODEX_HOME=~/.esteira-auth/nicolas/codex codex

Só o board sobe por padrão com a demanda de exemplo `1001` para você ver
o formato. Apague `demands/1001/` quando for valer.

## Estado real desta máquina — conferido no Dia 1 (2026-08-28)

Cada linha foi provada com `runner.smoke_test(tier)`, não lida no `--help`.

| tier | CLI | veredito |
|---|---|---|
| `lead` | claude 2.1.250 | OK — exige `--verbose` junto com `stream-json` |
| `codex` | codex-cli 0.150.1 | OK — `-s workspace-write`, modelo gpt-5.4 |
| `opencode` | opencode 1.18.18 | OK — `--auto` + `-m` obrigatórios |
| `agy` | Antigravity CLI | OK — prompt em **argv**, e a flag do prompt por último |
| `orca` | orca 1.4.190 | não é runtime; ver "Sobre o Orca" |

Quatro coisas que só aparecem quando você roda:

1. **`agy` falha de um jeito que parece sucesso.** Duas armadilhas nele:

   - não lê prompt de stdin — quer o prompt como valor de `-p`; com stdin
     sai com 2 e imprime o usage. `config.RUNTIMES` já declarava
     `stdin_prompt` por runtime, e o `runner.py` passou a respeitar;
   - sem `--dangerously-skip-permissions` ele **responde, sai com 0 e não
     escreve nada**: em headless auto-nega a permissão `command`. Um tier
     que sai 0 e não toca o disco é exatamente o modo de falha que o
     `esteira-delegate` foi feito para pegar — e pegaria, dizendo "nada
     mudou no disco", sem nunca explicar por quê.

   - e a **ordem das flags importa**. O runner anexa o prompt no fim do
     `argv`, então a flag que recebe o prompt tem que ser a última. Com
     `agy -p --dangerously-skip-permissions` o próprio agy avisa que `-p`
     tomou a flag como prompt e ignorou o texto. O certo é
     `agy --dangerously-skip-permissions -p`.

   Provado em 2026-08-28: `codigo=0`, arquivo escrito no disco.

2. **Modelo free do OpenCode sai do ar sem aviso.** O default do
   `~/.config/opencode/opencode.jsonc` (`deepseek-v4-flash-free`) já não
   existe; `hy3-free` e `mimo-v2.5-free` foram verificados escrevendo em
   disco. Confira com `opencode models | grep -- -free` antes de culpar
   a esteira.
3. **O `codex` estava instalado e ainda assim não existia.** O `npm i -g`
   tinha morrido no meio: o pacote no lugar, a dependência nativa
   (`@openai/codex-linux-x64`) faltando, e no lugar do link `codex` um
   `.codex-KEfGGw34` de instalação interrompida. `command -v codex` não
   achava nada. `npm install -g @openai/codex@latest` resolveu. Vale a
   primeira suspeita quando um tier "não está instalado".

4. **`n8n` não está instalado nesta máquina.** Dia 2 em diante depende
   dele. Até subir, `esteira-ask` e `esteira-deliver` não têm para onde
   mandar o e-mail.

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
