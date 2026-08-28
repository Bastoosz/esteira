# Relatório de construção da esteira

Registro do que **mudou de fato**, por dia, com a prova que sustenta cada
linha. Ordem cronológica de execução, não a ordem do `BUILD.md`.

Regra deste arquivo: nada entra aqui sem ter sido rodado. Se não foi
provado nesta máquina, aparece marcado como **não provado**.

---

## Dia 1 — fundação · 2026-08-28 · FECHADO

Os quatro itens do `BUILD.md` Dia 1 estão verdes.

### Mudanças

| arquivo | mudança |
|---|---|
| `esteira/runner.py` | passa a respeitar `stdin_prompt`, que `config.py` já declarava e ninguém lia |
| `config.py` | `RUNTIMES` com os comandos que de fato funcionam; `agy` com `stdin_prompt: False` |
| `.env` / `.env.example` | comandos conferidos, valores entre aspas |
| `contas.yaml` | pessoa real (`nicolas`); placeholders inativos |
| `README.md` | seção "Estado real desta máquina"; preço da credencial copiada |
| `AGENTS.md` | sintoma do modelo *free* morto e o que o agente faz com ele |
| `PADROES.md` | id de modelo *free* é validade, não configuração |

Repo: `AndradeMaia-Tech/esteira`, privado, `main` empurrado.

### O que estava quebrado

**`codex` não existia.** `npm i -g` tinha morrido no meio: pacote no lugar,
dependência nativa `@openai/codex-linux-x64` faltando, e no lugar do link
`codex` um `.codex-KEfGGw34` de instalação interrompida. `command -v codex`
não achava nada. `npm install -g @openai/codex@latest` resolveu →
`codex-cli 0.150.1`.

**`CMD_LEAD` nunca teria rodado.** Faltava `--verbose`:

    Error: When using --print, --output-format=stream-json requires --verbose

Era o primeiro comando do primeiro item do Dia 1. Falhava em 3s.

**`agy` não lê prompt de `stdin`.** Quer o prompt como valor de `-p`; com
`stdin` sai com 2 e imprime o *usage*. `config.py` declarava
`stdin_prompt` por runtime e o `runner.py` nunca lia o campo.

**`agy` também responde sem tocar o disco.** Sem
`--dangerously-skip-permissions` ele auto-nega a permissão `command` em
modo *headless*: sai com 0, imprime resposta, não escreve nada. Mensagem
dele:

    jetski: no output produced — a tool required the "command" permission
    that headless mode cannot prompt for, so it was auto-denied.

**O modelo *free* do OpenCode saiu do ar.** `deepseek-v4-flash-free`, o
padrão do `~/.config/opencode/opencode.jsonc`, não existe mais.
`hy3-free` e `mimo-v2.5-free` provados escrevendo em disco.

**`.env` não é lido por código nenhum.** É para `EnvironmentFile=` do
`systemd`. E os valores do `.env.example` vinham sem aspas — `. ./.env`
no bash rodava `-p` como comando.

### Provas

    lead      OK  codigo=0  claude 2.1.250
    codex     OK  codigo=0  codex-cli 0.150.1, modelo gpt-5.4
    opencode  OK  codigo=0  hy3-free, escreveu prova.txt
    agy       OK  codigo=0  responde; escrita em disco NÃO PROVADA
    orca      VAZIO (proposital)

Contas com auth isolada:

    lead   conta=nicolas:claude   OK codigo=0
    codex  conta=nicolas:codex    OK codigo=0

Isolamento medido: o mesmo *smoke* roda **12** hooks com `CODEX_HOME` do
host e **zero** com o diretório da esteira.

### Dívidas que o Dia 1 deixou

1. **`agy --dangerously-skip-permissions` não foi provado.** O sandbox da
   sessão de construção bloqueou rodar a flag. É a única linha do Dia 1
   sem prova. Comando para fechar isso está no `README.md`.
2. **Credencial copiada, não logada.** A cópia é um retrato: quando o CLI
   do dia a dia renova o token, ela não renova — vence em silêncio e a
   demanda quebra no meio. A defesa é o `smoke_todas()` de hora em hora
   do Dia 6. Até lá é dívida.
3. **`n8n` não está instalado.** Bloqueia o Dia 2 inteiro.

---

## Dia 0 — template e projeto real · 2026-08-28 · FECHADO

### O achado que muda o item 1 do `BUILD.md`

O `BUILD.md` supõe um DS empacotado, com `tokens/`, `styles.css`,
`assets/` e um `.jsx` + `.prompt.md` por componente, num *zip* de 64 MB.

**Esse pacote não existe nesta máquina.** Não há nenhum `.prompt.md`,
nenhum `_adherence.oxlintrc.json` (que o próprio `check_ds.sh` cita) e
nenhum *zip* do DS.

