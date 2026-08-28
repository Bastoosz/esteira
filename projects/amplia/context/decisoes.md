# Decisões

> *Append-only*, datado. Nunca reescreva histórico — acrescente a decisão nova
> dizendo que substitui a antiga. Teto: 200 linhas; ao passar, compacta.

- `2026-06` — O backend nativo na AWS passou a ser o caminho primário. FastAPI
  atende fluxos assíncronos, SSE, RAG e IA; Django atende administração e
  migrações. A mudança remove o limite de 60 segundos das Edge Functions,
  suporta processamento pesado e concentra segurança e observação.
- `2026-06` — As Edge Functions Supabase em Deno permaneceram somente como
  contingência do chat. O frontend tenta esse caminho em falhas 5xx da API AWS;
  evoluções novas devem mirar o backend primário.
- `2026-06` — SQS substituiu MSK/Kafka como barramento de eventos. Filas e DLQs
  por tipo de evento atendem o volume do produto e removeram cerca de US$ 410/mês
  de custo-base ocioso documentado.
- `2026-06` — O acervo usa envio direto do navegador ao S3 por URL assinada; OCR,
  extração e embeddings seguem por *workers*. Isso evita transferir arquivos de
  até 150 MB pela API e isola processamento pesado.
- `2026-06` — A recuperação usa Postgres + pgvector com busca textual PT-BR e
  vetorial, fundidas por RRF. Modos adaptativos e etapas condicionais equilibram
  latência, cobertura e custo.
- `2026-06` — O Postgres opera atrás de PgBouncer em modo transacional. Os clientes
  desativam *prepared statements* (`prepare_threshold=None` no psycopg e
  `statement_cache_size=0` no asyncpg) para evitar colisões sob carga.
- `2026-06` — O Supabase permaneceu responsável por autenticação JWT e banco
  Postgres gerenciado, embora a execução principal tenha migrado para AWS.
- `2026-06` — Reconhecimento facial, controle por gestos e projeção remota foram
  retirados com o protótipo. Não fazem parte do produto ativo em
  `frontend/src/amplia/`.
- `2026-07` — Tokens Microsoft delegados passaram a ser armazenados cifrados no
  backend, com envelope KMS e renovação no servidor. O frontend não deve enviar
  `X-Microsoft-Token`, reduzindo exposição de credenciais no cliente.
- `2026-07` — O fluxo de publicação do backend executa migração Alembic antes da
  atualização gradual do ECS e usa *circuit breaker* com reversão, impedindo que
  código novo suba sobre esquema incompatível.
