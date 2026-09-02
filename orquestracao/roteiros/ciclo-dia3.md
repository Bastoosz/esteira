# Roteiro de prova do ciclo — Dia 3

Este roteiro prova a demanda 1002 em duas rodadas: a primeira pergunta e sai
com código 42; a segunda retoma com a resposta persistida e entrega o XLSX.

> Rode esta prova sem outros executores escrevendo no repositório. Ao fechar
> cada rodada, o worker faz `git add -A`, commit e push da raiz inteira.

## 1. Confirmar o ponto de partida

No terminal 1:

```bash
cd "/home/nicolas/Área de trabalho/esteira"
.venv/bin/python -c "import sys;sys.path.insert(0,'.');from esteira.demanda import Demanda;d=Demanda('1002');print('estado=',d.estado);print('abertas=',[q['n'] for q in d.perguntas_abertas()]);print('proxima_da_fila=',(Demanda.proxima_da_fila() or type('x',(),{'id':None})).id)"
```

Esperado antes da primeira rodada:

```text
estado= PRONTA
abertas= []
proxima_da_fila= 1002
```

Falhou se o estado ou o ID forem diferentes. Não inicie o worker: outra
demanda está na frente ou a pasta 1002 precisa ser corrigida.

## 2. Subir o board

Ainda no terminal 1:

```bash
set -a
. ./.env
set +a
.venv/bin/python board.py
```

Esperado: o Flask informa `http://127.0.0.1:5000` (ou a porta definida em
`BOARD_PORT`). Falhou se o processo encerrar ou `/` não responder. Deixe-o
rodando; a rota de resposta usada adiante pertence a este processo.

## 3. Subir o worker e acompanhar a primeira rodada

No terminal 2:

```bash
cd "/home/nicolas/Área de trabalho/esteira"
set -a
. ./.env
set +a
.venv/bin/python -m esteira.worker
```

Esperado: `worker de pé. ctrl-c para parar.`. Em até um intervalo do worker,
a 1002 passa para `EXECUTANDO`, cria `rodadas/1/` e `runs/1.log`.

No terminal 3, acompanhe o estado durável:

```bash
cd "/home/nicolas/Área de trabalho/esteira"
watch -n 2 '.venv/bin/python -c "from esteira.demanda import Demanda;d=Demanda(\"1002\");print(\"estado=\",d.estado,\"rodada=\",d.rodada,\"pid=\",d.meta.get(\"pid\"));print(\"abertas=\",[q[\"n\"] for q in d.perguntas_abertas()])"'
```

Falhou se não aparecer `EXECUTANDO` nem o journal registrar
`PRONTA -> EXECUTANDO (rodada 1)`. Consulte `runs/1.log`; não rode um segundo
worker.

## 4. Ver a pergunta, o código 42 e a espera humana

No terminal 3, interrompa o `watch` com `Ctrl-C` e rode:

```bash
while ! find demands/1002/questions -maxdepth 1 -name '*.json' | grep -q .; do sleep 2; done
N="$(find demands/1002/questions -maxdepth 1 -name '*.json' -printf '%f\n' | sed 's/\.json$//' | sort -n | tail -1)"
.venv/bin/python -m json.tool "demands/1002/questions/$N.json"
until test -f demands/1002/execucoes.jsonl && .venv/bin/python -c "import json,pathlib;linhas=pathlib.Path('demands/1002/execucoes.jsonl').read_text().splitlines();raise SystemExit(0 if any(json.loads(linha).get('codigo') == 42 for linha in linhas) else 1)"; do sleep 2; done
tail -n 1 demands/1002/execucoes.jsonl
rg -n 'pergunta [0-9]+ registrada|Encerrando execução' demands/1002/runs/1.log
.venv/bin/python -c "from esteira.demanda import Demanda;d=Demanda('1002');print('estado=',d.estado);print('abertas=',[q['n'] for q in d.perguntas_abertas()])"
```

Esperado: a pergunta oferece `manter todos` e `somente ativos`, o último
registro de execução tem `"codigo": 42`, e o estado é
`ESPERANDO_HUMANO` com `abertas= [1]`. O worker continua de pé, mas não roda
a demanda enquanto houver pergunta aberta. O `rg` mostra também a mensagem
emitida pelo próprio `esteira-ask` antes de ele devolver 42.

Falhou se não houver JSON de pergunta, se o código não for 42 ou se o estado
for `TRAVADA`. O código 42 é do agente registrado em `execucoes.jsonl`; o
processo contínuo do worker não deve encerrar.

## 5. Responder pelo endpoint e tornar `PRONTA` observável

No terminal 2, pare temporariamente o worker com `Ctrl-C`. Isso evita que ele
consuma `PRONTA` antes da conferência. No terminal 3:

```bash
N="$(find demands/1002/questions -maxdepth 1 -name '*.json' -printf '%f\n' | sed 's/\.json$//' | sort -n | tail -1)"
curl --fail-with-body -sS -X POST "http://127.0.0.1:5000/answer/1002/1002-$N" -H 'Content-Type: application/json' --data '{"resposta":"manter todos","autor":"equipe-dia3"}'
echo
test -f "demands/1002/answers/$N.md" && sed -n '1,20p' "demands/1002/answers/$N.md"
.venv/bin/python -c "from esteira.demanda import Demanda;d=Demanda('1002');print('estado=',d.estado);print('abertas=',[q['n'] for q in d.perguntas_abertas()]);print('proxima_da_fila=',(Demanda.proxima_da_fila() or type('x',(),{'id':None})).id)"
```

Esperado: o POST devolve `{"ok":true}`, o arquivo `answers/$N.md` contém a
resposta, `estado= PRONTA`, `abertas= []` e `proxima_da_fila= 1002`.

Falhou em HTTP 400 se a resposta estiver vazia e em 404 se o board ou a
demanda não estiverem acessíveis. Se o estado continuar
`ESPERANDO_HUMANO`, confira se ainda existe outra pergunta sem resposta.

## 6. Ver a retomada e a entrega

No terminal 2, suba o worker novamente:

```bash
cd "/home/nicolas/Área de trabalho/esteira"
set -a
. ./.env
set +a
.venv/bin/python -m esteira.worker
```

No terminal 3:

```bash
until rg -q 'PRONTA -> EXECUTANDO \(rodada 2\)' demands/1002/journal.md; do sleep 2; done
rg 'respondeu pergunta|PRONTA -> EXECUTANDO' demands/1002/journal.md
test -f demands/1002/runs/2.log && tail -n 40 demands/1002/runs/2.log
until .venv/bin/python -c "from esteira.demanda import Demanda;raise SystemExit(0 if Demanda('1002').estado in ('EM_REVISAO','TRAVADA') else 1)"; do sleep 5; done
.venv/bin/python -c "from esteira.demanda import Demanda;d=Demanda('1002');print('estado=',d.estado);print('rodada=',d.rodada)"
find demands/1002/outbox -maxdepth 1 -type f -printf '%f %s bytes\n'
```

Esperado: o journal mostra a resposta antes de
`PRONTA -> EXECUTANDO (rodada 2)`, `runs/2.log` existe, o estado final é
`EM_REVISAO` e há um XLSX não vazio em `outbox/`.

Falhou se o estado final for `TRAVADA`, se a rodada continuar em 1, se a
resposta não aparecer no prompt/log da retomada ou se faltar o XLSX. Nesse
caso, pare o worker e preserve `runs/2.log`, `journal.md` e
`execucoes.jsonl` para diagnóstico.

Ao terminar, encerre board e worker com `Ctrl-C`.