O que existe é o DS **em uso**, dentro de um produto:

    Projeto Disney/Jornada-Do-Cliente/o-jeito-am/
      src/app/globals.css       4233 linhas — o :root com os 72 tokens
      src/app/am-identity.css   3520 linhas — a camada institucional
      public/fonts/sansation/   6 pesos
      public/brand/             PNGs da marca

Consequência prática: o Dia 0 deixa de ser "copiar pasta" e passa a ser
**extrair um pacote de DS de dentro de um app Next.js**, separando o que
é institucional do que é do produto.

### O conflito de tokens — decisão tomada

Os tokens do `base.html` da esteira **não são** os do DS AM:

| | `base.html` da esteira | DS AM real |
|---|---|---|
| tema | claro (`#f4f4f4`, texto preto) | **escuro** (`#000`, texto branco) |
| cantos | `--radius: 2px` | `--radius: 0px` + `--chamfer: 18px` (45°) |
| nomes | `--am-gray-050`, `--space-1..7` | `--ink-1..5`, `--bg-elev-1..4`, sem `--space-*` |

O `BUILD.md` diz que "os tokens atravessam sem mudança". Então o DS real é
o canônico e o `base.html` da esteira é que está fora do padrão — ele foi
escrito contra um conjunto de tokens inventado.

**Decisão:** o template carrega os tokens reais (escuro, chanfrado). O
`base.html` do board da esteira fica divergente por enquanto e entra como
dívida — não é item do Dia 0 e mexer nele agora não entrega nada.

### O que o DS real não tem

Não existe escala de espaçamento (`--space-*`), embora a mensagem de erro
do `check_ds.sh` mande usar `var(--space-*)`. O template cria a escala em
`static/ds/tokens/espacamento.css`, marcada como adição do template. A
pasta `/tokens/` é ignorada pelo `check_ds.sh`, então `px` cru ali é
legítimo.

### Bug encontrado na própria extração — `--font-montserrat`

Auditando o `tokens.css` que eu extraí, um token ficou **órfão**:

    --font-display:   var(--font-montserrat), "Montserrat", "Segoe UI", sans-serif;
    --font-condensed: var(--font-montserrat), "Montserrat", "Segoe UI", sans-serif;

`--font-montserrat` não é definido em CSS nenhum: quem injeta é o
`next/font`, em `o-jeito-am/src/app/layout.tsx`. Fora do Next ele não
existe.

Por que isso importa: `var()` sem *fallback* apontando para variável
inexistente torna a declaração **inválida no tempo de computação**. Não é
"cai para o próximo da lista" — é `font-family` virar `unset`. Resultado:
**todo título perderia a Montserrat, em silêncio**, e nem o `check_ds.sh`
nem o `check.sh` pegariam, porque a sintaxe está correta.

É exatamente o modo de falha que o `PADROES.md` chama de invalidador de
V1: "layout fora do design system" passando por todos os testes.

Correção mínima, na camada do template (o `tokens.css` fica intocado
porque é canônico):

    :root { --font-montserrat: "Montserrat"; }

Aí a cadeia resolve e a Montserrat aparece se estiver disponível.

**Pendência separada:** Montserrat não existe nesta máquina —
`fc-list | grep -i montserrat` volta vazio e não há `.ttf`/`.woff2` em
lugar nenhum. A Sansation é auto-hospedada em `assets/fonts/`; a
Montserrat não. Decidir entre auto-hospedar (coerente com a Sansation,
sem dependência externa na renderização) ou `<link>` do Google Fonts.
Até decidir, a cadeia cai em Segoe UI / `sans-serif`.

### Bug bloqueante no `check_ds.sh` — o gate era impossível de passar

A regra de itálico reprovava o texto **corretamente** italicizado:

    <p>Faça o <i>upload</i> do arquivo</p>     →  ✗ estrangeirismo sem itálico

Causa: a regra procurava primeiro e tentava excluir depois —

    grep -nioE ">[^<]*\b(upload|...)\b[^<]*<" "$f" | grep -viE '<(i|em)[ >]'

O casamento é `>…<`, então o fragmento encontrado é `>upload<`, que **nunca
contém** a tag que o envolve. O filtro de exclusão não tinha o que excluir.
Consequência: qualquer página que citasse uma dessas 13 palavras reprovava,
italicizada ou não. O gate era inatingível.

Segundo defeito na mesma regra: o escape `ds-ok` não valia ali. As outras
três regras usam `grep -nE` e passam a linha inteira para o `sem_escape`;
esta usa `grep -o` e passa só o fragmento, onde o comentário de escape
nunca aparece.

