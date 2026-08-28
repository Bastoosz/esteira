# Mapa dos arquivos

    AGENTS.md          [FIXO·global]  como o agente opera; os comandos
    PADROES.md         [FIXO·global]  valores, ordem de preferência, contas
    STACKS.md          [FIXO·global]  tabela de decisão de stack
    README.md                         como subir; a arquitetura em uma tela
    BUILD.md                          plano ordenado para o Claude Code
    ESTRUTURA.md                      este arquivo
    config.py                         tudo que se ajusta, no topo
    contas.yaml        [FIXO]         registro das 4 pessoas — SEM SEGREDO
    board.py                          Flask, só lê e mostra

    bin/                              o que o agente pode chamar
      esteira-ask                     pergunta e ENCERRA (exit 42)
      esteira-nota                    observação efêmera
      esteira-decisao                 decisão técnica
      esteira-delegate                sub-task em codex/opencode/agy
      esteira-provar                  roda de verdade e captura o artefato
      esteira-deliver                 gates + commit + preview

    esteira/
      demanda.py                      a demanda é uma pasta; git é a verdade
      runner.py                       wrapper de CLI — a peça mais frágil
      contas.py                       seleção de conta, cooldown, atribuição
      comm.py                         envelope para o n8n
      preflight.py                    checklist de 6 perguntas na chegada
      worker.py                       loop: uma demanda por vez
      vigia.py                        watchdog burro de propósito

    papeis/            [FIXO·papel]
      orquestrador.md                 como planejar, delegar, parar
      subtask-teste.md · subtask-lint.md · subtask-n8n.md · subtask-revisao.md

    projects/_exemplo/ [FIXO·projeto] copie para criar projeto de verdade
      AGENTS.md                       ≤150 linhas
      check.sh                        um comando, saída 0 = verde
      context/dominio.md              ≤200 — linguagem compartilhada
      context/decisoes.md             ≤200 — append-only, datado
      context/armadilhas.md           ≤150 — cresce pelo botão "fixar"

    refs/                             carregado sob demanda; ver refs/README.md
    n8n/README.md                     especificação dos 4 fluxos
    scripts/check_ds.sh               aderência ao design system
    templates/                        board (tokens AM, HTMX, sem build)
    demands/1001/                     demanda de exemplo — apague depois
    workspace/                        gitignored — onde o agente trabalha
    logs/                             gitignored

## Tetos

Fixo que passa do teto não é apagado — o worker abre uma sub-task de
compactação: modelo barato reescreve condensando, sem perder regra, e abre
PR. Você revisa 20 linhas de diff em vez de descobrir em seis meses que o
`armadilhas.md` tem 900 linhas e ninguém lê.

## Códigos de saída

    0   terminou (esteira-deliver já mudou o estado)
    42  perguntou — execução pausa, retomada é execução nova
    43  bloqueado por acesso externo
    124 timeout (o runner mata)
    *   erro; o vigia parqueia e avisa
