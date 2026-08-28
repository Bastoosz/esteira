# Relatório Dia 0 — AMPLIA

## Arquivos criados

- `AGENTS.md`
- `check.sh`
- `context/dominio.md`
- `context/decisoes.md`
- `context/armadilhas.md`
- `RELATORIO-DIA0.md`

## Stack encontrada

### Frontend

React 18.3, Vite 5, TypeScript 5, Tailwind CSS 3, shadcn/ui com Radix,
React Router 6, TanStack Query 5, ESLint e Vitest. O aplicativo ativo fica em
`frontend/src/amplia/` e é publicado na Vercel.

### Backend

Monorepo Python 3.12 gerenciado por `uv`, com FastAPI 0.115, Django 5 e oito
*workers* assíncronos. Usa Postgres + pgvector/PgBouncer, Supabase Auth, Redis,
S3, SQS/DLQ, Textract, SSM/KMS, ECS Fargate, Cloudflare Tunnel e Terraform.
OpenRouter atende LLMs; OpenAI atende embeddings e voz; Microsoft Graph,
Escavador e JUIT são integrações externas. Edge Functions Deno são contingência.

## Saída real do `check.sh`

```text
[1/4] sintaxe
  backend: 277 arquivos Python válidos
  frontend (pulando: dependências ausentes; rode npm ci em frontend/)
[2/4] lint
All checks passed!
  frontend (pulando: dependências ausentes; rode npm ci em frontend/)
[3/4] testes
  backend (pulando: recurso tiktoken cl100k_base indisponível sem rede)
  frontend (pulando: dependências ausentes; rode npm ci em frontend/)
  fallback Deno (pulando: deno não instalado)
[4/4] segredo no código
  nenhum padrão de credencial encontrado
check.sh: ok
saida=0
```

## Etapas degradadas

- Sintaxe, análise estática e testes do frontend: `node_modules` não existe na
  cópia local e a máquina não permite instalar dependências pela rede.
- Testes do backend: a coleta exige o recurso `cl100k_base` do `tiktoken`; ele não
  está em cache e a rede está indisponível, portanto nenhum teste chega a rodar.
- Teste do fallback Deno: o executável `deno` não está instalado.

O backend teve os 277 arquivos Python analisados sintaticamente em memória e o
`ruff check .` foi executado com sucesso usando a `.venv` existente.

## Pendências

- Rodar o gate em ambiente com `npm ci`, Deno e o vocabulário `tiktoken` em cache
  para validar as suítes completas das duas metades.
- O repositório não identifica inequivocamente dono geral do produto nem revisor
  padrão de PR; somente responsabilidades operacionais específicas foram achadas.
- Os ADRs de confiabilidade do acervo e resultados tipados de ferramentas
  jurídicas, datados de 2026-08-12, aguardam aprovação de liderança.
