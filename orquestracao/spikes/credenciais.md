# Spike: Onde Cada CLI Guarda Credencial (Medição Linux e Roteiro Windows)

**Data:** 2026-09-02  
**Autor:** Nicolas (Engenharia de Esteira)  
**Status:** Concluído (Medição Linux realizada com prova; Roteiro Windows documentado)

---

## 1. Contexto e Princípios

Na arquitetura da Esteira, os agentes executam tarefas utilizando assinaturas individuais da equipe e modelos *free*. Conforme documentado em `esteira/contas.py`, `contas.yaml` e `README.md`:

1. **O repositório e os arquivos de configuração nunca contêm segredos**: `contas.yaml` apenas mapeia pessoas para diretórios de configuração (`config_dir`).
2. **Isolamento de diretório próprio da esteira**: O agente não utiliza o `~/.claude` ou `~/.codex` do dia a dia do desenvolvedor para evitar herdar *settings*, *hooks* e *plugins* não declarados.
3. **Segurança de credenciais**: Nenhuma credencial tem seu conteúdo exposto, lido ou impresso. Este documento relata localização, permissões, meio de armazenamento (*keyring* vs arquivo em disco), suporte a redirecionamento via variáveis de ambiente e sobrevivência a *reboot*.

---

## 2. Quadro Síntese (Medição no Linux)

| *Runtime* | CLI e Versão | Local Padrão da Credencial | Local Isolado na Esteira | Aceita Variável de Diretório? | Meio de Armazenamento | Sobrevive a *Reboot*? (Inferência) |
|---|---|---|---|---|---|---|
| `lead` | `claude` 2.1.258 | `~/.claude/.credentials.json` | `~/.esteira-auth/<pessoa>/claude/.credentials.json` | **Sim**: `CLAUDE_CONFIG_DIR` | Arquivo JSON (`0600`) | **Sim** (armazenado em `/home` em partição `ext4` persistente) |
| `codex` | `codex` 0.152.1 | `~/.codex/auth.json` | `~/.esteira-auth/<pessoa>/codex/auth.json` | **Sim**: `CODEX_HOME` | Arquivo JSON (`0600`) | **Sim** (armazenado em `/home` em partição `ext4` persistente) |
| `opencode` | `opencode` 1.18.25 | `~/.local/share/opencode/auth.json` | N/A (Usa *provider* *free* global / XDG) | **Não em `contas.py`** (Usa XDG Base Dir no sistema) | Arquivo JSON (`0600`) | **Sim** (armazenado em `/home` em partição `ext4` persistente) |
| `agy` | `agy` 1.1.24 | `~/.gemini/config/config.json` | N/A (Sem conta individual em `contas.py`) | **Não em `contas.py`** (Diretório fixo `~/.gemini`) | Arquivo JSON (`0600`) | **Sim** (armazenado em `/home` em partição `ext4` persistente) |

---

## 3. Medições Realizadas no Linux (Com Prova de Execução)

Abaixo constam os comandos executados no ambiente Linux e suas saídas literais, comprovando a existência de binários, permissões e diretórios de configuração sem jamais expor o conteúdo dos *tokens*.

### 3.1. Binários e Versões Instaladas

```bash
which claude codex opencode agy
```
Saída:
```text
/home/nicolas/.local/bin/claude
/home/nicolas/.nvm/versions/node/v24.18.0/bin/codex
/home/nicolas/.nvm/versions/node/v24.18.0/bin/opencode
/home/nicolas/.local/bin/agy
```

```bash
claude --version; codex --version; opencode --version; agy --version
```
Saída:
```text
2.1.258 (Claude Code)
codex-cli 0.152.1
1.18.25
1.1.24
```

---

### 3.2. Claude Code (`claude`)

- **Onde mora o *token*:** Arquivo `.credentials.json` dentro do diretório de configuração do usuário (`~/.claude/` por padrão, ou no diretório customizado apontado pela esteira).
- **Meio:** Arquivo em disco com permissões restritas `0600` (`-rw-------`). Não utiliza o *keyring* do sistema operacional no Linux.
- **Variável de diretório:** Aceita `CLAUDE_CONFIG_DIR`. Declarado em `esteira/contas.py` (`VAR_CONFIG["claude"] = "CLAUDE_CONFIG_DIR"`).
- **Sobrevivência a *reboot*:** **Sim** (inferência: gravado no disco persistente `/dev/nvme0n1p2`, montagem `ext4` em `/home/nicolas`, e não em sistema de arquivos volátil na memória RAM como `/tmp` ou `tmpfs`).