Corrigido invertendo a ordem: apaga primeiro o que já está marcado
(`<i>`, `<em>`, `class="foreign"`, linha com `ds-ok`), depois procura. O
`sed` esvazia o conteúdo da linha mas nunca remove a linha, para o número
de linha do `grep` continuar correto.

Provado nos dois sentidos:

    BOM  (i/em/foreign/ds-ok)  → [ds] ok      saída 0
    RUIM (hex, px, Arial, sem itálico) → 5 desvios   saída 1
    esteira inteira            → [ds] ok      saída 0

Isso era bloqueante para o Dia 0 inteiro: os dois entregáveis têm
`check_ds.sh` verde como critério de aceite, e o `BUILD.md` Dia 4 manda
pendurar esse mesmo script no `check.sh` de cada projeto.

### A extração mecânica do DS

Novo repo `template-stack1-flask-htmx` em `/home/nicolas/orca/`:

| caminho | o que é | prova |
|---|---|---|
| `static/ds/tokens/tokens.css` | 72 tokens AM extraídos do `:root` | conferido token a token contra a origem: 72 na origem, 72 no destino, **nenhum faltando** |
| `static/ds/assets/fonts/` | Sansation, 6 `.ttf` | 240 KB |
| `static/ds/assets/logos/` | `am-elements.png` | 304 KB |
| `static/ds/assets/icons/` | 9 PNGs de elemento de marca | 668 KB |

Total do DS extraído: **1,2 MB** — contra os ~4 MB que o `BUILD.md`
estimava, porque o pacote original tinha mais do que os tokens e a marca.

### Como foi executado

Dois `codex` em paralelo, pelo `runner.rodar` da própria esteira
(assinatura `nicolas:codex`), cada um no seu `cwd`:

| tarefa | `cwd` | duração | saída |
|---|---|---|---|
| template | `orca/template-stack1-flask-htmx` | 796s | `codigo=0` |
| `projects/amplia` | `esteira` | 409s | `codigo=0` |

### Entregue: `projects/amplia/` — item 3 do Dia 0

Projeto real escolhido: **AMPLIA** (`orca/AMPLIA.APP_vers-o-2`,
`AndradeMaia-Tech`) — plataforma de inteligência jurídica do escritório,
*backend* FastAPI na AWS, *frontend* na Vercel. É o único repo AM já
registrado no Orca e tem 8 *worktrees* de trabalho ativo: projeto vivo,
não exemplo.

| arquivo | linhas |
|---|---|
| `AGENTS.md` | 89 (teto 150) |
| `check.sh` | 98, executável |
| `context/dominio.md` | 47 |
| `context/decisoes.md` | 35 |
| `context/armadilhas.md` | 35 |

Verificado **por mim**, não pelo relato do agente:

    bash projects/amplia/check.sh /home/nicolas/orca/AMPLIA.APP_vers-o-2
    → 822 passed, 19 skipped, 38 xfailed em 101s     saída 0
    bash scripts/check_ds.sh projects/amplia         → [ds] ok, saída 0

O AMPLIA ficou intacto: nada com `mtime` posterior ao início do worker. As
duas mudanças que aparecem no `git status` dele são de 2026-08-14,
pré-existentes.

O `armadilhas.md` só tem armadilha comprovada lendo o repo — inclusive
duas que valem ouro: o `tiktoken` baixa o vocabulário na coleta dos
testes, e as métricas de requisição do ALB ficam zeradas porque o tráfego
entra por Cloudflare Tunnel. Duas marcações `REGRA-JURIDICA` onde o agente
se recusou a escrever contagem de prazo.

#### A prosa do agente e a realidade divergiram — e o `check.sh` acertou nos dois

O relatório do worker diz que os testes do *backend* **não rodaram**: a
coleta exige o vocabulário `cl100k_base` do `tiktoken`, sem cache e sem
rede. Na minha execução, **822 testes passaram**.

Os dois estão certos. O sandbox do codex (`-s workspace-write`) não tem
rede; o meu shell tem. O que importa é que o `check.sh` **degradou
explicitamente** num ambiente e **rodou de verdade** no outro, sem
quebrar em nenhum — que era o pedido.

É a regra do `runner.py` valendo na prática: a prosa do agente não é o
veredito. Se eu tivesse acreditado no relatório, teria concluído que o
gate não roda. Ele roda.

### Entregue: `template-stack1-flask-htmx` — item 1 do Dia 0

