"""
Wrapper de CLI. A peça mais frágil do sistema — por isso é a mais rígida.

REGRA NÚMERO UM
    Nunca leia a prosa do agente para saber o que aconteceu.
    stdout é log, não interface.
    O resultado vem de: (a) código de saída, (b) arquivos escritos.

Se você algum dia escrever um grep no stdout do CLI para decidir algo,
acabou de criar o bug que vai te assombrar.
"""
import os, shlex, subprocess, time, datetime as dt
from pathlib import Path
import config

# Só estas variáveis passam para o processo do agente.
# Nada de despejar o ambiente inteiro num processo que escreve arquivo.
ENV_PERMITIDO = (
    "PATH", "HOME", "USER", "LANG", "LC_ALL", "TERM", "SHELL",
    "TMPDIR", "XDG_CONFIG_HOME", "XDG_CACHE_HOME",
    # tokens de assinatura dos CLIs — ajuste ao que cada um usa
    "ANTHROPIC_API_KEY", "CLAUDE_CONFIG_DIR",
    "OPENAI_API_KEY", "CODEX_HOME",
    "OPENCODE_CONFIG", "OPENROUTER_API_KEY",
)


class Resultado:
    def __init__(self, codigo, duracao_s, log_path, timeout=False,
                 exit_confiavel=True):
        self.codigo = codigo
        self.duracao_s = duracao_s
        self.log_path = log_path
        self.timeout = timeout
        self.exit_confiavel = exit_confiavel

    @property
    def ok(self):
        return self.codigo == config.EXIT_OK

    @property
    def perguntou(self):
        return self.codigo == config.EXIT_ASK

    @property
    def bloqueado(self):
        return self.codigo == config.EXIT_BLOQUEADO

    def __repr__(self):
        return f"<Resultado codigo={self.codigo} {self.duracao_s:.0f}s timeout={self.timeout}>"


def _env(extra=None):
    env = {k: os.environ[k] for k in ENV_PERMITIDO if k in os.environ}
    env.update(extra or {})
    return env


def rodar(tier, prompt, cwd, log_path, timeout_s, extra_env=None, conta=None,
          on_start=None):
    """
    Roda um runtime de agente. Uma função, um lugar, sempre com timeout.

    tier      chave de config.RUNTIMES
    prompt    texto enviado por stdin
    cwd       diretório de trabalho (workspace da demanda)
    log_path  onde stdout+stderr vão parar
    conta     dict de esteira.contas.escolher() — injeta o config dir da
              assinatura de quem vai pagar essa execução
    """
    from esteira import contas as _contas
    rt = config.RUNTIMES.get(tier)
    if not rt or not rt["cmd"].strip():
        raise RuntimeError(
            f"runtime '{tier}' não configurado. Defina CMD_{tier.upper()} no .env"
        )

    cwd = Path(cwd)
    cwd.mkdir(parents=True, exist_ok=True)
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    env_extra = dict(extra_env or {})
    env_extra.update(_contas.env_para(conta))

    argv = shlex.split(rt["cmd"])
    inicio = time.time()
    timeout = False

    with log_path.open("a", encoding="utf-8") as log:
        quem = f"{conta['nome']} ({conta['tipo']})" if conta else "sem conta individual"
        log.write(f"\n{'='*70}\n{dt.datetime.now().isoformat()} :: {tier} :: {rt['cmd']}\n"
                  f"cwd={cwd}\nconta={quem}\n{'='*70}\n")
        log.flush()
        try:
            proc = subprocess.Popen(
                argv, cwd=str(cwd), env=_env(env_extra),
                stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
                text=True, start_new_session=True,
            )
            if on_start:
                on_start(proc.pid)
            try:
                proc.communicate(input=prompt, timeout=timeout_s)
                codigo = proc.returncode
            except subprocess.TimeoutExpired:
                timeout = True
                proc.kill()
                proc.communicate()
                codigo = 124
                log.write(f"\n[runner] TIMEOUT após {timeout_s}s — processo morto\n")
        except FileNotFoundError:
            log.write(f"\n[runner] comando não encontrado: {argv[0]}\n")
            codigo = 127

    confiavel = rt.get("exit_confiavel", config.EXIT_CONFIAVEL_PADRAO)
    res = Resultado(codigo, time.time() - inicio, log_path, timeout, confiavel)
    res.conta = conta
    _contas.marcar_uso(conta)
    # Falhou logo e não foi pergunta nem bloqueio: pode ser limite ou auth.
    # Colocamos a conta de molho e avisamos o dono. Não parseamos prosa
    # para "descobrir" o motivo — não é confiável.
    if (conta and confiavel
            and codigo not in (config.EXIT_OK, config.EXIT_ASK, config.EXIT_BLOQUEADO)):
        if res.duracao_s < 90:
            _contas.cooldown(conta, f"codigo={codigo} em {res.duracao_s:.0f}s")
    return res


def smoke_test(tier="lead", conta=None):
    """
    Autenticação expirando em silêncio é a forma número um deste setup
    morrer sem ninguém perceber. Rode de hora em hora, POR CONTA.
    """
    import tempfile
    sufixo = conta["chave"].replace(":", "-") if conta else tier
    with tempfile.TemporaryDirectory() as tmp:
        r = rodar(tier, prompt="Responda exatamente: OK", cwd=tmp,
                  log_path=config.LOGS_DIR / f"smoke-{sufixo}.log",
                  timeout_s=120, conta=conta)
    return r.ok, r


def smoke_todas():
    """Testa cada conta ativa. Devolve lista de (conta, ok)."""
    from esteira import contas as _c
    out = []
    for tier, tipo in _c.TIER_CONTA.items():
        for conta in _c.disponiveis(tipo):
            ok, _ = smoke_test(tier, conta)
            out.append((conta, ok))
    return out