**Comando e Saída (Diretório Isolado da Esteira):**
```bash
ls -la ~/.esteira-auth/nicolas/claude/
```
Saída:
```text
total 72
drwx------ 5 nicolas nicolas  4096 ago 28 11:13 .
drwx------ 4 nicolas nicolas  4096 ago 28 11:04 ..
drwxrwxr-x 2 nicolas nicolas  4096 ago 28 11:13 backups
-rw------- 1 nicolas nicolas 36965 ago 28 11:13 .claude.json
-rw------- 1 nicolas nicolas  1886 ago 28 11:13 .credentials.json
-rw------- 1 nicolas nicolas   335 ago 28 11:13 policy-limits.json
drwxrwxr-x 3 nicolas nicolas  4096 ago 28 11:13 projects
-rw------- 1 nicolas nicolas    29 ago 28 11:13 remote-settings.json
drwx------ 2 nicolas nicolas  4096 ago 28 11:13 sessions
```

**Comando e Saída (Diretório Padrão do Host):**
```bash
ls -la ~/.claude/.credentials.json
```
Saída:
```text
-rw------- 1 nicolas nicolas 1034 set  2 08:45 /home/nicolas/.claude/.credentials.json
```

---

### 3.3. OpenAI Codex CLI (`codex`)

- **Onde mora o *token*:** Arquivo `auth.json` dentro do diretório `$CODEX_HOME` (`~/.codex/` por padrão ou diretório da esteira).
- **Meio:** Arquivo JSON em disco com permissões restritas `0600` (`-rw-------`). Não utiliza *keyring* do Linux por padrão.
- **Variável de diretório:** Aceita `CODEX_HOME`. Declarado em `esteira/contas.py` (`VAR_CONFIG["codex"] = "CODEX_HOME"`). O `--help` do binário referencia explicitamente `$CODEX_HOME`.
- **Sobrevivência a *reboot*:** **Sim** (inferência: gravado no disco persistente `/dev/nvme0n1p2`, sistema de arquivos `ext4`).

**Comando e Saída (Diretório Isolado da Esteira):**
```bash
ls -la ~/.esteira-auth/nicolas/codex/
```
Saída:
```text
total 7552
drwx------ 9 nicolas nicolas    4096 set  2 15:38 .
drwx------ 4 nicolas nicolas    4096 ago 28 11:04 ..
-rw------- 1 nicolas nicolas    4448 ago 28 11:13 auth.json
drwxrwxr-x 5 nicolas nicolas    4096 ago 28 11:36 cache
-rw------- 1 nicolas nicolas     216 ago 28 11:36 config.toml
-rw-r--r-- 1 nicolas nicolas   32768 ago 28 14:57 goals_1.sqlite
-rw-r--r-- 1 nicolas nicolas   32768 set  2 15:38 goals_1.sqlite-shm
-rw-r--r-- 1 nicolas nicolas   16512 set  2 15:38 goals_1.sqlite-wal
-rw-r--r-- 1 nicolas nicolas      36 ago 28 11:13 installation_id
-rw-r--r-- 1 nicolas nicolas   49152 set  2 15:38 logs_2.sqlite
-rw-r--r-- 1 nicolas nicolas   32768 set  2 15:38 logs_2.sqlite-shm
-rw-r--r-- 1 nicolas nicolas    4152 set  2 15:38 logs_2.sqlite-wal
-rw-r--r-- 1 nicolas nicolas   40960 ago 28 14:56 memories_1.sqlite
-rw-r--r-- 1 nicolas nicolas   32768 set  2 15:38 memories_1.sqlite-shm
-rw-r--r-- 1 nicolas nicolas    8272 set  2 15:38 memories_1.sqlite-wal
-rw-rw-r-- 1 nicolas nicolas  202809 set  2 15:38 models_cache.json
drwxrwxr-x 4 nicolas nicolas    4096 ago 28 11:13 plugins
-rw-r--r-- 1 nicolas nicolas   40960 ago 28 11:49 queue_1.sqlite
-rw-r--r-- 1 nicolas nicolas   32768 set  2 15:38 queue_1.sqlite-shm
-rw-r--r-- 1 nicolas nicolas   24752 set  2 15:38 queue_1.sqlite-wal
-rw------- 1 nicolas nicolas       3 ago 28 11:13 .sandbox_migration
drwxrwxr-x 3 nicolas nicolas    4096 ago 28 11:13 sessions
drwxrwxr-x 2 nicolas nicolas    4096 set  2 15:38 shell_snapshots
drwxrwxr-x 3 nicolas nicolas    4096 ago 28 11:13 skills
-rw-r--r-- 1 nicolas nicolas  286720 ago 28 14:57 state_5.sqlite
-rw-r--r-- 1 nicolas nicolas   32768 set  2 15:39 state_5.sqlite-shm
-rw-r--r-- 1 nicolas nicolas 3654472 set  2 15:39 state_5.sqlite-wal
-rw-r--r-- 1 nicolas nicolas 1241088 ago 28 14:57 thread_history_1.sqlite
-rw-r--r-- 1 nicolas nicolas   32768 set  2 15:39 thread_history_1.sqlite-shm
-rw-r--r-- 1 nicolas nicolas 1845792 set  2 15:39 thread_history_1.sqlite-wal
drwxrwxr-x 2 nicolas nicolas    4096 set  2 15:38 thread-writer-locks
drwxrwxr-x 3 nicolas nicolas    4096 ago 28 11:13 tmp
```