Repo com 2 commits. Sem remote ainda.

    static/ds/tokens/tokens.css        72 tokens AM (canônico, não se edita)
    static/ds/tokens/fontes.css        ponte do --font-montserrat
    static/ds/tokens/espacamento.css   --space-1..7 e --largura-max
    static/ds/styles.css               396 linhas, camada institucional
    static/ds/assets/                  Sansation 6 pesos + 10 PNGs de marca
    templates/base.html                liga os 4 CSS na ordem + HTMX 2.0.7
    templates/_partials/               9 macros Jinja
    templates/demo.html                7 seções cobrindo os 9 partials
    app.py 22 linhas · config.py 16 · check.sh · scripts/check_ds.sh
    requirements.txt · .env.example · README.md · RELATORIO-DIA0.md

Verificado **por mim**:

    bash scripts/check_ds.sh .   → [ds] ok, saída 0
    bash check.sh                → saída 0 (compileall + import do app + ds)
    app na 5001, demo renderiza:
      am-btn 27 · am-box 20 · am-tag 5 · upload-field 15 · badge 10
      3 <table>, 11 <th> · input 15 · select 9 · checkbox 3
    tokens.css, fontes.css, espacamento.css, styles.css e Sansation → 200
    ordem dos CSS: tokens → fontes → espacamento → styles ✓

O worker traduziu do `am-identity.css` só o genérico e registrou o que
deixou de fora: as classes de produto (`encantometro`, `phase-trail`,
`mural`, `wow-*`, `checklist`, `client-table`, `roadmap`) e três
auxiliares — `.am-num-box`, `.am-seal`, `.am-pattern`. As duas últimas são
elementos de marca; vale reavaliar se entram numa segunda passada.

Ele resolveu a regra de itálico melhor do que eu pedi: em vez de encher a
demo de `<i>`, manteve palavra estrangeira **só em nome técnico** (macro,
classe CSS, `{% import %}`) e escreveu toda a cópia visível em PT-BR — o
que o `PADROES.md` permite explicitamente. Zero escapes `ds-ok`.

Honesto no relatório dele: não conseguiu abrir soquete local nem comitar,
por permissão do sandbox do codex. Provou pelo cliente WSGI (200). A prova
pela porta e o commit fiz eu.

#### Correção que o worker não pegou

`--font-montserrat` continuava órfão. Criado
`static/ds/tokens/fontes.css` definindo-o, carregado logo depois do
`tokens.css` — que fica intocado porque é canônico.

### Dívidas que o Dia 0 deixou

1. **Montserrat não auto-hospedada.** A Sansation está em
   `assets/fonts/`; a Montserrat não, porque o app de origem a pegava do
   Google Fonts em tempo de *build*, e ela não existe nesta máquina
   (`fc-list` vazio). Até decidir entre auto-hospedar ou `<link>`,
   `--font-display` cai em Segoe UI / `sans-serif`.
2. **`base.html` do board da esteira está fora do DS.** Tema claro, nomes
   de token inventados, `--radius: 2px` onde o DS é `0px` + chanfro. O
   template agora é a referência correta; o board é que divergiu.
3. **`template-stack1-flask-htmx` sem remote.** Só git local.
4. **`python-dotenv` no template.** A esteira não usa (carrega `.env` por
   `EnvironmentFile=`); o template usa. Divergência pequena e deliberada
   do worker, mas é uma dependência a mais no molde de todo projeto
   Stack 1.
5. **HTMX por CDN** (`cdn.jsdelivr.net`), como no board. Dependência
   externa no momento de renderizar.
6. **`template-stack2-fastapi` não existe.** O `STACKS.md` promete.

### Nota de orquestração

A primeira tentativa foi por `orca orchestration worker-start --agent
codex`. Não funcionou, em três degraus:

1. `--repo` e `--display-name` são recusados com `--worktree current`;
2. `Agent startup blocked: codex-interactive-prompt` — resolvido com
   `orca agent hooks prepare-codex` e com `trust_level = "trusted"` para
   as duas pastas novas em `~/.codex/config.toml` (*backup* em
   `config.toml.pre-esteira`);
3. mesmo assim, `agent_prompt_stalled`: o Orca abriu um terminal e digitou
   o *briefing* inteiro **no bash**, linha por linha, em vez de dentro do
   codex. O repo não sujou (`git status` limpo), mas o agente nunca subiu.

A confirmação veio depois, pela fila de mensagens: as duas rejeições que
chegaram eram o **bash executando os *placeholders* do preâmbulo** —
`worker-done` chamado com `<3-sentence summary…>` e `path/a`, `path/b`
literais. Orca recusou porque o dispatch já estava encerrado. Fila zerada
com `--ack`.

Troquei para o `runner.rodar` da esteira — que é o primitivo que o
`esteira-delegate` já usa e que foi provado no Dia 1 escrevendo em disco.
Vale como sinal: **o `CMD_ORCA` vazio no `config.py` estava certo.** O
Orca serve como IDE, não como runtime de agente sem humano dirigindo, e
isso agora está medido, não suposto.

