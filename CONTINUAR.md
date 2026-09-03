# Continuar daqui

Estado em **2026-09-03**. Este arquivo é para retomar; o histórico do que
mudou e por quê está no `RELATORIO.md`, e o motivo de cada decisão de
orquestração está em `orquestracao/JOURNAL.md`.

**O escopo mudou:** a esteira vai virar um **executável Windows** que cada
dev instala. O plano está em `orquestracao/PLANO-DESKTOP.md`. O miolo não
muda — `runner.rodar` continua sendo o runtime, git continua sendo a verdade
da demanda, e o app é **rosto, não cérebro**.

## LEIA PRIMEIRO — duas coisas esperando humano

**1. A credencial de `nicolas:claude` venceu.** A dívida da cópia
materializou em 02/09: o host renovou o token às 08:45, a cópia da esteira
é de 28/08 e o *refresh* dela já não vale.

    Failed to authenticate: OAuth session expired and could not be refreshed

Isso **bloqueia rodar o worker** (ele exige conta `claude` ativa). A cura é
login de verdade, que é interativo:

    CLAUDE_CONFIG_DIR=~/.esteira-auth/nicolas/claude claude

Copiar de novo destrava mais rápido e **recria a mesma dívida**. A
recomendação é o login.

**2. O `agy` esgotou a cota individual.**

    Individual quota reached. Resets in 132h37m45s.   (medido em 03/09)

Ou seja até ~08/09. **A bancada tem 3 vagas úteis, não 4.** Não é a flag nem
a tarefa: o T-04 foi o último trabalho dele e consumiu o resto. Confirme com
`agy --dangerously-skip-permissions -p "OK"` antes de contar com a vaga 4.

Rode isto antes de acreditar em qualquer outra coisa deste arquivo:

    .venv/bin/python bin/esteira-maestro doctor

Ordem de leitura ao voltar: este arquivo → `BUILD.md` → `RELATORIO.md`
só quando precisar do detalhe de algum achado.

---

## 1. Onde está tudo

| o que | caminho | git |
|---|---|---|
| esteira | `~/Área de trabalho/esteira` | `Bastoosz/esteira`, privado, `main` empurrado |
| n8n | `npm -g`, dados em `~/.n8n` | não é repo; roda em `localhost:5678` |
| template Stack 1 | `~/orca/template-stack1-flask-htmx` | local, **sem remote** |
| projeto real | `~/orca/AMPLIA.APP_vers-o-2` | `AndradeMaia-Tech/AMPLIA.APP_vers-o-2` (não é nosso; só leitura) |
| DS de origem | `~/Área de trabalho/Projeto Disney/Jornada-Do-Cliente/o-jeito-am` | não é nosso; fonte dos tokens |
| auth da esteira | `~/.esteira-auth/nicolas/{claude,codex}` | fora do git, modo 700 |

Portas: board na **5000**, demo do template na **5001**, n8n na **5678**.

Últimos commits da esteira:

    be6b00a Esteira Desktop: hub, tres telas, login guiado e telemetria no runner
    f9a2cf9 orquestracao: plano do Esteira Desktop, fila e as sete provas
    982e766 docs: registra o escaping que comeu 4 trechos da mensagem anterior
    290194d maestro: conserta 10 defeitos que a revisao adversarial achou
    b9f171f orquestracao: fecha T-09, T-10, T-13 e declara pytest
    be85ff9 docs: CONTINUAR.md com o estado de 02/09 e a bancada de orquestracao

---

## 2. Retomar em um minuto

    cd ~/Área\ de\ trabalho/esteira
    set -a; . ./.env; set +a          # NENHUM código lê o .env. Carregue você.
    .venv/bin/python board.py         # http://localhost:5000

Conferir os runtimes **e as contas**:

    .venv/bin/python bin/esteira-maestro doctor

