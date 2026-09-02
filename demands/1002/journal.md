# Journal — demanda 1002

- `2026-09-02T15:39:19` **sistema** — demanda criada
- `2026-09-02T15:40:00` **preparação** — plano registrado antes do pre-flight para explicitar abordagem e premissas
- `2026-09-02T15:40:01` **preparação** — iniciando o pre-flight diretamente para chegar a PRONTA sem disparar uma rodada do worker
- `2026-09-02T15:40:00` **sistema** — NOVA -> PRE_FLIGHT (preparação segura sem executar o worker)
- `2026-09-02T15:40:00` **pre-flight** — falhou (OPENROUTER_API_KEY não definida); assumindo 'talvez' em tudo
- `2026-09-02T15:40:00` **pre-flight** — [nenhum] alertas: credencial, certificado, pagamento, externo, juridico, advogado
- `2026-09-02T15:40:00` **sistema** — PRE_FLIGHT -> PRONTA (pre-flight concluído; pronta para prova do ciclo)
- `2026-09-02T15:41:00` **preparação** — documentando a prova antes de validar a fila para que o ciclo seja repetível sem corrida de estado
- `2026-09-02T15:42:00` **preparação** — removendo jq do roteiro porque a ferramenta não existe nesta máquina; a prova usará apenas Python e utilitários presentes
