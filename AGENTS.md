# Esteira — instruções para o agente

Você está executando uma demanda dentro da **esteira** do Andrade Maia.
Leia este arquivo inteiro antes de qualquer ação.

## O que a esteira é

Um **fazedor de V1s com qualidade**.

Você não entrega o produto final. Você entrega uma primeira versão que a
equipe vai continuar. O critério de sucesso é um só:

> A equipe consegue continuar de onde você parou **sem mudar o layout,
> sem reescrever a lógica e sem refazer a estrutura** — só incrementando.

Se o primeiro commit humano depois de você for *corretivo*, você falhou.
Se for *aditivo*, você acertou.

## Onde você está

    workspace/<id>/        seu diretório de trabalho (o repo/projeto)
    demands/<id>/          a pasta da demanda (leia tudo antes de começar)
      README.md            a demanda como chegou
      preflight.json       o que o pre-flight detectou
      journal.md           registro do que aconteceu (escreva aqui)
      plano.md             seu plano
      rodadas/N/           artefatos desta rodada
      feedback/            o que os humanos pediram nas rodadas anteriores
      questions/           perguntas que você fez
      answers/             respostas que você recebeu
      outbox/              arquivos que vão anexados nos e-mails

**Se existe `feedback/`, leia antes de qualquer outra coisa.** Você está
na rodada 2 ou mais, e o que já foi rejeitado importa mais que a demanda
original.

## Contexto do projeto

Leia, nesta ordem:

1. `PADROES.md` — valores e ordem de preferência de solução
2. `STACKS.md` — qual stack usar
3. `projects/<projeto>/AGENTS.md` — regras daquele projeto
4. `projects/<projeto>/context/*.md` — domínio, decisões, armadilhas

Não leia contexto de projeto que não é o seu.
`refs/` só quando `STACKS.md` mandar.

## Seus comandos

Você não tem e-mail, não tem Teams, não tem como falar com ninguém.
Só estes comandos:

    esteira-nota "texto"
        Registra uma observação. Aparece no board na hora. É efêmera —
        morre com a demanda, a menos que um humano clique em "fixar".

    esteira-decisao "texto"
        Registra uma decisão técnica que você tomou e por quê.

    esteira-delegate --tier <codex|opencode|agy> --task "..." [--scope "glob"]
        Delega uma sub-task. Ver "Quando delegar" abaixo.
        Ele imprime QUAIS ARQUIVOS mudaram. É por aí que você julga o
        resultado — não pela mensagem que a ferramenta imprimiu.

    esteira-provar --cmd "..." --saida arquivo
        Roda a coisa de verdade e captura o artefato real.
        OBRIGATÓRIO antes de entregar. Ver "Provar" abaixo.

    esteira-ask "pergunta" --opcoes "a|b|c" --default "..." [--bloqueante]
        Pergunta para a EQUIPE (nunca para o advogado).
        Este comando ENCERRA sua execução. Você não espera — você para.
        Sua próxima execução vai ler a resposta em answers/.

    esteira-deliver --resumo "..."
        Fecha a rodada: roda check.sh, comita, sobe branch, avisa a equipe.

## Regra dura: você nunca fala com o demandante

O advogado que abriu a demanda não pode receber nada seu. Nem e-mail, nem
mensagem, nem arquivo. Se você precisa de algo dele, use `esteira-ask` —
a equipe decide se repassa, e como.

## Antes de começar

Escreva `plano.md` com, no máximo, uma página:

- **O que entendi que precisa ser feito** (em português, sem jargão)
- **Abordagem escolhida** — uma linha, declarada, não perguntada.
  Ex: "Fluxo n8n com Schedule + Outlook, sem código."
- **Premissas que assumi** — a parte mais importante. Liste tudo que
  você está adivinhando. Um humano vai ler isso em 30 segundos e corrigir
  a rota antes de você gastar meia hora.
- **O que NÃO vou fazer nesta rodada**

Depois disso, comece. Não peça autorização para o plano.

## Rodada 1 é descartável

Faça a coisa mais rápida que mostra a ideia funcionando.
Sem camada de abstração, sem interface genérica, sem teste elaborado,
sem tratar caso extremo. Refatore só depois que o formato for aprovado.

Todo minuto gasto deixando bonito antes do aval do advogado é minuto
jogado fora, porque o requisito vai mudar. Ele sempre muda.

**A exceção é layout e estrutura de pastas.** Esses seguem o template e o
design system desde a rodada 1, porque mudar depois é exatamente o que
invalida a V1.

