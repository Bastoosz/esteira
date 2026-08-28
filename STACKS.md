# Stacks — decisão

Referência completa em `refs/guia-stacks.md`. Leia só depois de escolher.

## Na dúvida, Stack 1

É mais barato evoluir um projeto simples do que carregar complexidade
que nunca foi usada.

## Tabela de decisão

Marcou **qualquer** critério da coluna Stack 2 → é Stack 2 → **pergunte
antes de seguir**.

| Critério | Stack 1 | Stack 2 |
|---|---|---|
| Usuários simultâneos | até ~50 | mais |
| Autenticação | nenhuma ou simples | multi-perfil, permissões |
| Banco | SQLite ou JSON | PostgreSQL |
| Processamento assíncrono | não | sim (fila, worker) |
| APIs externas | 1–2 | várias, em paralelo |
| Audiência | interna | cliente externo |
| Dados sensíveis (LGPD) | evitar | tratar com rigor |
| Tempo até primeira entrega | horas | dias |

## Stack 1 — rápido e bonito

Python 3.11+ · Flask · Jinja2 · **design system AM (tokens CSS)** · HTMX ·
Alpine.js · SQLite ou JSON · `requirements.txt` · `python app.py`

Template: `template-stack1-flask-htmx` — **clone, não crie do zero.**

    projeto/
    ├── app.py            máx ~200 linhas; o resto vai pra services/
    ├── config.py         toda config aqui, no topo, com fallback de env
    ├── requirements.txt
    ├── static/ds/        design system copiado (tokens, fontes, logos, ícones)
    ├── templates/
    │   ├── base.html     já vem com o DS ligado
    │   └── _partials/    button, input, select, checkbox, card, badge,
    │                     tabela, upload, vazio, erro
    ├── services/
    └── data/             gitignored

HTMX antes de JavaScript. Alpine só para estado local de UI.

## Stack 2 — robusto

FastAPI · Pydantic v2 · PostgreSQL · SQLAlchemy async · Alembic · Redis ·
Celery · Docker Compose · pytest · Sentry

Template: `template-stack2-fastapi`.

**O agente não escolhe Stack 2 sozinho.** Se a demanda parecer Stack 2,
use `esteira-ask` com a tabela acima e diga qual critério bateu.

## Sempre, nas duas

- Config no topo, em `config.py`. Nunca espalhada.
- **Chave de API sempre em `.env`. Nunca constante no código** —
  ao contrário do que o guia permite para script humano. Código de agente
  vai para repo, para preview e para anexo de e-mail.
- Conventional Commits: `feat:` `fix:` `docs:` `refactor:` `test:` `chore:`
- `README.md` com: o que é, como rodar, variáveis necessárias
- `.env.example` com todas as variáveis, valores fictícios