**Comando e Saída (Diretório Padrão do Host):**
```bash
ls -la ~/.codex/auth.json
```
Saída:
```text
-rw------- 1 nicolas nicolas 4448 ago 26 17:31 /home/nicolas/.codex/auth.json
```

---

### 3.4. OpenCode (`opencode`)

- **Onde mora o *token* e configuração:**
  - Configuração: `~/.config/opencode/opencode.jsonc` (especificação `$XDG_CONFIG_HOME`).
  - Autenticação e estado: `~/.local/share/opencode/auth.json` (especificação `$XDG_DATA_HOME`).
- **Meio:** Arquivo JSON em disco com permissões `0600`.
- **Variável de diretório:** **Não possui variável em `contas.py`**. O OpenCode roda na esteira sem conta individual (apenas modelos *free* declarados via linha de comando `-m opencode/mimo-v2.5-free`).
- **Sobrevivência a *reboot*:** **Sim** (inferência: arquivos sob `/home/nicolas/.local/share` e `/home/nicolas/.config` em partição `ext4`).

**Comando e Saída (Autenticação e Dados):**
```bash
ls -la ~/.local/share/opencode/auth.json
```
Saída:
```text
-rw------- 1 nicolas nicolas 124 ago 14 11:26 /home/nicolas/.local/share/opencode/auth.json
```

**Comando e Saída (Configuração):**
```bash
ls -la ~/.config/opencode/opencode.jsonc
```
Saída:
```text
-rw-rw-r-- 1 nicolas nicolas 1246 ago 14 11:40 /home/nicolas/.config/opencode/opencode.jsonc
```

---

### 3.5. Antigravity CLI (`agy`)

- **Onde mora o *token* e configuração:**
  - Configurações da CLI: `~/.gemini/antigravity-cli/settings.json`.
  - Configurações globais e autenticação: `~/.gemini/config/config.json`.
- **Meio:** Arquivos JSON em disco com permissões restritas `0600`.
- **Variável de diretório:** **Não possui variável em `contas.py`**. Não há mapeamento de conta individual para `agy` no ecossistema da esteira.
- **Sobrevivência a *reboot*:** **Sim** (inferência: diretório `~/.gemini` gravado em partição persistente `ext4`).

**Comando e Saída:**
```bash
ls -la ~/.gemini/config/config.json ~/.gemini/antigravity-cli/settings.json
```
Saída:
```text
-rw------- 1 nicolas nicolas 2986 ago 29 11:37 /home/nicolas/.gemini/antigravity-cli/settings.json
-rw------- 1 nicolas nicolas   89 ago 26 18:43 /home/nicolas/.gemini/config/config.json
```

---

### 3.6. Comprovação de Persistência em Disco (Partição e Ponto de Montagem)

Para sustentar a inferência de que os arquivos sobrevivem a *reboot*, verificou-se o sistema de arquivos onde residem:

