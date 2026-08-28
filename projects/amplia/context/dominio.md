# Domínio — linguagem compartilhada

> Teto: 200 linhas. Vocabulário do projeto, para o agente nomear as coisas
> como a equipe nomeia. Definições extraídas do AMPLIA, não regras jurídicas.

## Produto e documentos

| Termo | O que significa aqui |
|---|---|
| AMPLIA | Copiloto de IA jurídica interno do Andrade Maia Advogados. |
| Acervo | Área “Meus documentos”, com arquivos do usuário armazenados no S3 e preparados para consulta. |
| Documento pronto | Documento cujas capacidades necessárias estão explicitamente prontas no contrato `DocumentCapabilities`; não é um estado único. |
| Capacidade de documento | Aptidão verificável, como ter texto, trechos, embeddings ou busca RAG disponíveis. |
| Conversa focada | Conversa cuja recuperação fica restrita aos documentos anexados ou selecionados. |
| Matriz revisável | Resultado estruturado de uma análise que permite correção manual antes do relatório. |
| Memória do usuário | Preferências e fatos salvos para reutilização entre conversas do mesmo usuário. |

## Busca e evidência

| Termo | O que significa aqui |
|---|---|
| RAG | Geração de resposta apoiada por trechos recuperados do acervo autorizado. |
| RAG híbrido | Busca que combina texto integral em PT-BR e similaridade vetorial, fundindo os rankings por RRF. |
| Escopo de recuperação | Conjunto de documentos autorizados e efetivamente pesquisados para uma resposta. |
| Resultado vazio | Busca concluída sem trechos; deve trazer motivo e não pode representar falha de provedor. |
| Evidência jurídica | Fonte e trecho que sustentam uma afirmação, com atualidade, origem e cobertura rastreáveis. |
| Escavador | Provedor externo consultado para dados processuais, inclusive por número CNJ. |
| JUIT | Provedor de jurisprudência usado como alternativa ao catálogo interno de acórdãos. |
| Acórdão | Decisão colegiada de tribunal. |
| Jurisprudência | Conjunto de decisões judiciais reiteradas sobre determinado tema. |
| Súmula | Síntese de jurisprudência consolidada, vinculante ou persuasiva. |
| Tema repetitivo | Questão processual comum a múltiplos casos, julgada sob rito de repetição. |
| CNJ | Conselho Nacional de Justiça e, no produto, o formato padronizado do número processual usado na consulta. |

## Análises jurídicas

| Termo | O que significa aqui |
|---|---|
| Petição inicial | Documento que inicia a ação e apresenta fatos e pedidos do autor. |
| Contestação | Resposta do réu à petição inicial. |
| Análise de Impugnação | Compara inicial e contestação, relaciona pedidos e apresenta o enfrentamento em matriz revisável. |
| Comparador de Provas | Relaciona alegações da petição aos anexos e apresenta suficiência com linguagem de apoio. |
| Dialeticidade | Princípio recursal segundo o qual o recurso deve enfrentar especificamente os fundamentos da decisão recorrida. |
| Revisão de dialeticidade | Modo especializado da conversa que auxilia a verificar esse enfrentamento. |
| Impugnado | Rótulo da matriz que indica enfrentamento identificado na contestação; exige revisão humana. |
| Não impugnado | Rótulo da matriz para pedido sem enfrentamento identificado; não é conclusão jurídica definitiva. |
| Não localizado com segurança | Rótulo de incerteza usado quando o sistema não encontrou suporte suficiente para classificar. |
