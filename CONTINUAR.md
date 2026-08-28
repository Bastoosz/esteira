# Continuar daqui

Estado em **2026-08-28**. Este arquivo é para retomar; o histórico do que
mudou e por quê está no `RELATORIO.md`.

Ordem de leitura ao voltar: este arquivo → `BUILD.md` → `RELATORIO.md`
só quando precisar do detalhe de algum achado.

---

## 1. Onde está tudo

| o que | caminho | git |
|---|---|---|
| esteira | `~/Área de trabalho/esteira` | `AndradeMaia-Tech/esteira`, privado, `main` empurrado |
| template Stack 1 | `~/orca/template-stack1-flask-htmx` | local, **sem remote** |
| projeto real | `~/orca/AMPLIA.APP_vers-o-2` | `AndradeMaia-Tech/AMPLIA.APP_vers-o-2` (não é nosso; só leitura) |
| DS de origem | `~/Área de trabalho/Projeto Disney/Jornada-Do-Cliente/o-jeito-am` | não é nosso; fonte dos tokens |
| auth da esteira | `~/.esteira-auth/nicolas/{claude,codex}` | fora do git, modo 700 |

Portas: board na **5000**, demo do template na **5001**.

Últimos commits da esteira:

    77ba968 docs: restaura as secoes do Dia 0 que um sed meu apagou
    68fe449 docs: fecha o Dia 0 no relatorio
    f2c1911 Dia 0: projects/amplia real + conserta o gate do design system
    245c8db Dia 1: agy precisa de skip-permissions ou responde sem tocar o disco
    107049e Dia 1: conta nicolas ativa, com auth isolada da do host
    c4df1f6 Dia 1: runtimes conferidos contra os CLIs instalados

---

## 2. Retomar em um minuto

    cd ~/Área\ de\ trabalho/esteira
    set -a; . ./.env; set +a          # NENHUM código lê o .env. Carregue você.
    .venv/bin/python board.py         # http://localhost:5000

Conferir que os quatro runtimes ainda respondem:

    .venv/bin/python -c "import sys;sys.path.insert(0,'.');\
    from esteira import runner;import config;\
    [print(t, runner.smoke_test(t)[0]) for t in ('lead','codex','opencode','agy')]"

Se algum cair, é `.env` ou `config.py` — **não** é o worker. Ver secção 6.

Template:

    cd ~/orca/template-stack1-flask-htmx
    bash check.sh                     # compileall + import + check_ds
    .venv/bin/python app.py           # http://localhost:5001

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

### Dia 2 — BLOQUEADO

- [ ] F1 `esteira-comms-out` no n8n
- [ ] Linha `--- responda acima desta linha ---`
- [ ] F2 `esteira-comms-in`
- [ ] Testar `POST /answer/1001/1001-1` na mão

**Bloqueio: `n8n` não está instalado.** Sem ele, `esteira-ask` e
`esteira-deliver` não têm para onde mandar e-mail.

O item que **dá para fazer já**, sem n8n, é o último: o endpoint
`/answer` existe em `board.py:126` e é testável na mão.

### Dias 3 a 6 — não começados

Ler o `BUILD.md`. Antes do Dia 3, ver a armadilha do `systemd` na
secção 6 — ela vai morder.

---

## 4. Duas decisões esperando você

### 4.1 Montserrat

O `tokens.css` usa `--font-display: var(--font-montserrat), "Montserrat", …`.
No app de origem, `--font-montserrat` era injetada pelo `next/font`. Fora
do Next ela não existe, e `var()` sem *fallback* para variável indefinida
**invalida a declaração inteira** — não cai para o próximo item da lista.
Todo título perderia a Montserrat em silêncio, com os dois gates verdes.

Já mitigado: `static/ds/tokens/fontes.css` define
`--font-montserrat: "Montserrat"`. Falta escolher de onde vem a fonte:

| opção | a favor | contra |
|---|---|---|
| auto-hospedar | coerente com a Sansation, que já está em `assets/fonts/`; nada de rede ao renderizar | precisa baixar e versionar ~6 arquivos |
| `<link>` do Google Fonts | uma linha | dependência externa em toda renderização |

Enquanto não decidir, a cadeia cai em Segoe UI / `sans-serif`. A
Montserrat não existe nesta máquina: `fc-list | grep -i montserrat` volta
vazio.

### 4.2 Remote do template

`~/orca/template-stack1-flask-htmx` só tem git local. O `STACKS.md`
manda **clonar** o template — sem remote, ninguém clona. Proposta:

    cd ~/orca/template-stack1-flask-htmx
    gh repo create AndradeMaia-Tech/template-stack1-flask-htmx \
      --private --source=. --remote=origin --push

---

## 5. Dívidas, em ordem de dor

1. **`agy --dangerously-skip-permissions` não foi provado.** Única linha
   do Dia 1 sem prova: o sandbox da sessão de construção bloqueou rodar a
   flag. Sem ela o agy responde, sai 0 e **não escreve nada** — auto-nega
   a permissão `command` em modo *headless*. Feche assim:

       cd ~/Área\ de\ trabalho/esteira
       set -a; . ./.env; set +a
       .venv/bin/python -c "import sys;sys.path.insert(0,'.');\
       from esteira import runner;print(runner.smoke_test('agy'))"

2. **Credencial copiada, não logada.** `~/.esteira-auth/nicolas/` foi
   semeado copiando `~/.claude/.credentials.json` e `~/.codex/auth.json`.
   A cópia é um retrato: quando o CLI do dia a dia renova o token, ela
   **não** renova — vence em silêncio e a demanda quebra no meio, não na
   largada. Duas defesas, nesta ordem: subir o `smoke_todas()` de hora em
   hora (Dia 6), e quando vencer fazer login de verdade dentro do
   diretório em vez de copiar outra vez:

       CLAUDE_CONFIG_DIR=~/.esteira-auth/nicolas/claude claude
       CODEX_HOME=~/.esteira-auth/nicolas/codex codex

3. **`base.html` do board está fora do DS.** Tema claro, `--radius: 2px`,
   nomes de token inventados (`--am-gray-050`, `--space-*`). O DS real é
   preto, `--radius: 0px` + chanfro 45°, `--ink-1..5`. O template agora é
   a referência correta; o board é que divergiu. Não é urgente — o board
   é ferramenta interna — mas é incoerente pregar aderência ao DS num
   arquivo que não adere.
4. **`n8n` não instalado.** Bloqueia o Dia 2 inteiro.
5. **`python-dotenv` no template.** A esteira carrega `.env` por
   `EnvironmentFile=`; o template usa `load_dotenv()`. Divergência
   pequena, mas é uma dependência a mais no molde de todo projeto Stack 1.
6. **HTMX por CDN** no template e no board (`cdn.jsdelivr.net`,
   `unpkg.com`). Dependência externa no momento de renderizar.
7. **`.am-seal` e `.am-pattern` ficaram fora do `styles.css`.** São
   elementos de marca; o worker os classificou como auxiliares. Vale
   reavaliar numa segunda passada.
8. **`template-stack2-fastapi` não existe.** O `STACKS.md` promete.

---

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
