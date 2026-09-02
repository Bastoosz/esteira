"""Smoke periódico das contas de assinatura e aviso de falhas."""
import argparse
import json
import re
import time
from types import SimpleNamespace

import config
from esteira import comm, contas, runner

ESTADO = config.LOGS_DIR / "sentinela-estado.json"


def _demanda_minima():
    return SimpleNamespace(
        id="sentinela",
        meta={"projeto": "esteira", "titulo": "Smoke das contas"},
        rodada=0,
    )


def _envelope_falha(conta):
    dono = conta["nome"]
    tipo = conta["tipo"]
    titulo = f"🔴 Conta de {dono} falhou — {tipo}"
    corpo = "\n".join([
        f"A conta de **{dono}** (`{conta['chave']}`) falhou no smoke de autenticação.",
        "",
        "A credencial isolada da esteira pode ter expirado e precisa ser autenticada novamente.",
        f"**Dono da conta:** {dono} ({conta.get('email') or 'e-mail não cadastrado'})",
    ])
    msg_id = f"sentinela-{conta['chave'].replace(':', '-')}-{int(time.time())}"
    return comm.envelope(
        _demanda_minima(), "blocked", titulo, corpo,
        msg_id=msg_id, urgencia="blocking",
    )


def _avisar(conta, simular=False):
    env = _envelope_falha(conta)
    destino = conta["nome"]
    if conta.get("email"):
        destino += f" <{conta['email']}>"
    if simular:
        print(f"Simulação: aviso para {destino} via envelope to={env['to']}.")
        print(f"Título: {env['titulo']}")
        return True
    ok, erro = comm.enviar(env)
    if ok:
        print(f"Aviso da conta de {conta['nome']} entregue ao n8n (to={env['to']}).")
    else:
        print(f"Aviso da conta de {conta['nome']} não enviado: {erro}")
    return ok


def _avisadas():
    try:
        return set(json.loads(ESTADO.read_text(encoding="utf-8"))["avisadas"])
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return set()


def _salvar_avisadas(avisadas):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(
        json.dumps({"avisadas": sorted(avisadas)}, indent=2), encoding="utf-8")


def _conta_simulada(chave, resultados):
    for conta, _ in resultados:
        if conta["chave"] == chave:
            return conta

    try:
        pessoa_id, tipo = chave.split(":", 1)
    except ValueError as erro:
        raise ValueError(f"conta inválida: {chave}") from erro
    def normalizar(texto):
        return re.sub(r"\W", "", texto).casefold()

    for item in contas.resumo():
        if (item["ativo"] and item["tipo"] == tipo
                and normalizar(item["pessoa"]) == normalizar(pessoa_id)):
            return {"chave": chave, "pessoa_id": pessoa_id,
                    "nome": item["pessoa"], "email": "", "tipo": tipo}
    raise ValueError(f"conta ativa não encontrada: {chave}")


def ciclo(simular_falha=None):
    resultados = runner.smoke_todas()
    chaves_testadas = {conta["chave"] for conta, _ in resultados}
    avisadas = _avisadas()
    antes = set(avisadas)
    avisadas.difference_update(
        conta["chave"] for conta, ok in resultados if ok)

    falhas = []
    for conta, ok in resultados:
        if not ok or conta["chave"] == simular_falha:
            falhas.append(conta)
    if simular_falha and not any(c["chave"] == simular_falha for c in falhas):
        falhas.append(_conta_simulada(simular_falha, resultados))

    total = len(resultados) + int(bool(simular_falha and simular_falha not in chaves_testadas))
    print(f"Smoke concluído: {total} conta(s); {total - len(falhas)} passaram; {len(falhas)} falharam.")
    if not falhas:
        print("Nenhum aviso enviado.")
        return

    for conta in falhas:
        print(f"Falha: conta de {conta['nome']} ({conta['chave']}).")
        if not simular_falha and conta["chave"] in avisadas:
            print("Aviso já entregue para esta falha; não será repetido.")
        elif _avisar(conta, simular=bool(simular_falha)) and not simular_falha:
            avisadas.add(conta["chave"])
    if not simular_falha and avisadas != antes:
        _salvar_avisadas(avisadas)


def _registrar_erro(erro):
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with (config.LOGS_DIR / "sentinela.log").open("a", encoding="utf-8") as log:
        log.write(f"{time.time()} erro no ciclo: {erro}\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Smoke periódico das contas da esteira")
    parser.add_argument("--uma-vez", action="store_true")
    parser.add_argument("--simular-falha", metavar="PESSOA:TIPO")
    args = parser.parse_args(argv)

    if args.uma_vez:
        try:
            ciclo(args.simular_falha)
            return 0
        except Exception as erro:
            _registrar_erro(erro)
            print(f"Erro no ciclo: {erro}")
            return 1

    while True:
        try:
            ciclo(args.simular_falha)
        except Exception as erro:
            _registrar_erro(erro)
        time.sleep(config.SMOKE_INTERVALO_S)


if __name__ == "__main__":
    raise SystemExit(main())
