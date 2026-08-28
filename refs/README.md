# refs — referência carregada sob demanda

Nada aqui entra no contexto por padrão. O agente lê só quando
`STACKS.md` ou o papel mandar.

    guia-stacks.md         o Guia de Stacks completo (as 16 páginas)
    design-system/         o DS Andrade Maia — readme.md + guidelines/
    n8n/*.json             OS FLUXOS QUE VOCÊS JÁ TÊM. Ver abaixo.
    skills/                skills de terceiros (npx skills add), com o commit anotado

## refs/n8n — a pasta de maior retorno do projeto

Gerar JSON de fluxo n8n do zero é difícil: schema de nó, conexões,
posição. O resultado costuma nem abrir.

**Copiar e adaptar um exemplo de vocês é fácil.**

Ponha aqui 5 ou 6 fluxos reais, exportados, com os segredos removidos e
um nome que diga o que ele faz:

    outlook-agendado-relatorio.json
    outlook-le-caixa-e-classifica.json
    teams-card-com-botao.json
    http-para-planilha.json
    schedule-com-retry.json

Isso é a diferença entre o agente acertar 30% e 80% das automações.
É trabalho chato e é o item de maior retorno da lista.

## refs/skills

Instale com `npx skills@latest add <repo>` — **não** com o plugin
gerenciado do Claude Code. O plugin atualiza sozinho, e instrução que
muda atrás de você quebra a reprodutibilidade: você deixa de conseguir
explicar por que a demanda #1799 se comportou diferente da #1827.

Anote o commit em `refs/skills/ORIGEM.md` e atualize quando **você**
decidir, num PR que a equipe revisa.