```bash
df -T ~/.esteira-auth/ ~/.claude/ ~/.codex/ ~/.local/share/opencode/ ~/.gemini/
```
Saída:
```text
Sist. Arq.     Tipo Blocos de 1K     Usado Disponível Uso% Montado em
/dev/nvme0n1p2 ext4    490617784 140805788  324816516  31% /
/dev/nvme0n1p2 ext4    490617784 140805788  324816516  31% /
/dev/nvme0n1p2 ext4    490617784 140805788  324816516  31% /
/dev/nvme0n1p2 ext4    490617784 140805788  324816516  31% /
/dev/nvme0n1p2 ext4    490617784 140805788  324816516  31% /
```

---

## 4. O Desenho Arquitetural do Nó Windows

### 4.1. O Problema Fundamental: *Keyring*, DPAPI e a Conta `SYSTEM`

No Windows, ferramentas de linha de comando frequentemente utilizam o **Windows Credential Manager** (*Gerenciador de Credenciais*) através da **DPAPI** (*Data Protection API*), ou salvam dados sob `%USERPROFILE%` / `%APPDATA%`.

A criptografia da DPAPI atrela as chaves à senha e ao SID (*Security Identifier*) do usuário interativo (`%APPDATA%\Microsoft\Protect\{SID}`).

**Consequência arquitetural crítica:**
- Um serviço Windows padrão rodando sob a conta **`NT AUTHORITY\SYSTEM`** (ou `LocalSystem`):
  1. **Não possui acesso às chaves DPAPI do usuário humano**, sendo incapaz de descriptografar qualquer *token* guardado no Credential Manager do usuário.
  2. O `%USERPROFILE%` do `SYSTEM` aponta para `C:\Windows\System32\config\systemprofile`, onde as credenciais dos CLIs instalados e logados pelo desenvolvedor simplesmente não existem.
  3. Serviços rodando sob `SYSTEM` não conseguem interagir com o *keyring* do usuário.

---

### 4.2. Conclusão por *Runtime* no Windows

1. **`claude` no Windows:**
   - **Comportamento esperado:** Se o login foi feito pelo usuário, as credenciais residem em `%USERPROFILE%\.claude\.credentials.json` ou no Credential Manager via DPAPI. Redirecionar com `CLAUDE_CONFIG_DIR=C:\Users\<user>\.esteira-auth\<pessoa>\claude` apontará para arquivos de credenciais criados no contexto daquele usuário.
   - **Veredito:** `SYSTEM` falhará por incompatibilidade de perfil e DPAPI. **Exige execução sob o usuário.**

2. **`codex` no Windows:**
   - **Comportamento esperado:** Utiliza `%USERPROFILE%\.codex\auth.json` ou `%CODEX_HOME%`. Se o *loader* nativo do Codex no Windows interagir com o *keytar* / Credential Manager nativo, `SYSTEM` não terá acesso.
   - **Veredito:** Mesmo com `$env:CODEX_HOME` configurado, um serviço `SYSTEM` não tem o ambiente de chaves do usuário. **Exige execução sob o usuário.**

3. **`opencode` no Windows:**
   - **Comportamento esperado:** Localiza arquivos em `%APPDATA%\opencode` e `%LOCALAPPDATA%\opencode\auth.json`. Não possui variável de *config-dir* mapeada em `contas.py`.
   - **Veredito:** `SYSTEM` aponta para `%LOCALAPPDATA%` do sistema (`systemprofile`), que estará vazio ou sem permissões de rede/chave. **Exige execução sob o usuário.**

4. **`agy` no Windows:**
   - **Comportamento esperado:** Configurações e sessões em `%USERPROFILE%\.gemini\antigravity-cli`. Sem variável de *config-dir* em `contas.py`.
   - **Veredito:** O processo precisa do `%USERPROFILE%` do desenvolvedor autenticado. `SYSTEM` quebra a resolução do perfil. **Exige execução sob o usuário.**

### 4.3. Decisão de Desenho para o Nó Windows

> **Decisão:** O nó de execução / *worker* no Windows **NÃO pode rodar como serviço padrão sob a conta `SYSTEM`**. Ele deve ser configurado obrigatoriamente como uma **Tarefa Agendada (*Scheduled Task*) do Windows** configurada com a opção *"Executar somente quando o usuário estiver conectado"* (ou configurada para rodar com as credenciais do usuário da esteira), ou executado diretamente em uma sessão interativa de segundo plano (*background worker* sob a conta de usuário).

---

## 5. Roteiro de Medição para Máquina Windows

Quando uma máquina Windows estiver disponível, este roteiro deve ser executado no PowerShell (executado como usuário normal, **não** como Administrador/SYSTEM) para medir e preencher a tabela real.

