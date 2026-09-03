"""
Reporte ao hub — best-effort, com fila local.

REGRA QUE GOVERNA ESTE ARQUIVO

    Hub fora do ar NÃO derruba execução.

O estado da demanda vive em git; o hub é telemetria. Telemetria que derruba
o trabalho que ela mede é pior que telemetria nenhuma. O padrão é o mesmo da
`esteira/sentinela.py`, que em 02/09 tentou falar com o n8n desligado,
tratou a falha e saiu 0 — e o mesmo do `comm.enviar`, que já dizia
"falha de envio não pode derrubar a execução. O estado já está no disco".

O que muda aqui: o dado não se perde, só atrasa. Quem não foi entregue cai
numa fila local em jsonl e é reenviado no próximo `drenar()`.

NADA DE SEGREDO SAI DAQUI. O payload é filtrado por lista de permissão, não
por lista de proibição — chave nova que apareça no dicionário de origem não
vaza por esquecimento.
"""
import json, os, time
from pathlib import Path

import config

# Lista de PERMISSÃO. Campo que não está aqui não é enviado, e é assim de
# propósito: com lista de proibição, um campo novo no dicionário de origem
# vazaria até alguém lembrar de proibi-lo.
CAMPOS = (
    "pessoa", "runtime", "tier", "task_id", "demanda", "cwd",
    "duracao_s", "codigo", "timeout", "exit_confiavel",
    "arquivos_mudados", "log_bytes", "veredito",
    "tokens_entrada", "tokens_saida", "custo_nocional_usd",
)

URL_PADRAO = os.getenv("ESTEIRA_HUB_URL", f"{config.WORKER_BASE_URL}/telemetria")
FILA_PADRAO = config.LOGS_DIR / "hub-pendentes.jsonl"
TIMEOUT_S = 2          # hub lento não pode segurar execução


def limpar(dados):
    """Só o que está em CAMPOS, e `cwd` sem o home de ninguém."""
    saida = {k: dados[k] for k in CAMPOS if k in dados and dados[k] is not None}
    if "cwd" in saida:
        try:
            saida["cwd"] = str(Path(saida["cwd"]).relative_to(config.BASE_DIR))
        except (ValueError, TypeError):
            saida["cwd"] = Path(str(saida["cwd"])).name
    return saida


def _enfileirar(dados, fila):
    fila = Path(fila)
    fila.parent.mkdir(parents=True, exist_ok=True)
    with fila.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dados, ensure_ascii=False) + "\n")


def enviar(dados, url=None, fila=None, enfileirar_se_falhar=True):
    """
    Manda uma execução para o hub. Devolve True se entregou.

    NUNCA levanta. Falha de rede, hub morto, DNS quebrado, 500 do outro
    lado — tudo vira False e uma linha na fila local.
    """
    url = url or URL_PADRAO
    fila = Path(fila or FILA_PADRAO)
    corpo = limpar(dados)
    if not corpo:
        return False
    try:
        import requests
        r = requests.post(url, json=corpo, timeout=TIMEOUT_S)
        if 200 <= r.status_code < 300:
            return True
        # 4xx é payload errado nosso: enfileirar de novo só repetiria o erro.
        if 400 <= r.status_code < 500:
            _registrar(f"hub recusou {r.status_code}: {str(r.text)[:160]}")
            return False
    except Exception as e:
        _registrar(f"{type(e).__name__}: {str(e)[:160]}")
    if enfileirar_se_falhar:
        _enfileirar(corpo, fila)
    return False


def drenar(url=None, fila=None, maximo=500):
    """
    Reenvia o que ficou pendente. Devolve quantos entregou.

    Reescreve a fila com o que NÃO entregou — nunca apaga antes de ter
    certeza. Se o hub cair no meio da drenagem, o resto continua na fila.
    """
    url = url or URL_PADRAO
    fila = Path(fila or FILA_PADRAO)
    if not fila.exists():
        return 0
    linhas = [l for l in fila.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not linhas:
        return 0

    entregues, sobraram = 0, []
    for i, linha in enumerate(linhas):
        if i >= maximo:
            sobraram.append(linha)
            continue
        try:
            dados = json.loads(linha)
        except json.JSONDecodeError:
            continue          # linha corrompida não volta para a fila
        if enviar(dados, url=url, fila=fila, enfileirar_se_falhar=False):
            entregues += 1
        else:
            sobraram.append(linha)

    tmp = fila.with_suffix(fila.suffix + ".tmp")
    tmp.write_text("".join(l + "\n" for l in sobraram), encoding="utf-8")
    os.replace(tmp, fila)
    return entregues


def _registrar(msg):
    try:
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with (config.LOGS_DIR / "hub.log").open("a", encoding="utf-8") as f:
            f.write(f"{time.time():.0f} {msg}\n")
    except Exception:
        pass          # nem o log de falha pode derrubar quem reporta