Use o `doctor`, não o `smoke_test` cru. O smoke sem conta usa o
`~/.claude` do host e diz OK com a conta da esteira morta — foi medido em
02/09 e é a razão de o `doctor` testar por conta.

Se algum cair, é `.env` ou `config.py` — **não** é o worker. Ver secção 6.

Template:

    cd ~/orca/template-stack1-flask-htmx
    bash check.sh                     # compileall + import + check_ds
    .venv/bin/python app.py           # http://localhost:5001

n8n (2.36.8, instalado por npm; não há Docker nesta máquina):

    export PATH="$HOME/.nvm/versions/node/v24.18.0/bin:$PATH"
    export N8N_PORT=5678 N8N_SECURE_COOKIE=false N8N_DIAGNOSTICS_ENABLED=false
    n8n start                         # http://localhost:5678

---

## 3. Onde o `BUILD.md` está

### Dia 0 — FECHADO

- [x] `template-stack1-flask-htmx` com o DS ligado e 9 partials Jinja
- [x] Copiar tokens, `styles.css`, fontes, logos, ícones (deu 1,2 MB)
- [x] Um projeto real: `projects/amplia/` com `check.sh` que roda

Provas, rodadas por mim e não pelo relato do agente:

    bash projects/amplia/check.sh ~/orca/AMPLIA.APP_vers-o-2
    → 822 passed, 19 skipped, 38 xfailed em 101s        saída 0
    cd ~/orca/template-stack1-flask-htmx && bash check.sh   saída 0
    demo na 5001: am-btn 27x, am-box 20x, 3 tabelas, upload-field 15x
    os 4 CSS e a Sansation servem 200

**O `BUILD.md` estava errado sobre o DS.** Ele supõe um pacote com
`tokens/`, `styles.css`, `assets/` e um `.jsx` + `.prompt.md` por
componente, num zip de 64 MB. Esse pacote não existe nesta máquina. O DS
real vive dentro do app `o-jeito-am`: 72 tokens no `:root` do
`globals.css` e 3520 linhas de `am-identity.css`. Se alguém achar o zip
depois, compare com `static/ds/tokens/tokens.css` antes de substituir.

### Dia 1 — FECHADO

Os quatro itens verdes. Detalhe de cada quebra no `RELATORIO.md`.

### Dia 2 — CÓDIGO PRONTO, FALTA CREDENCIAL

- [x] F1 `esteira-comms-out` no n8n — 17 nós, importa
- [x] Linha `--- responda acima desta linha ---` — F1 escreve, F2 corta
- [x] F2 `esteira-comms-in` — 8 nós, importa
- [x] Testar `POST /answer/1001/1001-1` na mão

**O que falta para o Dia 2 fechar de verdade:** credencial. Sem Outlook e
Teams reais não há entrega ponta a ponta. Os dois fluxos entram
**inativos** e o `n8n/COMO-IMPORTAR.md` lista o que configurar à mão:
credencial `Outlook — Esteira`, credencial `Teams — Esteira`, endereço da
equipe (hoje `equipe@CONFIGURAR.invalid`), IDs do Team e do canal, ID da
pasta `Esteira/nao-identificado`, e a Data Table `esteira_comms`.

Importar:

    export PATH="$HOME/.nvm/versions/node/v24.18.0/bin:$PATH"
    n8n import:workflow --input=n8n/esteira-comms-out.json
    n8n import:workflow --input=n8n/esteira-comms-in.json

**Se mexer no `WORKER_BASE` do F2**, ele está fixo no topo do nó
`Casar mensagem e cortar corpo` e precisa bater com `WORKER_BASE_URL` do
`.env`.

O endpoint `/answer` (`board.py:126`) foi testado nos quatro caminhos:

    1001-1 já respondida  → 200 {"ok":true,"nota":"resposta já registrada (idempotente)"}
    resposta vazia        → 400 {"ok":false,"erro":"resposta vazia"}
    demanda inexistente   → 404
    pergunta 2 aberta     → 200, answers/2.md gravado com autor e horário,
                            estado transitou EM_REVISAO → PRONTA

