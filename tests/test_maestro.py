"""Testes dos contratos essenciais do maestro."""

import multiprocessing
from queue import Empty
from types import SimpleNamespace

import pytest

from esteira import maestro


@pytest.fixture(autouse=True)
def estado_do_maestro_isolado(tmp_path, monkeypatch):
    """Redireciona todo arquivo do maestro para a pasta temporária."""
    raiz = tmp_path / "repositorio"
    diretorio = raiz / "orquestracao"
    caminhos = {
        "DIR": diretorio,
        "FILA": diretorio / "fila.jsonl",
        "ESTADO": diretorio / "estado.json",
        "ESTADO_LOCK": diretorio / ".estado.lock",
        "DESPACHOS": diretorio / "despachos.jsonl",
        "JOURNAL": diretorio / "JOURNAL.md",
        "LOCK": diretorio / ".tick.lock",
    }
    for nome, caminho in caminhos.items():
        monkeypatch.setattr(maestro, nome, caminho)
    monkeypatch.setattr(maestro.config, "BASE_DIR", raiz)
    maestro.trava._fh = None
    maestro.trava._n = 0
    yield
    maestro.trava._fh = None
    maestro.trava._n = 0


def test_lock_permite_que_exatamente_um_despacho_reserve_a_vaga(monkeypatch):
    """Dois processos concorrentes não podem reservar a mesma vaga."""
    if "fork" not in multiprocessing.get_all_start_methods():
        pytest.skip("o teste concorrente exige processos com fork")

    fila = [
        {
            "id": identificador,
            "titulo": identificador,
            "tier": "codex",
            "escopo": f"escopos/{identificador}/**",
            "prova": "true",
            "prereq": [],
            "estado": "pronta",
        }
        for identificador in ("T-A", "T-B")
    ]
    maestro.escrever_fila(fila)
    for item in fila:
        briefing = maestro.DIR / "briefings" / f"{item['id']}.md"
        briefing.parent.mkdir(parents=True, exist_ok=True)
        briefing.write_text("Execute a tarefa.", encoding="utf-8")

    from esteira import contas, runner

    contexto = multiprocessing.get_context("fork")
    largada = contexto.Event()
    trabalhador_entrou = contexto.Event()
    liberar_trabalhador = contexto.Event()
    resultados = contexto.Queue()

    def rodar_falso(*args, **kwargs):
        trabalhador_entrou.set()
        liberar_trabalhador.wait(timeout=10)
        return SimpleNamespace(
            codigo=0,
            duracao_s=0,
            timeout=False,
            exit_confiavel=True,
        )

    monkeypatch.setattr(contas, "escolher", lambda tier: None)
    monkeypatch.setattr(runner, "rodar", rodar_falso)

    def despachar(identificador):
        largada.wait(timeout=3)
        try:
            maestro.dispatch(identificador, vaga=1)
        except SystemExit as erro:
            resultados.put((identificador, "rejeitado", str(erro)))
        except BaseException as erro:  # pragma: no cover - diagnóstico do processo filho
            resultados.put((identificador, "erro", repr(erro)))
        else:
            resultados.put((identificador, "reservado", ""))

    processos = [
        contexto.Process(target=despachar, args=(identificador,))
        for identificador in ("T-A", "T-B")
    ]
    for processo in processos:
        processo.start()

    largada.set()
    assert trabalhador_entrou.wait(timeout=3), (
        "nenhum dos despachos chegou a reservar a vaga"
    )
    try:
        primeiro_resultado = resultados.get(timeout=3)
    except Empty:
        primeiro_resultado = None
    liberar_trabalhador.set()

    recebidos = [] if primeiro_resultado is None else [primeiro_resultado]
    recebidos.extend(
        resultados.get(timeout=5) for _ in range(len(processos) - len(recebidos))
    )
    for processo in processos:
        processo.join(timeout=5)
        assert not processo.is_alive(), "um processo concorrente ficou travado"
        assert processo.exitcode == 0, "um processo concorrente terminou com erro"

    reservados = [r for r in recebidos if r[1] == "reservado"]
    rejeitados = [r for r in recebidos if r[1] == "rejeitado"]
    erros = [r for r in recebidos if r[1] == "erro"]
    assert not erros, f"os processos filhos tiveram erros inesperados: {erros}"
    assert len(reservados) == 1, (
        f"exatamente um despacho deveria reservar a vaga, resultado: {recebidos}"
    )
    assert len(rejeitados) == 1, (
        f"exatamente um despacho deveria ser rejeitado, resultado: {recebidos}"
    )
    assert "vaga 1 já tem" in rejeitados[0][2], (
        "o despacho perdedor deveria ser rejeitado porque a vaga estava ocupada"
    )


