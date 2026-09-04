# Journal da orquestração

O que os comandos não registram: o motivo.

## 2026-09-02 — primeiro bloco

- `15:25` **Reconhecimento antes de escrever.** `git log`, `git status`, as
  pastas, os `CMD_` do `.env`, e os contratos (`CONTINUAR.md`, `BUILD.md`,
  `PADROES.md`, `ESTRUTURA.md`, `papeis/orquestrador.md`).
  — **por quê:** terreno com ferramenta, não com modelo. Três achados
  saíram daí e mudaram o plano; nenhum deles apareceria lendo só os
  documentos.

- `15:27` **`doctor` reprovou 2 de 4.** `codex` código 127, `opencode`
  código 1.
  — **por quê:** o `BUILD.md` manda conferir os runtimes antes de qualquer
  coisa, e o `CONTINUAR.md` diz que runtime caído é `.env`/`config.py`, não
  worker. Despachar com dois tiers mortos teria produzido duas voltas
  vazias e eu culparia a tarefa.

- `15:28` **`codex`: o *symlink* tinha desaparecido.** Pacote e dependência
  nativa no lugar; o link `bin/codex`, não. Recriar o link não bastou — o
  *loader* procura `@openai/codex/vendor/<triple>/bin/codex` e o binário
  estava sob `node_modules/@openai/codex-linux-x64/vendor/...`.
  `npm install -g @openai/codex@latest` → **0.152.1** (era 0.150.1).
  — **por quê:** segunda vez que este CLI se apaga sozinho nesta máquina.
  Vira primeira suspeita, não terceira.

- `15:29` **`opencode`: `hy3-free` saiu do ar** entre 28/08 e hoje.
  Testei os **5** *free* existentes **com prova de disco**, não de texto:
  todos os 5 escreveram o arquivo. Passei o `.env` para `mimo-v2.5-free` e
  registrei os outros quatro como reserva, na ordem em que passaram.
  — **por quê:** a armadilha do `PADROES.md` valendo pela segunda vez em
  cinco dias. Trocar por um só resolveria hoje; a lista de reserva resolve
  a próxima vez, que vai acontecer.

- `15:30` **A 1001 é *fixture*, não execução.** Os dois registros de
  `execucoes.jsonl` têm o mesmo *timestamp* da criação, `runs/` está vazio
  e o journal salta `NOVA -> EM_REVISAO`. E ela está em `EM_REVISAO`, que
  `proxima_da_fila()` não pega.
  — **por quê:** o Dia 3 do `BUILD.md` pede "roda a 1001 de verdade". Se eu
  tivesse forçado a 1001 para `PRONTA`, teria destruído a única referência
  de formato do repo e a prova não seria reproduzível. Criar a 1002 satisfaz
  o que o item quer — o ciclo fechando — e deixa a 1001 intacta.

- `15:30` **O worker comita o repo inteiro.** `worker.py::commit()` roda
  `git add -A` + `commit` + `push` na `BASE_DIR` a cada rodada.
  — **por quê:** isso serializa parte do trabalho. Executor escrevendo no
  repo quando o worker fecha uma rodada tem o trabalho comitado pela
  metade. Não é defeito ("git é a verdade" é o desenho), mas ninguém tinha
  escrito a consequência. Por isso o A1 virou dois itens: preparação
  delegável e paralela (T-01), execução do worker minha e serializada
  (T-06).

- `15:35` **`esteira-maestro` escrito por mim, não delegado.**
  — **por quê:** é o contrato — códigos de saída, `--json`, idempotência do
  `tick`. Contrato não se delega. As duas peças difíceis já existiam
  (`runner.rodar` e a foto do disco) e não foram reescritas.

- `15:37` **Corrida no meu próprio código, achada e consertada antes de
  usar.** Quatro `dispatch` em processos separados mexem no mesmo
  `estado.json`. Sem lock, dois leem o mesmo estado, cada um reserva a vaga
  que acha livre, e um sobrescreve o outro. Adicionei um `trava` reentrante
  com `fcntl.flock` em volta de todo read-modify-write.
  Provado com 4 disputando a vaga 3: **um ganhou, três recusaram.**
  — **por quê:** é exatamente a perda que ninguém nota até faltar um
  despacho no fim do dia. Provar com 4 em paralelo custa 10 segundos.