A demanda 1001 foi restaurada com `git checkout` depois do teste.

Conferido de passagem: o `msg_id` bate. O `board.py` deriva o número da
pergunta com `msg_id.split("-")[-1]`, e o `esteira-ask` passa
`msg_id=f"{d.id}-{n}"` explícito — por isso `1001-1` dá `n=1`. O
`comm.envelope` monta um `msg_id` diferente por padrão
(`{id}-{tipo}-{timestamp}`), mas só para tipos que não voltam pelo
`/answer`. Não mexa nisso sem olhar os dois lados.

`n8n` foi instalado por `npm install -g n8n` (não há Docker nesta
máquina). O `n8n/README.md` já tem a especificação completa de F1 a F4 —
é o documento a seguir para escrever os fluxos.

**Cuidado ao gerar o JSON dos fluxos:** o `refs/README.md` avisa que
fluxo n8n gerado do zero "costuma nem abrir". Não aceite JSON que não
tenha passado por `n8n import:workflow --input=<arquivo>`. `refs/n8n/`
**deixou de estar vazia** no T-09: tem os dois fluxos exportados e
sanitizados, mais um README dizendo o que cada nó ensina.

### Dia 3 — PEÇAS PRONTAS, BLOQUEADO NA CREDENCIAL

- [x] Demanda `1002` real, em `PRONTA`, que o worker pega
      (`proxima_da_fila()` devolve `1002`)
- [x] Roteiro de prova em `orquestracao/roteiros/ciclo-dia3.md`
- [x] `deploy/` com os 4 units, `PATH` declarado no unit,
      `Restart=always`, `systemd-analyze verify` sai 0
- [ ] **Rodar o worker de verdade** — bloqueado: exige conta `claude`
      ativa, e a de `nicolas` está com OAuth expirado (ver LEIA PRIMEIRO)
- [ ] Matar o processo do agente à mão e ver o card do vigia — depende do
      item acima

A 1001 **não serve** para provar o ciclo: é *fixture*, escrita à mão. Os
dois registros de `execucoes.jsonl` têm o mesmo *timestamp* da criação,
`runs/` está vazio, e o journal salta `NOVA -> EM_REVISAO`. Por isso a
1002 existe.

**Antes de rodar o worker, leia:** ele faz `git add -A` + `commit` +
`push` na `BASE_DIR` a cada rodada. Não rode com trabalho paralelo no
repo — ele comita o que estiver pela metade.

### Dia 6, adiantado — a sentinela

- [x] `esteira/sentinela.py` + `bin/esteira-smoke`: roda `smoke_todas()`
      e avisa o dono de cada conta que falhar.
      `--uma-vez` para cron, `--simular-falha <chave>` para testar.
      Unit e timer em `deploy/esteira-smoke.{service,timer}`, `OnCalendar=hourly`.

Isto foi adiantado do Dia 6 de propósito: é a defesa que converte a dívida
da credencial copiada em aviso. **Pegou um problema real na primeira
execução** — a conta `nicolas:claude` vencida.

### Dias 4 e 5 — não começados

Ler o `BUILD.md`. Antes do Dia 3, ver a armadilha do `systemd` na
secção 6 — ela vai morder.

---

## 4. Decisões

### 4.1 Montserrat — RESOLVIDO, auto-hospedada

O `tokens.css` usa `--font-display: var(--font-montserrat), "Montserrat", …`.
No app de origem, `--font-montserrat` era injetada pelo `next/font`. Fora
do Next ela não existe, e `var()` sem *fallback* para variável indefinida
**invalida a declaração inteira** — não cai para o próximo item da lista.
Todo título perderia a Montserrat em silêncio, com os dois gates verdes.

