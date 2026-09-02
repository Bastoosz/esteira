# Plano — bloco de orquestração de 2026-09-02

## O que entendi

O repo fechou os Dias 0, 1 e 2 do `BUILD.md`. O que falta para a esteira
ter valor é **o ciclo rodar sozinho de ponta a ponta** — Dia 3 — e o
alarme de credencial do Dia 6, que é o que converte a dívida da credencial
copiada em aviso em vez de quebra silenciosa.

Abordagem em uma linha: **fechar o Dia 3 primeiro, com prova de disco em
cada item; nó Windows e CLI de orquestração só depois.**

## O que o reconhecimento mudou no plano

Três coisas que eu não sabia antes de rodar comando.

### 1. Dois runtimes estavam caídos — consertados antes de qualquer despacho

    codex     127  comando não encontrado
    opencode    1  UnknownError do servidor

- **`codex`**: o *symlink* no `bin` do nvm tinha desaparecido, com o pacote
  e a dependência nativa no lugar. Recriar o link não bastou: o *loader*
  procura `@openai/codex/vendor/<triple>/bin/codex` e o binário estava em
  `@openai/codex/node_modules/@openai/codex-linux-x64/vendor/...`, ou seja,
  a resolução do pacote de plataforma estava quebrada.
  `npm install -g @openai/codex@latest` resolveu → **0.152.1** (era 0.150.1).
  É a segunda vez que este CLI se apaga sozinho. Primeira suspeita sempre.
- **`opencode`**: `hy3-free` **saiu do ar** entre 2026-08-28 e hoje. A
  armadilha do `PADROES.md` valendo pela segunda vez em cinco dias: id de
  modelo *free* é validade, não configuração.

  Testei os **5** *free* existentes hoje, com prova de disco e não de
  texto. **Todos os 5 escreveram o arquivo.** Passei o `.env` para
  `mimo-v2.5-free` e deixei os outros quatro registrados como reserva na
  ordem em que passaram. Quando o próximo cair, a lista está no `.env`.

Depois: **4/4 verdes.**

### 2. A demanda 1001 é *fixture*, não execução

O `BUILD.md` Dia 3 diz "roda a 1001 de verdade". Ela não serve para isso:

- os dois registros de `execucoes.jsonl` têm o **mesmo** *timestamp* que a
  criação da demanda;
- `runs/` está **vazio** — nenhum log de execução existe;
- o journal salta `NOVA -> EM_REVISAO` sem passar por `PRE_FLIGHT`,
  `PRONTA` nem `EXECUTANDO`.

Foi escrita à mão para o board ter o que mostrar, e o `README.md` diz isso.
Além disso ela está em `EM_REVISAO`, e `proxima_da_fila()` só pega `PRONTA`
ou `ESPERANDO_HUMANO` sem pergunta aberta — o worker **não a pegaria**.

**Decisão:** criar uma demanda de teste nova (`1002`), pequena e real, e
provar o ciclo nela. A 1001 fica intacta como referência de formato. O item
do `BUILD.md` é satisfeito no que ele quer — o ciclo fechando — e fica
reproduzível, o que a 1001 não seria depois de eu mexer nela.

### 3. O worker comita o repo inteiro — isso serializa parte do trabalho

`esteira/worker.py::commit()` roda `git add -A` + `commit` + `push` na
`BASE_DIR` a cada rodada. Se um executor estiver escrevendo no repo quando
o worker fechar uma rodada, **o worker comita o trabalho pela metade dele**
e empurra.

Não é defeito: "git é a verdade" é o desenho. Mas é uma restrição de
orquestração que ninguém tinha escrito. Consequência:

> **Rodar o worker de verdade não pode acontecer em paralelo com vaga que
> escreve na `BASE_DIR`.**

Por isso o A1 virou dois itens: a preparação é delegável e paralela; a
execução do worker é minha e serializada, com as vagas de escrita paradas.

## Premissas que assumi

1. A 1001 pode ficar como está. Não apago — o `README.md` manda apagar
   "quando for valer", e não é hoje.
2. `POLITICA_CONTA=fixa` / `nicolas` continua. Não ligo `rodizio`:
   `PADROES.md` e `README.md` pedem confirmação de termos, e a aritmética
   da casa não precisa.
3. `mimo-v2.5-free` como *free* padrão por continuidade com o Dia 1, e não
   porque é melhor — os 5 empataram na prova.
4. O remote é `Bastoosz/esteira` (mudou de `AndradeMaia-Tech/esteira` na
   sessão anterior, por falta de acesso à organização). O
   `worker.commit()` empurra para lá automaticamente.

## O que NÃO vou fazer neste bloco

- **Frente B (nó Windows) além do spike B1.** Nó remoto que distribui
  trabalho de um ciclo que ainda não fecha sozinho é complexidade sem
  cliente. B1 é medição e cabe agora; B2 em diante espera A1 e A2 verdes.
- **`esteira-maestro` completo.** Nesta sessão: `doctor`, `fila`, `slots`,
  e o `tick` com `colher`. `dispatch` entra, mas sem agendamento.
- **Nada da lista proibida** do `BUILD.md`, e em particular: nenhum merge
  automático, nenhum broker, nenhum formato de estado novo além de
  `jsonl` + git.
- **Não vou transformar o Orca em runtime.** `CMD_ORCA` fica vazio.