- `15:38` **4 vagas despachadas, escopos disjuntos.**
  T-01 `demands/1002/**` (codex) · T-02 `esteira/sentinela.py,bin/esteira-smoke`
  (codex) · T-03 `deploy/**` (opencode) · T-04 `orquestracao/spikes/**` (agy).
  — **por quê:** nenhum par de escopos se cruza. Não é boa prática, é a
  única coisa que impede dois executores de se sobrescreverem sem ninguém
  notar.

- `15:38` **B1 reenquadrado.** O item pedia medir credencial em máquina
  Windows. **Não há máquina Windows aqui.** O briefing do T-04 passou a
  pedir: medir os 4 CLIs **nesta** máquina, com comando e saída colados, e
  escrever o roteiro Windows como pendência — com a instrução explícita de
  **não inventar resultado de medição**.
  — **por quê:** spike que inventa medição é pior que spike não feito,
  porque o B2 seria desenhado sobre chute.

- `15:42` **Faltou visibilidade, não orquestração.** Narrei "despachado"
  sem mostrar processo vivo nem disco. Subi um vigia de progresso.
  — **por quê:** de fora, "despachei 4" e "não despachei nada" são
  indistinguíveis. A prova tem que ser visível sem me perguntar.
- `2026-09-02T15:43:19` `T-03` voltou de opencode — código 0, 5 arquivo(s) mudado(s), 285s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T15:43:22` `T-01` voltou de codex — código 0, 5 arquivo(s) mudado(s), 293s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T15:44:13` `T-01` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo; rode a prova
- `2026-09-02T15:44:13` `T-03` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo; rode a prova
- `2026-09-02T15:46:28` `T-01` **FEITO** — **por quê:** prova rodada por mim: estado=PRONTA e proxima_da_fila=1002; roteiro ciclo-dia3.md existe (5.9K); pedido pequeno e real, com esteira-ask no meio de proposito
- `2026-09-02T15:46:28` `T-03` **FEITO** — **por quê:** prova rodada por mim: 4 units saem 0 no systemd-analyze verify, PATH com o bin do nvm declarado no unit, Restart=always no worker e vigia. CONSERTEI: ExecStart apontava para symlink fora do repo; troquei por caminho citado, provado com systemd-run
- `2026-09-02T15:46:28` `T-04` **FEITO** — **por quê:** prova rodada por mim: 348 linhas, 4 CLIs medidos com comando+saida, inferencias marcadas como inferencia, secao Windows como roteiro e nao como medicao
- `2026-09-02T15:46:28` fila += T-09, T-10, T-11, T-12 — **por quê:** tres vagas livres e nenhum item de vaga pronto. Encher a fila e a tarefa, nao abrir a quinta vaga
- `2026-09-02T15:48:15` `T-12` voltou de agy — código 1, 0 arquivo(s) mudado(s), 28s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T15:48:20` `T-02` voltou de codex — código 0, 2 arquivo(s) mudado(s), 589s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T15:48:38` `T-11` voltou de opencode — código 0, 1 arquivo(s) mudado(s), 53s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T15:49:16` `T-02` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo; rode a prova
- `2026-09-02T15:49:16` `T-11` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo; rode a prova
- `2026-09-02T15:49:16` `T-12` colhido: **REFAZER** — **por quê:** nada mudou no disco — suspeite do ambiente antes da tarefa: modelo free fora do ar, credencial vencida, CLI sem link
- `2026-09-02T15:51:02` cooldown de `nicolas:codex` limpo à mão — **por quê:** o log do smoke provou que a causa era 'Read-only file system' do sandbox do subagente de revisao, nao a conta. T-01 e T-02 rodaram com essa conta e sairam 0. Contornar cooldown de causa DESCONHECIDA seria errado; de causa provada e falsa, e conserto
- `2026-09-02T15:53:03` `T-02` **FEITO** — e provou valor na primeira execução — **por quê:** a sentinela detectou que a credencial COPIADA de nicolas:claude expirou. Era a defesa numero 1 prevista no README para essa divida exata, e mordeu no primeiro tiro
- `2026-09-02T15:53:03` `T-11` **FEITO** — **por quê:** template do board renderizando e aderente ao design system
- `2026-09-02T15:53:03` `T-12` **BLOQUEADA** e a vaga 4 fora do ar — **por quê:** 'Individual quota reached ... Resets in 137h26m13s'. O T-04 (348 linhas) foi o ultimo trabalho do agy e consumiu o que restava. A bancada tem 3 vagas uteis, nao 4, ate ~08/09
- `2026-09-02T15:53:03` `doctor` consertado: passa a testar POR CONTA, nao so sem conta — **por quê:** ponto cego medido: sem conta ele usa o ~/.claude do host, que esta valido, e imprime 'lead OK' enquanto a credencial da esteira esta com OAuth expirado. Doctor que diz OK com a conta de producao morta e pior que doctor nenhum
- `2026-09-02T15:53:03` `foto()` e `fora_do_escopo()` consertados — **por quê:** o oraculo era cego para escrita FORA do repo: o opencode criou ~/bin/esteira-venv-python numa tarefa de escopo deploy/** e nada acusou. Agora glob absoluto funciona e caminho fora da raiz e sempre violacao. O docstring passou a dizer o que o oraculo NAO ve
- `2026-09-02T15:54:54` `T-05` **FEITO** — **por quê:** o contrato era meu e nao se delega; as duas pecas difíceis (runner.rodar e a foto do disco) ja existiam e nao foram reescritas
- `2026-09-02T15:54:54` `T-08` **FEITO**, com o escopo corrigido — **por quê:** eu tinha posto projects/_exemplo/context/armadilhas.md no escopo. Errado: aquele arquivo e o MOLDE que todo projeto copia, e as armadilhas de hoje sao de infraestrutura, nao de projeto. Escrever nele poluiria todo projeto futuro. Foi para README.md e PADROES.md
- `2026-09-02T15:54:54` fila += `T-13` — **por quê:** template sem rota e meia entrega; o T-11 fica pendurado sem isso
- `2026-09-02T15:57:42` `T-10` voltou de codex — código 0, 1 arquivo(s) mudado(s), 269s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T15:57:46` `T-09` voltou de codex — código 0, 3 arquivo(s) mudado(s), 276s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T15:57:48` `T-13` voltou de opencode — código 0, 1 arquivo(s) mudado(s), 150s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T15:58:17` `T-09` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo; rode a prova
- `2026-09-02T15:58:17` `T-10` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo; rode a prova
- `2026-09-02T15:58:17` `T-13` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo; rode a prova
- `2026-09-02T16:00:20` `T-09`, `T-10`, `T-13` **FEITOS** — **por quê:** refs/n8n deixa de estar vazia — era o item que o proprio refs/README chamava de maior retorno do repo; o maestro passa a ter teste; e o board mostra a bancada
- `2026-09-02T16:00:20` ERRO MEU: comitei trabalho em voo num commit de documentação — **por quê:** o commit be85ff9 diz 'docs: CONTINUAR.md' e carregou board.py, refs/n8n/* e tests/test_maestro.py — trabalho de tres executores que ainda estavam escrevendo. Meu 'git add -A' varreu tudo. E a MESMA armadilha do worker.commit() que eu havia documentado 20 minutos antes, e eu cai nela. Regra nova: nao comitar com vaga em voo, ou comitar caminho especifico. Nao reescrevo historico ja empurrado
- `2026-09-02T16:00:20` briefing meu estava errado: afirmei que pytest estava no venv — **por quê:** nao estava. requirements.txt tinha flask, pyyaml e requests. O projects/_exemplo/check.sh ja chamava pytest, entao a esteira esperava a dependencia sem declarar. Instalei e declarei. Licao: 'a ferramenta X ja esta la' e afirmacao que precisa de prova, igual a qualquer outra
- `2026-09-02T20:22:52` revisão adversarial do maestro: 56 achados, 18 de gravidade alta — **por quê:** o workflow devolveu 'confirmados: []', mas 112 dos 117 agentes morreram no limite de sessao — o vazio era dos refutadores que nao rodaram, NAO 'nada encontrado'. Li o journal.jsonl e triei eu mesmo. Descartar 591k tokens por causa de um resultado enganoso teria sido o erro
- `2026-09-02T20:22:52` o pior achado desmontou um conserto que eu achava feito — **por quê:** fora_do_escopo(mudou, escopo) era ESTRUTURALMENTE VAZIO: `mudou` saía de foto(escopo), entao todo caminho nele ja casava com o escopo por construcao. A protecao nunca disparou — foi assim que o residuo em ~/bin passou. Meu conserto anterior (aceitar glob absoluto) era cosmetico: a funcao continuava sem receber violacao nenhuma. Agora dispatch tira duas fotos, a do escopo e a do repo inteiro, e compara
- `2026-09-02T20:22:52` colher() prometia rodar a prova e nunca rodou; prereq exigia estado que ninguem escrevia — **por quê:** dois defeitos que se somavam: o docstring dizia 'roda a prova' e o corpo nunca lia it['prova']; e prereq_ok exigia estado 'feito' que nenhum codigo gravava, entao toda cadeia de dependencia morria calada. Agora existe `esteira-maestro provar`, que roda a prova declarada e e o UNICO caminho para feito. Provado: prova que sai 0 fecha, que sai 3 devolve para pronta, e o dependente so anda depois
- `2026-09-02T20:23:28` mensagem do commit 290194d perdeu 4 trechos entre crases — **por quê:** o bash tratou o conteudo das crases como substituicao de comando dentro do heredoc do git commit -m. Nao reescrevi o historico: ja estava empurrado e eu tinha acabado de escrever que nao reescrevo historico empurrado. Daqui em diante: git commit -F arquivo
- `2026-09-02T20:43:07` fila += D1, D2, D3, D4, E1, I1, F1, G1 — escopo Esteira Desktop — **por quê:** cada prova e COMANDO executavel, nao prosa. O `provar` agora roda de verdade e e o unico caminho para feito; prova em prosa nao fecha item nenhum
- `2026-09-02T20:43:45` D2 fundido em D1 — **por quê:** D2 (endpoints) tinha escopo esteira/hub/api.py, que cruza com esteira/hub/** do D1 e dependia dele. Item que nunca seria despachado sozinho e contabilidade falsa: vira um so, com escopo esteira/hub/**,board.py
- `2026-09-02T20:48:59` `I1` voltou de opencode — código 0, 1 arquivo(s) mudado(s), 200s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T20:53:10` `I1` colhido: **ESCALAR** — **por quê:** tocou fora do escopo: ['orquestracao/estado.json', 'orquestracao/logs/D1.log', 'orquestracao/logs/E1.log', 'orquestracao/logs/I1.log']
- `2026-09-02T20:53:31` `D1` voltou de codex — código 0, 7 arquivo(s) mudado(s), 478s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T20:53:52` I1 voltou de `escalada` para reavaliacao — **por quê:** a violacao de escopo era falso positivo do MEU oraculo: os arquivos acusados eram orquestracao/estado.json e os logs das outras vagas — escrita do proprio maestro durante o despacho, que o executor nunca viu. Consertado com lista de exclusao, provada nos quatro casos (escrita do maestro ignorada, violacao real ainda acusada, fora da raiz ainda acusada, dentro do escopo nao acusada)
- `2026-09-02T20:53:52` `I1` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo. Isto NÃO é aprovação: rode `esteira-maestro provar --task I1`
- `2026-09-02T20:53:58` prova de `I1`: **passou** (código 0) — **por quê:** único caminho para `feito`; sem isto a cadeia de prereq não anda
- `2026-09-02T20:54:08` `D1` colhido: **ESCALAR** — **por quê:** tocou fora do escopo: ['__pycache__/board.cpython-312.pyc', 'data/hub.db', 'logs/contas-estado.json', 'orquestracao/JOURNAL.md', 'orquestracao/RELATORIO-D1.md']
- `2026-09-02T20:54:53` oraculo: o git passa a decidir o que e residuo — **por quê:** o D1 foi para ESCALAR por tocar __pycache__/*.pyc e data/hub.db — bytecode que aparece so de rodar Python, e o banco que o item existe para criar. Ambos gitignored. Lista minha de excecoes envelheceria; `git check-ignore` ja sabe e nao envelhece. E RELATORIO-*.md passa a ser excluido porque TODO briefing manda escreve-lo em orquestracao/ — cobrar o executor por escrever onde eu mandei e defeito do briefing, nao dele
- `2026-09-02T20:54:53` `D1` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo. Isto NÃO é aprovação: rode `esteira-maestro provar --task D1`
- `2026-09-02T20:54:54` prova de `D1`: **passou** (código 0) — **por quê:** único caminho para `feito`; sem isto a cadeia de prereq não anda
- `2026-09-02T20:56:43` `E1` voltou de codex — código 0, 13 arquivo(s) mudado(s), 667s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T20:58:12` `G1` voltou de opencode — código 0, 2 arquivo(s) mudado(s), 126s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-02T20:58:53` `F1` voltou de codex — código 0, 2 arquivo(s) mudado(s), 170s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-03T01:12:49` oraculo: a foto do repo nao sabe QUEM escreveu — conserto com escopo vizinho — **por quê:** E1, F1 e G1 voltaram todos com VIOLACAO DE ESCOPO, e as listas se cruzavam: F1 e G1 foram acusados de criar app/, que era trabalho do E1 rodando ao lado; o E1 foi acusado de board.py, que era do D1. A foto do repo inteiro so ve antes e depois, nao autor. Agora o dispatch guarda o escopo das vagas vizinhas (na reserva e na colheita) e nao acusa o executor pelo que caiu no escopo de outro. Provado nos quatro casos, inclusive que violacao real continua acusada
- `2026-09-03T01:12:49` `E1` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo. Isto NÃO é aprovação: rode `esteira-maestro provar --task E1`
- `2026-09-03T01:12:49` `F1` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo. Isto NÃO é aprovação: rode `esteira-maestro provar --task F1`
- `2026-09-03T01:12:49` `G1` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo. Isto NÃO é aprovação: rode `esteira-maestro provar --task G1`
- `2026-09-03T01:13:12` prova de `E1`: **passou** (código 0) — **por quê:** único caminho para `feito`; sem isto a cadeia de prereq não anda
- `2026-09-03T01:13:12` prova de `F1`: **passou** (código 0) — **por quê:** único caminho para `feito`; sem isto a cadeia de prereq não anda
- `2026-09-03T01:13:18` prova de `G1`: **passou** (código 0) — **por quê:** único caminho para `feito`; sem isto a cadeia de prereq não anda
- `2026-09-03T01:15:44` prova de `D3`: **passou** (código 0) — **por quê:** único caminho para `feito`; sem isto a cadeia de prereq não anda
- `2026-09-03T01:18:13` spike de Windows: o pywebview cai para o IE11 EM SILENCIO sem WebView2 — **por quê:** achado que muda o desenho do app. Sem o WebView2 Runtime o pywebview nao levanta erro: cai para MSHTML (IE11) com um logger.warning que ninguem ve se o logging nao estiver configurado. HTMX, fetch e CSS grid quebram e o app 'fica esquisito' na maquina de uma pessoa. E gui='edgechromium' NAO forca — o codigo so testa forced_gui != 'mshtml', entao nao existe 'WebView2 ou morra' embutido; o guard e nosso. Mesma classe da armadilha do --font-montserrat: passa em todo teste e esta errado
- `2026-09-03T01:18:13` o spike cobriu 1 de 4 perguntas, e o documento diz isso na primeira tela — **por quê:** PyInstaller, SmartScreen e credencial por CLI no Windows nao foram levantados — o levantamento bateu no limite de sessao. Registrei como NAO PERGUNTADAS, nao como 'sem achados'. Resultado vazio de ferramenta nao e resultado negativo: foi a licao de ontem, quando um workflow devolveu confirmados:[] que era 112 agentes mortos
- `2026-09-03T01:18:13` fila += `E5` — guard de WebView2 — **por quê:** nasce direto do spike: degradar em silencio para IE11 e inaceitavel nesta casa. O app tem que checar antes de abrir a janela e recusar com mensagem em PT-BR dizendo o que instalar
- `2026-09-03T01:20:18` `E5` voltou de codex — código 0, 1 arquivo(s) mudado(s), 95s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-03T01:20:33` `D4` voltou de codex — código 0, 1 arquivo(s) mudado(s), 226s — **por quê:** a prova ainda não rodou; estado a_colher
- `2026-09-04T10:20:19` oraculo: rastrear vizinho por timing nao fecha — a regra passa a ser a fila — **por quê:** D4 e E5 foram acusados de novo. Dois furos: CONTINUAR.md, que sou EU editando durante o despacho; e app/janela.py no D4, escopo de um vizinho que ja tinha TERMINADO quando o D4 colheu (o rastreio por timing so via vaga ainda ocupada). A regra nova nao usa relogio: caminho que casa com o escopo declarado de QUALQUER item da fila e trabalho legitimo de alguem; o que este oraculo tem que pegar e o caminho que NINGUEM declarou — que era exatamente o caso do residuo em ~/bin. Provado em seis casos
- `2026-09-04T10:20:19` `D4` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo. Isto NÃO é aprovação: rode `esteira-maestro provar --task D4`
- `2026-09-04T10:20:19` `E5` colhido: **FEITO** — **por quê:** disco mexeu dentro do escopo. Isto NÃO é aprovação: rode `esteira-maestro provar --task E5`
- `2026-09-04T10:21:54` prova de `D4`: **passou** (código 0) — **por quê:** único caminho para `feito`; sem isto a cadeia de prereq não anda
- `2026-09-04T10:21:54` prova de `E5`: **passou** (código 0) — **por quê:** único caminho para `feito`; sem isto a cadeia de prereq não anda