Resolvido em `static/ds/tokens/fontes.css`: define `--font-montserrat` e
carrega a fonte do disco. Fonte **variável** (pesos 100–900 num arquivo
só, então não há peso faltando por engano), normal e itálico,
subconjuntos `latin` e `latin-ext` apenas. Corta de 10 arquivos para 4,
232 KB. `OFL.txt` junto, que a licença exige ao redistribuir.

Auto-hospedar e não `<link>` do Google pelo mesmo motivo da Sansation:
nada de rede de terceiro no momento de renderizar. A esteira roda sozinha
às 2h da manhã.

Provado: os 4 `woff2` têm assinatura `wOF2`, servem 200, e o subconjunto
`latin` cobre todo acento de PT-BR (`ã ç é õ ú à ê ô í â` e maiúsculas).

### 4.2 Remote do template

`~/orca/template-stack1-flask-htmx` só tem git local. O `STACKS.md`
manda **clonar** o template — sem remote, ninguém clona. Proposta:

    cd ~/orca/template-stack1-flask-htmx
    gh repo create AndradeMaia-Tech/template-stack1-flask-htmx \
      --private --source=. --remote=origin --push

---

## 5. Dívidas, em ordem de dor

1. **Credencial copiada, não logada.** `~/.esteira-auth/nicolas/` foi
   semeado copiando `~/.claude/.credentials.json` e `~/.codex/auth.json`.
   A cópia é um retrato: quando o CLI do dia a dia renova o token, ela
   **não** renova — vence em silêncio e a demanda quebra no meio, não na
   largada. Duas defesas, nesta ordem: subir o `smoke_todas()` de hora em
   hora (Dia 6), e quando vencer fazer login de verdade dentro do
   diretório em vez de copiar outra vez:

       CLAUDE_CONFIG_DIR=~/.esteira-auth/nicolas/claude claude
       CODEX_HOME=~/.esteira-auth/nicolas/codex codex

2. **`base.html` do board está fora do DS.** Tema claro, `--radius: 2px`,
   nomes de token inventados (`--am-gray-050`, `--space-*`). O DS real é
   preto, `--radius: 0px` + chanfro 45°, `--ink-1..5`. O template agora é
   a referência correta; o board é que divergiu. Não é urgente — o board
   é ferramenta interna — mas é incoerente pregar aderência ao DS num
   arquivo que não adere.
3. **Sansation sem licença no repo.** A Montserrat foi
   redistribuída com o `OFL.txt` junto, como a licença exige. A
   Sansation está em `assets/fonts/` sem nenhum arquivo de licença.
   Confirmar os termos dela antes de o template sair do escritório.
4. **`python-dotenv` no template.** A esteira carrega `.env` por
   `EnvironmentFile=`; o template usa `load_dotenv()`. Divergência
   pequena, mas é uma dependência a mais no molde de todo projeto Stack 1.
5. **HTMX por CDN** no template e no board (`cdn.jsdelivr.net`,
   `unpkg.com`). Dependência externa no momento de renderizar.
6. **`.am-seal` e `.am-pattern` ficaram fora do `styles.css`.** São
   elementos de marca; o worker os classificou como auxiliares. Vale
   reavaliar numa segunda passada.
7. **`template-stack2-fastapi` não existe.** O `STACKS.md` promete.

---

## 5.4 Esteira Desktop — onde está

Fechado, com prova rodada pelo `esteira-maestro provar`:

| item | o que é | onde |
|---|---|---|
| D1 | hub SQLite + 3 endpoints no board | `esteira/hub/{db,api}.py` |
| D3 | telemetria no `runner`, best-effort | `esteira/hub/reporte.py` |
| E1 | as três telas contra o hub | `app/` |
| F1 | login guiado por pessoa e runtime | `esteira/login.py`, `bin/esteira-login` |
| G1 | F1 do n8n por `amknowledge@andrademaia.com` | `n8n/esteira-comms-out.json` |
| I1 | as APIs pagas, com dono e o que cai | `refs/ferramentas.md` |

Em voo: **D4** (semear o hub com o histórico) e **E5** (guard de WebView2).

