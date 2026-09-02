# Relatório T-02 — Sentinela de contas

## O que foi feito

- Criei `esteira/sentinela.py`, com um `ciclo()` que chama
  `runner.smoke_todas()`, monta um envelope `blocked` para cada falha e tenta
  enviá-lo com `comm.enviar()`.
- O envelope preserva `to="team"`. O dono aparece no título e no corpo.
- Usei um `SimpleNamespace` local com `.id`, `.meta` e `.rodada` como objeto
  mínimo aceito por `comm.envelope()`; não criei classe em `demanda.py`.
- Falha do n8n é exibida, mas não derruba a sentinela.
- `ciclo()` é idempotente: persiste em `logs/sentinela-estado.json` apenas
  avisos entregues, não os repete enquanto a falha persistir e libera novo
  aviso depois que a conta voltar a passar. Envio malsucedido pode ser tentado
  novamente no ciclo seguinte.
- Implementei o laço `while True`, intervalo de
  `config.SMOKE_INTERVALO_S`, tratamento por ciclo e registro em
  `logs/sentinela.log`, seguindo a forma de `vigia.py`.
- Implementei `--uma-vez` e `--simular-falha PESSOA:TIPO`. A simulação
  monta e imprime o envelope, sem chamar o n8n. Ela também localiza pelo
  `contas.resumo()` uma conta ativa que esteja temporariamente em cooldown.
- Criei o executável `bin/esteira-smoke`.
- `esteira/sentinela.py` tem 150 linhas, dentro do teto de 150.

## O que não foi feito

- Não alterei `runner.py`, `contas.py`, `comm.py`, `worker.py`, `vigia.py`,
  `config.py`, `contas.yaml`, `.env`, `demands/**` nem `deploy/**`.
- Não criei novo valor de `to` nem novo tipo de envelope.
- Não instalei serviço nem agendamento; esta tarefa entrega o processo e o
  modo de execução única.

O relatório é o único arquivo de entrega fora dos dois arquivos do escopo
funcional, porque foi exigido expressamente no briefing. As provas reais
também acrescentaram saída aos logs e ao estado de contas já usados por
`runner.smoke_todas()`; não editei esses artefatos manualmente.

## Premissas

- Uma falha persistente deve gerar um único aviso entregue. A recuperação
  confirmada por smoke aprovado rearma o aviso para uma falha futura.
- Quando `--simular-falha` está presente, toda notificação daquele ciclo é
  somente impressa. Assim a prova nunca depende do n8n, mesmo se houver uma
  falha real junto da simulada.
- O processo deve continuar e sair com zero depois de tratar falhas de conta
  ou de entrega. Exceções inesperadas fazem `--uma-vez` sair com 1 e, no modo
  contínuo, são registradas antes do próximo ciclo.

## O que quebrou na prova real

O cadastro lido hoje tem duas contas ativas, ambas de Nicolas, e não quatro:
`nicolas:claude` e `nicolas:codex`. No ambiente desta execução, nenhuma
passou:

- Claude repetiu tentativas de API até o timeout de 120 segundos.
- Codex terminou com erro ao inicializar o cliente interno por filesystem
  somente leitura do ambiente aninhado.
- O POST ao n8n local foi bloqueado neste ambiente. A sentinela absorveu o
  retorno `(False, erro)` e continuou.

Isso impediu a saída real esperada de quatro contas aprovadas. O código de
saída foi zero e o comportamento de falha ficou provado. Depois, uma prova
isolada com quatro resultados aprovados e `comm.enviar` configurado para
falhar caso fosse chamado produziu:

```text
Smoke concluído: 4 conta(s); 4 passaram; 0 falharam.
Nenhum aviso enviado.
```

A idempotência também foi exercitada com dois ciclos consecutivos da mesma
falha e envio bem-sucedido. O resultado foi `envios_em_dois_ciclos=1`; o
segundo ciclo informou que o aviso já havia sido entregue.

## Saídas exigidas

Comando normal:

```text
Smoke concluído: 2 conta(s); 0 passaram; 2 falharam.
Falha: conta de Nicolas (nicolas:claude).
Aviso da conta de Nicolas não enviado: HTTPConnectionPool(host='localhost', port=5678): Max retries exceeded with url: /webhook/esteira-comm (Caused by NewConnectionError("HTTPConnection(host='localhost', port=5678): Failed to establish a new connection: [Errno 1] Operation not permitted"))
Falha: conta de Nicolas (nicolas:codex).
Aviso da conta de Nicolas não enviado: HTTPConnectionPool(host='localhost', port=5678): Max retries exceeded with url: /webhook/esteira-comm (Caused by NewConnectionError("HTTPConnection(host='localhost', port=5678): Failed to establish a new connection: [Errno 1] Operation not permitted"))
saida=0
```

Comando com falha simulada:

```text
Smoke concluído: 1 conta(s); 0 passaram; 1 falharam.
Falha: conta de Nicolas (nicolas:claude).
Simulação: aviso para Nicolas <nicolas.bastos@andrademaia.com> via envelope to=team.
Título: 🔴 Conta de Nicolas falhou — claude
saida=0
```

## Lacunas nas interfaces preservadas

Se o escopo permitisse, eu consideraria:

- Em `runner.py`, fazer `smoke_todas()` devolver também o `Resultado`, para o
  aviso informar código, timeout e log sem tentar inferir texto do CLI.
- Em `runner.py`/`contas.py`, separar "contas ativas" de "contas disponíveis
  para trabalho". Hoje `smoke_todas()` usa `disponiveis()` e deixa de testar
  contas em cooldown, embora o diagnóstico periódico e a simulação ainda
  precisem enxergá-las.
- Em `contas.py`, expor uma busca pública por chave que inclua nome e e-mail,
  mesmo durante cooldown. `resumo()` não traz `pessoa_id`, `chave` ou e-mail.
- Em `comm.py`, oferecer um envelope para eventos de sistema, sem exigir um
  objeto no formato de demanda. O objeto mínimo local resolve sem alterar o
  contrato atual.