def test_colher_refaz_item_que_nao_tocou_o_disco_mesmo_com_saida_zero():
    """Saída zero sem mudança no disco nunca promove o item a feito."""
    maestro.escrever_fila(
        [
            {
                "id": "T-SEM-DISCO",
                "estado": "a_colher",
                "codigo": 0,
                "tocou_disco": False,
                "tentativas": 0,
            }
        ]
    )

    resultado = maestro.colher("T-SEM-DISCO")
    item_atualizado = maestro.ler_fila()[0]

    assert resultado[0]["veredito"] == "REFAZER", (
        "código zero sem escrita no disco deveria resultar em REFAZER"
    )
    assert resultado[0]["estado"] == "pronta", (
        "o item sem escrita deveria voltar para a fila pronta"
    )
    assert item_atualizado["estado"] == "pronta", (
        "a fila persistida deveria registrar o item como pronto para refazer"
    )
    assert item_atualizado["veredito_colheita"] == "REFAZER", (
        "a fila persistida não deveria registrar o item como feito"
    )


def test_foto_detecta_arquivo_novo_e_mudanca_de_tamanho(tmp_path):
    """A foto deve perceber criação de arquivo e alteração de tamanho."""
    raiz = tmp_path / "arquivos"
    raiz.mkdir()
    antes = maestro.foto("**/*.txt", raiz=raiz)

    arquivo = raiz / "novo.txt"
    arquivo.write_text("um", encoding="utf-8")
    depois_da_criacao = maestro.foto("**/*.txt", raiz=raiz)
    criados, removidos = maestro.diff_foto(antes, depois_da_criacao)

    assert criados == [str(arquivo)], "a foto deveria detectar o arquivo novo"
    assert removidos == [], "a criação não deveria indicar arquivo removido"

    arquivo.write_text("conteúdo maior", encoding="utf-8")
    depois_do_aumento = maestro.foto("**/*.txt", raiz=raiz)
    alterados, removidos = maestro.diff_foto(depois_da_criacao, depois_do_aumento)

    assert alterados == [str(arquivo)], "a foto deveria detectar a mudança de tamanho"
    assert removidos == [], "a mudança de tamanho não deveria remover arquivo"


def test_fora_do_escopo_acusa_externo_e_aceita_interno(tmp_path):
    """Caminho externo viola a raiz, mas caminho permitido dentro dela não."""
    raiz = tmp_path / "repositorio"
    interno = raiz / "tests" / "test_maestro.py"
    externo = tmp_path / "fora" / "intruso.py"

    resultado = maestro.fora_do_escopo(
        [str(interno), str(externo)], "tests/**", raiz=raiz
    )

    assert str(externo) in resultado, "um caminho fora da raiz deveria ser acusado"
    assert "tests/test_maestro.py" not in resultado, (
        "um caminho dentro do escopo não deveria ser acusado"
    )


def test_prereq_ok_distingue_pre_requisito_aberto_e_fechado():
    """Somente pré-requisito marcado como feito libera o item dependente."""
    dependente = {"id": "T-2", "prereq": ["T-1"]}
    fila_aberta = [{"id": "T-1", "estado": "pronta"}, dependente]
    fila_fechada = [{"id": "T-1", "estado": "feito"}, dependente]

    assert not maestro.prereq_ok(dependente, fila_aberta), (
        "pré-requisito aberto não deveria liberar o item"
    )
    assert maestro.prereq_ok(dependente, fila_fechada), (
        "pré-requisito fechado deveria liberar o item"
    )


def test_cruza_detecta_escopos_que_compartilham_diretorio():
    """Escopos no mesmo diretório principal devem ser considerados cruzados."""
    assert maestro.cruza("esteira/maestro.py", ["esteira/runner.py"]), (
        "escopos que compartilham o diretório esteira deveriam cruzar"
    )
    assert not maestro.cruza("tests/**", ["esteira/**"]), (
        "escopos em diretórios principais diferentes não deveriam cruzar"
    )