### O achado de Windows que muda o app

`orquestracao/spikes/windows.md`. Resumo: **sem o WebView2 Runtime, o
`pywebview` não dá erro — cai para o motor do IE11 em silêncio**, com um
`logger.warning` que ninguém vê. HTMX e `fetch` quebram e o app "fica
esquisito" na máquina de uma pessoa. E `gui='edgechromium'` **não força**.
Por isso o E5 existe: o app checa antes de abrir a janela e **recusa**.

O spike cobriu **1 de 4 perguntas**. PyInstaller, SmartScreen e credencial
por CLI no Windows estão marcados como **não perguntados**, não como "sem
achados" — a diferença importa.

### As provas são do maestro, não dos executores

`orquestracao/provas/` — sete scripts, escritos **antes** do despacho. Todo
briefing diz: não edite a prova para fazê-la passar; se ela parecer errada,
escreva no relatório.

Isso pegou coisa duas vezes. A melhor: a primeira versão da prova do D3
passava **de graça** — verificava que o `runner` não quebrava com o hub
morto, e um runner que não reporta também não quebra. Endurecida para exigir
que o hub **receba** a execução.

## 5.5 A bancada de orquestração

    orquestracao/
      PLANO.md            o que este bloco se propôs, e o que NÃO ia fazer
      fila.jsonl          os itens, com escopo e prova
      estado.json         as 4 vagas
      despachos.jsonl     um registro por despacho encerrado
      briefings/T-NN.md   o que foi mandado, exatamente
      logs/T-NN.log       stdout cru do executor
      roteiros/           ciclo-dia3.md, o roteiro de prova do Dia 3
      spikes/             credenciais.md (4 CLIs medidos)
      JOURNAL.md          o porquê de cada decisão

A CLI:

    .venv/bin/python bin/esteira-maestro doctor    # smoke por runtime E por conta
    .venv/bin/python bin/esteira-maestro fila list
    .venv/bin/python bin/esteira-maestro slots
    .venv/bin/python bin/esteira-maestro dispatch --task T-NN --vaga N
    .venv/bin/python bin/esteira-maestro colher
    .venv/bin/python bin/esteira-maestro tick

Códigos de saída: `0` ok · `1` falha · `2` uso inválido · `70` escalada.
`--json` em tudo que lista.

**Como despachar sem se enganar.** O briefing é arquivo em
`orquestracao/briefings/T-NN.md`, com sete partes: objetivo em uma frase,
caminhos absolutos, escopo, o que NÃO tocar, prova exigida, relatório,
detalhes. Sem "prova exigida" e "relatório" você recebe entrega e não sabe
o que foi conferido — já aconteceu.

**Dois escopos ativos nunca se cruzam.** O `dispatch` recusa. Não é boa
prática: é a única coisa que impede dois executores de se sobrescreverem
sem ninguém notar.

**O veredito é o disco, e depois a prova.** O `colher` classifica
FEITO/REFAZER/ESCALAR só olhando se o disco mexeu dentro do escopo. Ele
**não** roda a prova — isso é seu. Item colhido vai para `a_provar`, não
para `feito`.

## 6. Armadilhas que vão morder

### `.env` não é lido por código nenhum

É para `EnvironmentFile=` do `systemd`. Na mão: `set -a; . ./.env; set +a`.
Por isso todo valor com espaço está **entre aspas** — sem aspas o systemd
aceita e o bash não, e você perde meia hora achando que o CLI quebrou.

### `systemd` não vai achar `codex` nem `opencode` — leia antes do Dia 3

Os dois vivem em `~/.nvm/versions/node/v24.18.0/bin/`, que entra no `PATH`
pelo `nvm.sh` carregado no `.bashrc` (linhas 119-121). Serviço do
`systemd` não roda `.bashrc`. Num shell sem nvm, só `claude` e `agy` são
encontrados.

