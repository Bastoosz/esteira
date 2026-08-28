"""
Registro de contas de assinatura, seleção e atribuição.

Princípios:
  - o arquivo contas.yaml NÃO tem segredo, só caminho de config dir
  - o agente nunca vê credencial; recebe só a variável que aponta o dir
  - toda execução registra em qual conta rodou (atribuição no board)
  - rodízio existe, mas vem DESLIGADO. Ver POLITICA_CONTA em config.py
"""
import time, json
from pathlib import Path
import yaml
import config

COOLDOWN_S = 30 * 60          # conta que falhou fica de molho
ESTADO = config.LOGS_DIR / "contas-estado.json"

# Cada runtime guarda auth num lugar diferente.
VAR_CONFIG = {"claude": "CLAUDE_CONFIG_DIR", "codex": "CODEX_HOME"}
# Qual tier usa qual tipo de conta
TIER_CONTA = {"lead": "claude", "codex": "codex"}


def _registro():
    p = config.BASE_DIR / "contas.yaml"
    if not p.exists():
        return {"pessoas": [], "compartilhadas": {}}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _estado():
    if ESTADO.exists():
        try:
            return json.loads(ESTADO.read_text())
        except json.JSONDecodeError:
            pass
    return {"cooldown": {}, "ultimo_uso": {}, "contador": {}}


def _salvar(e):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(e, indent=2), encoding="utf-8")


def disponiveis(tipo):
    """Contas ativas daquele tipo que não estão de molho."""
    e = _estado()
    agora = time.time()
    out = []
    for p in _registro().get("pessoas", []):
        c = (p.get("contas") or {}).get(tipo) or {}
        if not c.get("ativo"):
            continue
        chave = f"{p['id']}:{tipo}"
        if e["cooldown"].get(chave, 0) > agora:
            continue
        out.append({
            "chave": chave, "pessoa_id": p["id"], "nome": p.get("nome", p["id"]),
            "email": p.get("email", ""), "tipo": tipo,
            "config_dir": str(Path(c["config_dir"]).expanduser()),
        })
    return out


def escolher(tier, dono_id=None):
    """
    POLITICA_CONTA:
      "dona"    a conta do dono da demanda (padrão, defensável, atribuível)
      "fixa"    sempre CONTA_FIXA
      "rodizio" round-robin — só ligue depois de confirmar os termos
    """
    tipo = TIER_CONTA.get(tier)
    if tipo is None:
        return None                        # opencode / agy / free: sem conta individual

    livres = disponiveis(tipo)
    if not livres:
        raise RuntimeError(
            f"nenhuma conta '{tipo}' ativa e fora de cooldown. "
            f"Autentique alguma e marque ativo: true em contas.yaml"
        )

    pol = config.POLITICA_CONTA
    if pol == "fixa":
        alvo = config.CONTA_FIXA
        return next((c for c in livres if c["pessoa_id"] == alvo), livres[0])

    if pol == "dona" and dono_id:
        achou = next((c for c in livres if c["pessoa_id"] == dono_id), None)
        if achou:
            return achou
        # dono sem conta ativa: cai para a menos usada, e o board mostra isso
    e = _estado()
    livres.sort(key=lambda c: e["ultimo_uso"].get(c["chave"], 0))
    return livres[0]


def marcar_uso(conta):
    if not conta:
        return
    e = _estado()
    e["ultimo_uso"][conta["chave"]] = time.time()
    e["contador"][conta["chave"]] = e["contador"].get(conta["chave"], 0) + 1
    _salvar(e)


def cooldown(conta, motivo="", segundos=COOLDOWN_S):
    if not conta:
        return
    e = _estado()
    e["cooldown"][conta["chave"]] = time.time() + segundos
    _salvar(e)
    with (config.LOGS_DIR / "contas.log").open("a", encoding="utf-8") as f:
        f.write(f"{time.time()} cooldown {conta['chave']} {segundos}s :: {motivo}\n")


def env_para(conta):
    """A única coisa que vai para o processo: o caminho do config dir."""
    if not conta:
        return {}
    var = VAR_CONFIG.get(conta["tipo"])
    return {var: conta["config_dir"]} if var else {}


def resumo():
    """Para o board: quem está ativo, quantas execuções, quem está de molho."""
    e = _estado()
    agora = time.time()
    linhas = []
    for p in _registro().get("pessoas", []):
        for tipo, c in (p.get("contas") or {}).items():
            chave = f"{p['id']}:{tipo}"
            cd = e["cooldown"].get(chave, 0)
            linhas.append({
                "pessoa": p.get("nome", p["id"]), "tipo": tipo,
                "ativo": bool(c.get("ativo")),
                "execucoes": e["contador"].get(chave, 0),
                "em_cooldown": cd > agora,
                "cooldown_ate": int(cd - agora) if cd > agora else 0,
            })
    return linhas
