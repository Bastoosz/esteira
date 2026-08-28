# Projeto: AMPLIA

> Contexto operacional da plataforma de inteligência jurídica do Andrade Maia.
> Teto: 150 linhas.

## O que é

O AMPLIA é o copiloto jurídico interno do Andrade Maia Advogados. Reúne conversa
com RAG, acervo e análise de documentos, Microsoft 365, consulta processual,
jurisprudência, planilhas e voz em uma SPA hospedada na Vercel, com serviços na AWS.

## Stack real

### Frontend

- React 18.3, Vite 5 e TypeScript 5; aplicação ativa em `frontend/src/amplia/`.
- Tailwind CSS 3, componentes shadcn/ui e Radix, React Router 6 e TanStack Query 5.
- Vitest para testes, ESLint para análise estática e Vercel para publicação.
- `frontend/src/components/` é legado; a evolução da interface ocorre em
  `frontend/src/amplia/`.

### Backend

- Python 3.12 em monorepo `uv` com FastAPI 0.115, Django 5 e *workers* assíncronos.
- FastAPI atende IA, RAG, SSE, voz e ferramentas; Django atende administração e
  migrações; os *workers* processam OCR, embeddings, auditoria e análises.
- Postgres + pgvector atrás de PgBouncer, Supabase Auth, Redis, S3, SQS, Textract,
  SSM/KMS, ECS Fargate e Cloudflare Tunnel.
- OpenRouter fornece LLMs; OpenAI fornece embeddings e voz; Microsoft Graph,
  Escavador e JUIT são integrações externas.
- Terraform descreve a infraestrutura em `backend/infra/terraform`.
- As Edge Functions Supabase em Deno são somente contingência do chat.

## Como rodar

Pré-requisitos documentados: Node.js 20, Python 3.12+, `uv` 0.4+ e Git 2.40+.

Backend:

    cd backend
    cp .env.example .env
    uv sync --all-packages --group dev
    docker compose up -d
    make migrate
    make dev-fastapi       # porta 8001
    make dev-django        # porta 8000, em outro terminal
    make dev-workers       # em outro terminal, se necessário

Frontend:

    cd frontend
    npm install
    npm run dev            # vite.config.ts usa a porta 8080

Variáveis e credenciais estão descritas em `backend/.env.example` e
`frontend/.env.example`. Nunca leia, copie ou versione valores de `.env` reais.

## Como validar

A partir da pasta `projects/amplia/` da esteira:

    bash check.sh /caminho/para/AMPLIA.APP_vers-o-2

Com o ambiente completo, os comandos canônicos do projeto são:

    cd backend && uv run ruff check . && uv run pytest tests/ -q
    cd frontend && npm run lint && npm run typecheck && npm run build && npm run test

## O que NÃO tocar

- Não alterar produção, filas, alarmes, banco, migrações, publicação ou
  segredos sem aprovação humana explícita no turno atual.
- Não registrar conteúdo integral de documentos jurídicos, e-mails ou dados
  pessoais; usar identificadores, hashes, contagens e metadados seguros.
- Não tratar Edge Functions Deno como caminho primário nem reintroduzir recursos
  retirados do protótipo: reconhecimento facial, gestos e projeção remota.
- Não criar regra de prazo, intimação, valor devido ou classificação processual.
  Marcar `REGRA-JURIDICA` e encaminhar para validação humana.
- Não confundir falha de provedor jurídico com ausência de resultado.
- Não prometer capacidade de documento antes de ela constar como pronta no
  contrato `contracts/document-capabilities.schema.json`.

## Responsáveis

- produto: Andrade Maia Advogados.
- responsável formal por operação do backend/DLQ: Mickel Baptista, conforme
  `docs/runbooks/dlq-triage.md`.
- responsável técnico citado em decisões de segurança: Stefan Gagliotti.
- dono geral do produto e revisor padrão de PR: não identificados no repositório.
