"""
Vigia. Processo separado, burro de propósito.

Um agente travado não avisa que travou — ele está travado. Então quem
avisa é outro. Este arquivo não tem inteligência nenhuma: olha horário de
arquivo e conta linha. É exatamente por isso que dá pra confiar nele.

Rodar por cron/systemd a cada 2 minutos.
"""
import os, signal, time, hashlib
from pathlib import Path
import config
from esteira.demanda import Demanda
from esteira import comm


def _vivo(pid):
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def _assinatura_progresso(d):
    """Hash do que existe no workspace + tamanho do journal."""
    ws = config.WORKSPACE_DIR / d.id
    partes = []
    if ws.exists():
        for p in sorted(ws.rglob("*")):
            if p.is_file() and ".git" not in p.parts:
                try:
                    partes.append(f"{p.relative_to(ws)}:{p.stat().st_size}")
                except OSError:
                    pass
    partes.append(f"journal:{(d.dir / 'journal.md').stat().st_size}")
    return hashlib.sha1("|".join(partes).encode()).hexdigest()[:12]


def checar(d):
    """Retorna (travada: bool, motivo: str)."""
    m = d.meta
    if d.estado != "EXECUTANDO":
        return False, ""

    agora = time.time()
    pid = m.get("pid")
    silencio = agora - d.ultimo_sinal

    if not _vivo(pid):
        return True, "o processo morreu sem chamar ask nem deliver"

    inicio = m.get("run_iniciado_em_ts") or agora
    if agora - inicio > config.TIMEOUT_RODADA_S:
        return True, f"passou do timeout da rodada ({config.TIMEOUT_RODADA_S // 60} min)"

    if silencio > config.SEM_SINAL_ALERTA_S:
        return True, f"journal parado há {int(silencio // 60)} min com processo vivo"

    ass = _assinatura_progresso(d)
    hist = m.get("assinaturas", [])
    if len(hist) >= 3 and len(set(hist[-3:])) == 1 and hist[-1] == ass:
        return True, "nenhum arquivo mudou nas últimas 3 verificações"
    hist = (hist + [ass])[-5:]
    d.set(assinaturas=hist)

    return False, ""


def matar(d, motivo):
    pid = d.meta.get("pid")
    if _vivo(pid):
        try:
            os.killpg(os.getpgid(int(pid)), signal.SIGTERM)
            time.sleep(3)
            if _vivo(pid):
                os.killpg(os.getpgid(int(pid)), signal.SIGKILL)
        except OSError:
            pass
    d.set(pid=None)
    d.transicao("TRAVADA", motivo)
    d.log("vigia", f"matou a execução: {motivo}")

    ultimas = [n["texto"] for n in d.ler_jsonl("notas.jsonl")[-2:]]
    corpo = "\n".join([
        f"**Motivo:** {motivo}",
        f"**Rodada:** {d.rodada}",
        f"**Última hipótese do agente:** {ultimas[-1] if ultimas else '(nenhuma nota)'}",
        "",
        "Escolha o que fazer no board.",
    ])
    env = comm.envelope(
        d, "blocked", f"🔴 #{d.id} travou — {d.meta.get('titulo','')}",
        corpo, opcoes=["continuar", "recomeçar rodada", "assumir", "cancelar"],
        default=None, urgencia="blocking",
    )
    comm.enviar(env)


def ciclo():
    for d in Demanda.todas():
        travada, motivo = checar(d)
        if travada:
            matar(d, motivo)


if __name__ == "__main__":
    while True:
        try:
            ciclo()
        except Exception as e:
            (config.LOGS_DIR / "vigia.log").parent.mkdir(exist_ok=True)
            with (config.LOGS_DIR / "vigia.log").open("a") as f:
                f.write(f"{time.time()} erro no ciclo: {e}\n")
        time.sleep(config.VIGIA_INTERVALO_S)
