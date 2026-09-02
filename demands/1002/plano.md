## O que entendi que precisa ser feito

Preparar uma demanda real e pequena para converter um cadastro CSV em uma
planilha XLSX legível, com uma pergunta obrigatória que demonstre a pausa e a
retomada da esteira.

## Abordagem escolhida

Script Python de conversão, sem interface, executado em duas rodadas separadas
por uma pergunta à equipe.

## Premissas que assumi

- A equipe responderá se contatos inativos entram no XLSX.
- `manter todos` é um padrão seguro porque não descarta dados.
- O agente poderá criar um CSV de amostra no workspace para provar a conversão.
- Um XLSX em `outbox/` é o artefato suficiente para a revisão desta V1.

## O que NÃO vou fazer nesta rodada

- Criar interface, banco de dados ou integração externa.
- Definir regra jurídica, prazo ou valor devido.
- Executar a rodada do worker durante a preparação da demanda.
