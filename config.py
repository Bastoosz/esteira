"""
Esteira — configuração.
Tudo que se ajusta fica aqui, no topo, com fallback para variável de ambiente.
"""
import os
from pathlib import Path

# === Caminhos ===
BASE_DIR = Path(__file__).resolve().parent
DEMANDS_DIR = BASE_DIR / "demands"
WORKSPACE_DIR = BASE_DIR / "workspace"
PROJECTS_DIR = BASE_DIR / "projects"
PAPEIS_DIR = BASE_DIR / "papeis"
LOGS_DIR = BASE_DIR / "logs"

# === n8n ===
# O agente e o worker só falam com o n8n por aqui. Localhost: sem porta aberta.
N8N_COMM_URL = os.getenv("N8N_COMM_URL", "http://localhost:5678/webhook/esteira-comm")
WORKER_BASE_URL = os.getenv("WORKER_BASE_URL", "http://localhost:5000")

# === Board ===
BOARD_PORT = int(os.getenv("BOARD_PORT", 5000))
BOARD_SENHA = os.getenv("BOARD_SENHA", "")  # vazio = sem senha (só rede local)
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# === Limites ===
# Assinatura é fixa: o que limita é turno, tempo e rodada — não dinheiro.
MAX_TURNOS = int(os.getenv("MAX_TURNOS", 60))
TIMEOUT_RODADA_S = int(os.getenv("TIMEOUT_RODADA_S", 45 * 60))
TIMEOUT_SUBTASK_S = int(os.getenv("TIMEOUT_SUBTASK_S", 10 * 60))
MAX_RODADAS = int(os.getenv("MAX_RODADAS", 5))
MAX_TENTATIVAS_MESMO_ERRO = 3

# === Vigia ===
VIGIA_INTERVALO_S = 120
SEM_SINAL_ALERTA_S = 10 * 60      # journal parado com processo vivo
SEM_ARQUIVO_ALERTA_S = 15 * 60    # nada escrito no workspace

# === Worker ===
WORKER_INTERVALO_S = 60
DEMANDAS_SIMULTANEAS = 1          # 2-3 demandas/semana. Uma por vez basta.

# === Códigos de saída dos comandos do agente ===
EXIT_OK = 0
EXIT_ASK = 42        # agente perguntou; execução pausa
EXIT_BLOQUEADO = 43  # falta credencial/acesso externo

# === Runtimes de agente ===
# Assinaturas Claude e Codex. Antigravity e OpenCode para sub-task.
# PROIBIDO: OpenRouter pago para rodar agente.
# {prompt_file} e {cwd} são substituídos pelo runner.
RUNTIMES = {
    "lead": {
        "cmd": os.getenv("CMD_LEAD", "claude -p --output-format stream-json"),
        "stdin_prompt": True,
        "descricao": "Claude Code — planeja, integra, revisa",
    },
    "codex": {
        "cmd": os.getenv("CMD_CODEX", "codex exec"),
        "stdin_prompt": True,
        "descricao": "Codex — implementação alternativa, revisão cruzada",
    },
    "opencode": {
        "cmd": os.getenv("CMD_OPENCODE", "opencode run"),
        "stdin_prompt": True,
        "descricao": "OpenCode com modelo free — sub-tasks pequenas",
        # Reclama de crédito e mesmo assim trabalha. Código de saída não
        # vale nada aqui: o veredito é o que mudou no disco.
        "exit_confiavel": False,
    },
    "agy": {
        # PREENCHER: comando headless do Antigravity no ambiente de vocês.
        "cmd": os.getenv("CMD_AGY", ""),
        "stdin_prompt": True,
        "descricao": "Antigravity — sub-tasks pequenas",
        "exit_confiavel": False,
    },
    "orca": {
        # PREENCHER se for usar o Orca como runtime headless (orca serve).
        # Orca é um ADE de desktop; confirme a invocação sem interface antes.
        "cmd": os.getenv("CMD_ORCA", ""),
        "stdin_prompt": True,
        "descricao": "Orca — orquestra outros CLIs em worktrees",
        "exit_confiavel": True,
    },
}
# Runtimes sem código de saída confiável: julgue pelo disco, não pelo exit.
EXIT_CONFIAVEL_PADRAO = True

# === Pre-flight ===
# Checklist fixo. Qualquer "sim"/"talvez" gera e-mail ANTES de começar.
PREFLIGHT_PERGUNTAS = [
    ("credencial", "precisa de credencial ou acesso que não está no projeto?"),
    ("certificado", "precisa de certificado digital?"),
    ("pagamento", "precisa de conta paga, assinatura ou serviço novo?"),
    ("externo", "depende de sistema externo (tribunal, PJe, Escavador)?"),
    ("juridico", "envolve prazo, intimação, contagem de dias ou valor devido?"),
    ("advogado", "depende de regra que só um advogado sabe responder?"),
]

# === Git ===
GIT_REMOTE = os.getenv("GIT_REMOTE", "origin")
GIT_BRANCH_PREFIX = "agent/"


# === Contas de assinatura da equipe ===
# "dona"    a demanda roda na conta do próprio dono (padrão)
# "fixa"    tudo numa conta só — mais simples para começar
# "rodizio" round-robin entre as contas ativas.
#           NÃO LIGUE antes de confirmar os termos das assinaturas.
POLITICA_CONTA = os.getenv("POLITICA_CONTA", "dona")
CONTA_FIXA = os.getenv("CONTA_FIXA", "joao")

# Smoke test de autenticação, por conta. Auth expirando em silêncio é a
# forma número um deste setup morrer sem ninguém perceber.
SMOKE_INTERVALO_S = 60 * 60

# === Modelos free (OpenRouter) para tarefas de texto puro ===
# Só ids com sufixo ':free'. esteira/llm.py recusa qualquer outro.
# Free model muda de nome e sai do ar — confira a lista atual antes de usar.
MODELOS_FREE = [
    m.strip() for m in os.getenv(
        "MODELOS_FREE",
        "meta-llama/llama-3.3-70b-instruct:free,"
        "qwen/qwen-2.5-72b-instruct:free,"
        "google/gemma-2-9b-it:free"
    ).split(",") if m.strip()
]