Ou o unit define o `PATH`, ou o `.env` usa caminho absoluto:

    CMD_CODEX="/home/nicolas/.nvm/versions/node/v24.18.0/bin/codex exec -s workspace-write --skip-git-repo-check"
    CMD_OPENCODE="/home/nicolas/.nvm/versions/node/v24.18.0/bin/opencode run --auto -m opencode/hy3-free"

Cuidado: esse caminho tem a versão do node dentro. Atualizar o node
quebra. Preferir `PATH` no unit.

### Não faça `append` cego no `~/.codex/config.toml`

O codex **escreve nesse arquivo sozinho**: quando roda numa pasta nova,
ele acrescenta `[projects."<caminho>"] trust_level = "trusted"`. Se você
já tiver acrescentado a mesma pasta na mão, vira chave duplicada e o
codex **para de subir inteiro**:

    Error loading config.toml:
    /home/nicolas/.codex/config.toml:55:11: duplicate key

Aconteceu aqui: `codex` passou a falhar com `codigo=1` em 0s, e parecia
problema da esteira. Não era. Antes de editar esse arquivo, confira:

    grep -n '^\[projects\.' ~/.codex/config.toml | sort -k2 | uniq -df1

Detalhe que ajuda: o `CODEX_HOME` isolado da esteira
(`~/.esteira-auth/nicolas/codex`) tem o **próprio** `config.toml` e se
auto-registra. Na maioria dos casos não é preciso mexer no do host.

### A flag que recebe o prompt tem que ser a última

Vale para todo runtime com `stdin_prompt: False` — hoje só o `agy`. O
runner anexa o prompt no **fim** do `argv`. Se houver outra flag depois
da que recebe o prompt, é essa flag que vira o prompt:

    agy -p --dangerously-skip-permissions      ✗  -p engole a flag
    agy --dangerously-skip-permissions -p      ✓

O agy avisa. Nem todo CLI avisa.

### O n8n guarda um pouco de estado — de propósito, e com rede de segurança

O `n8n/README.md` diz que "o n8n não guarda estado". O F1 guarda: uma
Data Table `esteira_comms` com a correlação entre o `Message-ID` que o
Outlook gerou e o `reply_to` lógico. Sem isso o casamento por
`In-Reply-To` é impossível — o próprio README pede esse caminho, e ele
exige lembrar o que foi enviado.