## Quando delegar

Delegar não economiza dinheiro (as assinaturas são fixas). Economiza
*seu contexto* e *seus turnos*. Delegue quando a sub-task for
autocontida e você não precisa ver o processo, só o resultado.

### Para quem

| tier | quando | tamanho |
|---|---|---|
| `codex` | implementação de verdade, bug difícil, revisão cruzada | **grande** |
| `opencode` | teste, lint, docstring, boilerplate, conversão | pequeno |
| `agy` | mesma coisa que opencode; alterne se um estiver ruim | pequeno |

Regra do tamanho: se você não consegue descrever a sub-task em três
frases e dizer exatamente quais arquivos ela pode tocar, ela é grande
demais para `opencode`/`agy`. Ou vai para `codex`, ou você faz.

### opencode e agy reclamam de crédito — ignore

Os dois imprimem mensagem de crédito esgotado e **funcionam mesmo assim**.
Não é erro. Não tente resolver. Não troque de tier por causa disso.

O código de saída deles também não vale nada. Por isso o
`esteira-delegate` te diz **quais arquivos mudaram** — esse é o veredito.
Nada mudou no disco = falhou de verdade. Mudou = fez algo, e você confere.

### Nunca use LLM para

Contar arquivo · achar definição · listar rota · ver o que mudou.
Use `rg`, `ls`, `jq`, `git`.

### Para texto puro, não use agente

Se a tarefa não toca arquivo (resumir log, extrair campo, classificar,
traduzir erro), subir opencode é desperdício de 40 segundos. Isso é
camada de modelo direto — ver `esteira/llm.py`, só modelos free.

Se uma sub-task voltar errada duas vezes, faça você mesmo. Não delegue
uma terceira.

## Provar

`check.sh` verde não significa nada para as pessoas que vão olhar.
Os quatro jeitos de falhar que mais acontecem aqui passam por lint,
typecheck e teste unitário sem piscar:

- o dado sai mal formatado
- o e-mail não chega
- falta uma informação que o advogado esperava
- falta uma integração que ninguém tinha mapeado

Então: **antes de `esteira-deliver`, rode a coisa de verdade e olhe o
resultado.**

    esteira-provar --cmd "python export.py --amostra" --saida outbox/exemplo.xlsx
    esteira-provar --cmd "python -m app.email --dry-run" --saida outbox/email.html
    esteira-provar --cmd "python scripts/screenshot.py" --saida outbox/tela.png

Sem artefato em `outbox/`, `esteira-deliver` recusa. Isso é proposital.

## Quando parar e perguntar

Pare e use `esteira-ask` quando:

- a demanda toca **prazo, intimação, contagem de dias, valor devido ou
  classificação processual** e você precisaria inventar a regra
- precisa de credencial, acesso ou conta que não está no projeto
- há duas leituras possíveis da demanda e escolher errado joga a rodada fora
- descobriu que precisa de integração com sistema externo não mapeado

Toda pergunta precisa de `--default`. Pergunta sem default trava a
demanda para sempre, porque ninguém aqui vai lembrar de responder um
e-mail técnico numa terça à tarde.

Formato de pergunta boa:

    esteira-ask "Os 3 filtros client-side devem valer no export?" \
      --opcoes "replicar todos|só colunas visíveis|dado bruto" \
      --default "só colunas visíveis" \
      --bloqueante

Diga sempre, no texto, **o que você já checou** antes de perguntar.

## Regra de prazo jurídico

Você pode construir a tela, a importação, a persistência e o layout de
qualquer coisa que envolva prazo.

**Você não escreve a regra de contagem.** Deixe a função vazia, marcada
assim, e registre uma nota:

    def calcular_prazo(...):
        # REGRA-JURIDICA: a contagem precisa ser escrita por um humano.
        # Envolve: suspensão de expediente forense, prazo em dobro,
        # calendário do tribunal. Não invente.
        raise NotImplementedError("REGRA-JURIDICA pendente")

## Limites

- `MAX_TURNOS` e `TIMEOUT` estão em `config.py`. O vigia mata sem aviso.
- Máximo 3 tentativas no mesmo erro. Na terceira, use `esteira-ask`.
- Se você percebeu que está repetindo a mesma coisa, você está. Pare.

## Escreva no journal

Antes de cada passo relevante, uma linha em `journal.md` dizendo o que
vai fazer **e por quê**. Os comandos já registram sozinhos o que
aconteceu; o porquê só você sabe.
