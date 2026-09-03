# Ferramentas e serviços externos

Cada API e serviço que esta esteira usa, com dono, utilidade, onde a chave
vive e o que acontece se cair.

## Runtimes de agente

| Ferramenta | Dono | Para que serve | Onde a chave vive | Se cair |
|---|---|---|---|---|
| *Claude Code* | Anthropic (assinatura da equipe) | Agente líder: planeja, integra, revisa | Diretório local de autenticação do CLI; política de contas em `config.py` → `POLITICA_CONTA` | Demanda fica sem líder — nenhuma execução de agente roda |
| *Codex* | OpenAI (assinatura da equipe) | Implementação alternativa e revisão cruzada | Diretório local de autenticação do CLI; política de contas em `config.py` | Perde revisão cruzada e alternativa de implementação |
| *OpenCode* | Comunidade (*open source*) | Sub-tasks pequenas, com modelo free | `OPENROUTER_API_KEY` em variável de ambiente (via `.env`); modelo em `CMD_OPENCODE` | Sub-tasks pequenas ficam sem executor; `agy` cobre como reserva |
| *Antigravity* (*agy*) | Comunidade (*open source*) | Sub-tasks pequenas, com modelo free | `OPENROUTER_API_KEY` em variável de ambiente; CLI invocado por `CMD_AGY` | Sub-tasks pequenas ficam sem executor; `opencode` cobre como reserva |

## LLM via API

| Ferramenta | Dono | Para que serve | Onde a chave vive | Se cair |
|---|---|---|---|---|
| *OpenRouter* (só modelos *free*) | OpenRouter Inc. | LLM direto para texto puro (sem agente): classificação, extração, JSON. NUNCA modelo pago. | `OPENROUTER_API_KEY` em variável de ambiente; lista de ids em `config.py` → `MODELOS_FREE` | `esteira/llm.py` falha em todas as tentativas — tarefas de texto puro ficam sem resposta |

## Automação e *workflow*

| Ferramenta | Dono | Para que serve | Onde a chave vive | Se cair |
|---|---|---|---|---|
| *n8n* | Instância local (self-hosted) | Secretária: monta e-mail, manda, escuta resposta, entrega no worker. Quatro fluxos: comms-out, comms-in, intake, digest | Webhook local em `N8N_COMM_URL` (localhost:5678); sem credencial externa — roda na máquina | E-mails não saem, respostas não chegam, demandas não entram, digest diário não dispara |

## Integrações Microsoft

| Ferramenta | Dono | Para que serve | Onde a chave vive | Se cair |
|---|---|---|---|---|
| *Microsoft Graph* (*Outlook*) | Andrade Maia (assinatura Microsoft 365) | Enviar/ler e-mails da caixa da esteira; trigger de novas mensagens no *n8n* | Credencial no *n8n* (variáveis de ambiente do *workflow* — não versionadas) | E-mails não saem nem chegam; fluxos F1, F2 e F3 do *n8n* falham |
| *Microsoft Teams* | Andrade Maia (assinatura Microsoft 365) | Cards de notificação e alerta para a equipe | Credencial no *n8n* (variáveis de ambiente do *workflow*) | Equipe não recebe alertas visuais; fluxos F1 e F3 perdem notificação |

## Integrações jurídicas

| Ferramenta | Dono | Para que serve | Onde a chave vive | Se cair |
|---|---|---|---|---|
| *Escavador* | Escavador (API externa) | Consulta processual e jurisprudência — integrado ao AMPLIA | Credencial no AMPLIA (`backend/.env`) — *inferência* baseada em `projects/amplia/AGENTS.md` | AMPLIA perde busca processual; consulta jurídica fica cega |
| *JUIT* | JUIT (API externa) | Pesquisa jurídica e acervo — integrado ao AMPLIA | Credencial no AMPLIA (`backend/.env`) — *inferência* baseada em `projects/amplia/AGENTS.md` | AMPLIA perde acesso a jurisprudência e acervo |

## Infraestrutura e hospedagem

| Ferramenta | Dono | Para que serve | Onde a chave vive | Se cair |
|---|---|---|---|---|
| *AWS* (S3, SQS, ECS Fargate, *Textract*, SSM/KMS) | Andrade Maia (conta AWS) | Backend do AMPLIA: armazenamento, filas, computação, OCR, segredos | Credenciais no AMPLIA (`backend/.env`); infra descrita em Terraform | AMPLIA inteiro fica indisponível |
| *Vercel* | Andrade Maia (conta Vercel) | Hospedagem do *frontend* do AMPLIA (SPA React) | *Deploy* automático via GitHub; variáveis no painel da Vercel — *inferência* | AMPLIA perde interface web |
| *Supabase* (Auth, Postgres, pgvector) | Andrade Maia (conta Supabase) | Autenticação, banco de dados e busca vetorial do AMPLIA | Credenciais no AMPLIA (`backend/.env`) — *inferência* baseada em `projects/amplia/AGENTS.md` | AMPLIA perde auth e banco |
| *Redis* | Andrade Maia (instância local ou cloud) | Cache e fila de mensagens do AMPLIA | Credencial no AMPLIA (`backend/.env`) — *inferência* | AMPLIA perde cache; performance degrada |
| *OpenAI* (embeddings e voz) | OpenAI (API paga) | Geração de embeddings e processamento de voz no AMPLIA | Credencial no AMPLIA (`backend/.env`) — *inferência* baseada em `projects/amplia/AGENTS.md` | AMPLIA perde RAG e funcionalidade de voz |

## Outros

| Ferramenta | Dono | Para que serve | Onde a chave vive | Se cair |
|---|---|---|---|---|
| *GitHub* | Andrade Maia (organização GitHub) | Versionamento, *branches* de demanda, PRs, *deploy* via CI | Token local ou *deploy key* — *inferência* | *Deploy* automático para; branches de demanda não sobem |

## O que não deu para confirmar

- **Dono de cada ferramenta:** o repositório não mapeia quem é responsável
  por cada serviço. Os nomes de responsáveis do AMPLIA (Mickel Baptista,
  Stefan Gagliotti) aparecem em `projects/amplia/AGENTS.md` para operação
  de backend/DLQ e segurança, mas não para todas as ferramentas listadas.
- **Credenciais do *n8n*:** os fluxos do *n8n* usam credenciais Microsoft
  Graph e Teams, mas o README não detalha onde vivem as *tokens* — apenas
  que são variáveis de ambiente do *workflow*.
- **Contas AWS, Vercel, Supabase:** confirmadas por inferência a partir de
  `projects/amplia/AGENTS.md`. Não há arquivo de configuração da esteira
  que detalhe essas integrações.
- **GitHub:** inferido pela existência de `config.py` → `GIT_REMOTE` e pelo
  fluxo de *branches* descrito em `AGENTS.md`. Não há documentação explícita
  de autenticação.
- **Valor mensal de cada assinatura:** não disponível no repositório.