O que **não** pode acontecer é a tabela virar ponto único de falha. Por
isso o caminho 3 (regex no assunto) **reconstrói** o `reply_to` quando
não acha linha na tabela:

    [esteira #1001-2]  →  {WORKER_BASE}/answer/1001/1001-2

Mesmo formato do `comm.envelope`. Perder o banco do n8n degrada o
casamento, não orfana pergunta.

Se um dia mexer nisso, teste os cinco caminhos, não só o feliz:
`In-Reply-To`, `conversationId`, assunto **com** tabela, assunto **sem**
tabela, e nada casando.

### Id de modelo *free* é validade, não configuração

`deepseek-v4-flash-free`, o padrão do `~/.config/opencode/opencode.jsonc`,
**saiu do ar**. Hoje o `.env` usa `hy3-free`. Antes de investigar qualquer
coisa no `opencode`:

    opencode models | grep -- -free

Sintoma típico: sub-task volta em poucos segundos sem tocar o disco, duas
vezes seguidas. É ajuste de `.env`, nunca de código.

### A prosa do agente não é o veredito

Aconteceu de verdade no Dia 0: o relatório do worker do AMPLIA dizia que
os testes do *backend* **não rodaram** (sem rede para o vocabulário do
`tiktoken`). Na minha execução, **822 passaram**. Os dois estavam certos —
o sandbox do codex não tem rede, o shell tem. Se eu tivesse acreditado no
relatório, teria concluído que o gate não funciona.

Regra: rode o `check.sh` você mesmo. É o que o `runner.py` prega.

### O sandbox do codex não tem rede nem soquete local

`-s workspace-write` bloqueia os dois. O worker do template não conseguiu
`curl localhost` nem comitar — provou pelo cliente WSGI e deixou a prova
pela porta e o commit para quem o chamou. Não é falha do worker; é o
sandbox. Planeje a prova final do lado de fora.

---

## 7. Como delegar — o que funciona

### Funciona: `runner.rodar`, o primitivo da própria esteira

É o mesmo que o `bin/esteira-delegate` usa. Dois codex em paralelo no
Dia 0, 796s e 409s, ambos `codigo=0`.

    cd ~/Área\ de\ trabalho/esteira
    set -a; . ./.env; set +a
    .venv/bin/python - <<'PY'
    import sys, pathlib
    sys.path.insert(0, '.')
    from esteira import runner, contas
    prompt = pathlib.Path('/tmp/briefing.md').read_text(encoding='utf-8')
    conta = contas.escolher('codex')
    r = runner.rodar('codex', prompt,
                     cwd='/caminho/do/repo',
                     log_path='/tmp/tarefa.log',
                     timeout_s=2700, conta=conta)
    print(r, conta['chave'])
    PY

O que faz o briefing funcionar: caminhos absolutos, dizer o que **não**
tocar, e exigir prova rodada (`check.sh` com a saída colada) mais um
`RELATORIO-DIA0.md` no fim. Sem isso o agente entrega e você não sabe o
que ele conferiu.

### Não funciona: `orca orchestration worker-start --agent codex`

Tentado, falhou em três degraus:

1. `--repo` e `--display-name` são recusados com `--worktree current`;
2. `Agent startup blocked: codex-interactive-prompt` — resolvido com
   `orca agent hooks prepare-codex` e `trust_level = "trusted"` para as
   pastas novas em `~/.codex/config.toml` (*backup* em
   `config.toml.pre-esteira`);
3. mesmo assim `agent_prompt_stalled`: o Orca abriu um terminal e digitou
   o briefing inteiro **no bash**, linha por linha, em vez de dentro do
   codex. Confirmado depois pela fila: as mensagens que chegaram eram o
   bash chamando `worker-done` com os *placeholders* do preâmbulo
   (`<3-sentence summary…>`, `path/a`) literais.

Nada sujou. Mas vale como sinal: **`CMD_ORCA` vazio no `config.py` está
certo**, e agora isso está medido, não suposto. Orca como IDE, `runner`
como runtime.

Se sobrou lixo de dispatch na fila:

    orca orchestration check --run <run_id> --peek --json     # ver
    orca orchestration check --run <run_id> --ack <delivery>  # limpar

O `run_78b8f795e3d9` do Dia 0 ficou com três dispatches mortos como
registro contábil (`retained`/`reclaimable`), terminais fechados. São
inertes.

---

## 8. O que NÃO fazer

Do `BUILD.md`, e vale repetir porque é a parte que se esquece:

> Todo ajuste vai no `AGENTS.md`, no `PADROES.md` e no `armadilhas.md` —
> não no código. Se você estiver mexendo no worker no dia 8, algo está
> errado.

Duas exceções aconteceram no Dia 0 e Dia 1, ambas conserto de defeito em
código já existente, nenhuma comportamento novo:

- `esteira/runner.py` passou a **respeitar** `stdin_prompt`, que o
  `config.py` já declarava e ninguém lia. Sem isso o tier `agy` não roda.
- `scripts/check_ds.sh` teve a regra de itálico corrigida. Ela reprovava
  o texto **corretamente** italicizado, o que tornava o gate impossível de
  passar em qualquer página que citasse uma das 13 palavras.

Se aparecer vontade de mexer no worker, releia isto primeiro.

E a lista do `BUILD.md` continua valendo: nada de roteamento de modelo com
aprendizado, DAG de agentes, registry em banco, *message broker*,
Temporal, Vault, RAG, teto em dólar, e **nunca** merge automático.
