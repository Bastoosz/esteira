# T-03 — Units systemd do worker, vigia e sentinela

## O que foi feito

Criados em `deploy/`:

| Arquivo | Tipo | Descrição |
|---|---|---|
| `esteira-worker.service` | Service (simple) | Loop infinito que processa demandas da fila |
| `esteira-vigia.service` | Service (simple) | Loop infinito que monitora workers travados |
| `esteira-smoke.service` | Service (oneshot) | Sentinela — smoke test periódico dos runtimes |
| `esteira-smoke.timer` | Timer | Dispara a sentinela a cada hora |
| `README.md` | Doc | Instruções de instalação |

## O que NÃO foi feito

- Nenhum arquivo fora de `deploy/` foi editado.
- `.env`, `config.py`, `esteira/**`, `demands/**`, `bin/**` intocados.

## O que foi assumido

1. **Symlink em `/home/nicolas/bin/esteira-venv-python`** — `systemd-analyze verify` não expande variáveis no `ExecStart` e rejeita caminhos com espaço. Criado symlink em local sem espaço que aponta para `.venv/bin/python`. Se o nó mudar (atualização do venv), o symlink precisa ser recriado.

2. **Servço de usuário** — todos os units usam `systemctl --user`. A credencial dos CLIs (`~/.esteira-auth/`) pertence ao usuário; serviço de sistema não alcançaria.

3. **`EnvironmentFile=-`** (com `-` prefix) — o serviço não morre se `.env` faltar.

4. **`PATH` explícito** — inclui `/home/nicolas/.nvm/versions/node/v24.18.0/bin` (onde `codex` e `opencode` vivem), `/home/nicolas/.local/bin` (onde `claude` e `agy` estão), e os padrões `/usr/local/bin:/usr/bin:/bin`.

5. **Sentinela como onshot** — `--uma-vez` é passado como argumento. O módulo pode não existir quando o verify roda, mas o verify checa sintaxe do unit, não existência do módulo.

6. **Sem `WatchdogSec`** — o código não usa `sd_notify`, então watchdog mataria o worker sem motivo.

## O que quebrou

Nada. Todos os 4 units passam no `systemd-analyze verify` com código 0 e sem aviso.

## Saída do verify

```
--- esteira-smoke.service ---
saida=0
--- esteira-vigia.service ---
saida=0
--- esteira-worker.service ---
saida=0
--- esteira-smoke.timer ---
saida=0
```
