# Converter cadastro CSV em XLSX formatado

_interno · equipe de operações · 2026-09-02T15:39:19_

Precisamos de um script Python pequeno que converta um CSV de cadastro de contatos em um XLSX pronto para revisão pela equipe.

O CSV de exemplo deve ter as colunas `nome`, `email`, `status` e `cadastrado_em`. O XLSX precisa ter cabeçalho destacado, filtro, primeira linha congelada, larguras legíveis e datas no formato brasileiro. Gere uma amostra real em `outbox/` e documente como executar.

Antes de implementar, use `esteira-ask` uma única vez para confirmar se os contatos com status `inativo` devem ser mantidos ou removidos. Ofereça as opções `manter todos` e `somente ativos`, com `manter todos` como padrão, e informe que você já verificou as colunas pedidas. Depois da resposta, conclua a entrega em uma nova rodada.

Não crie interface, banco, integração externa nem regra jurídica.