### 5.1. Passo 1 — Identificação dos Executáveis e Versões

Executar no PowerShell:

```powershell
# 1. Localizar executáveis
Get-Command claude, codex, opencode, agy | Select-Object Name, Source

# 2. Versões instaladas
claude --version
codex --version
opencode --version
agy --version
```

### 5.2. Passo 2 — Localização dos Arquivos de Credenciais e Configuração

Executar no PowerShell:

```powershell
# Claude Code
Get-ChildItem -Path "$env:USERPROFILE\.claude" -Force
Get-ChildItem -Path "$env:USERPROFILE\.esteira-auth\*\claude" -Force -ErrorAction SilentlyContinue

# OpenAI Codex
Get-ChildItem -Path "$env:USERPROFILE\.codex" -Force
Get-ChildItem -Path "$env:USERPROFILE\.esteira-auth\*\codex" -Force -ErrorAction SilentlyContinue

# OpenCode
Get-ChildItem -Path "$env:APPDATA\opencode" -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "$env:LOCALAPPDATA\opencode" -Force -ErrorAction SilentlyContinue

# Antigravity CLI
Get-ChildItem -Path "$env:USERPROFILE\.gemini" -Force -Recurse -Depth 2 -ErrorAction SilentlyContinue
```

*Atenção:* **Nunca use `Get-Content`, `type` ou `cat` nos arquivos `.json` ou de credencial.** Apenas inspecione nomes, tamanhos e permissões com `Get-ChildItem` e `Get-Acl`.

### 5.3. Passo 3 — Verificação do Windows Credential Manager (*Keyring*)

Executar no Prompt de Comando / PowerShell para verificar se algum CLI registrou segredos no cofre do Windows:

```powershell
cmdkey /list
```
*O que observar:* Verificar se há entradas associadas a `Claude`, `Anthropic`, `OpenAI`, `Codex`, `OpenCode` ou `Google/Gemini`.

### 5.4. Passo 4 — Teste de Redirecionamento de Variáveis no Windows

Executar no PowerShell para confirmar se as variáveis de ambiente redirecionam corretamente as pastas de configuração:

```powershell
# Teste de Claude com CLAUDE_CONFIG_DIR
$env:CLAUDE_CONFIG_DIR = "$env:USERPROFILE\.esteira-auth\teste\claude"
claude doctor

# Teste de Codex com CODEX_HOME
$env:CODEX_HOME = "$env:USERPROFILE\.esteira-auth\teste\codex"
codex doctor
```

### 5.5. Tabela de Resultados Windows (Template para Preenchimento)

*(Esta tabela deverá ser preenchida exclusivamente após a execução real em máquina Windows)*

| *Runtime* | Caminho do Executável | Caminho do Arquivo / Entrada no Credential Manager | Aceita Variável de Diretório? | Armazenamento (Arquivo vs DPAPI/Keyring) | Funciona sob `SYSTEM`? | Funciona sob Tarefa Agendada de Usuário? |
|---|---|---|---|---|---|---|
| `claude` | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* |
| `codex` | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* |
| `opencode` | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* |
| `agy` | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* | *(preencher)* |

---

## 6. O Que Não Deu Para Medir

Neste ambiente Linux não foi possível realizar as seguintes verificações, que dependem estritamente do acesso a uma máquina Windows:

1. **Uso efetivo da DPAPI / Windows Credential Manager:** Não é possível atestar sem um sistema Windows se as versões de distribuição Windows dos pacotes Node (`@openai/codex`, `@anthropic-ai/claude-code`, etc.) compilam dependências como `keytar` para descarregar *tokens* diretamente no Credential Manager do Windows em vez de gravá-los em arquivos `.json` no disco.
2. **Resolução de caminhos com separadores Windows (`\` vs `/`):** Se os CLIs tratam caminhos absolutos no formato Windows (ex: `C:\Users\nome\.esteira-auth\...`) de forma transparente em `CLAUDE_CONFIG_DIR` e `CODEX_HOME`.
3. **Comportamento exato sob a conta `SYSTEM` vs Tarefa Agendada no Windows:** A validação prática da falha de autorização ao tentar rodar `claude` ou `codex` sob uma sessão de serviço `SYSTEM` (via `psexec -s` ou *Service Control Manager*) versus uma Tarefa Agendada no *Task Scheduler* vinculada ao usuário logado.
