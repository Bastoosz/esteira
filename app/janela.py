"""Janela desktop da Esteira, com WebView2 obrigatório no Windows."""

from __future__ import annotations

import logging
import platform
import sys
from typing import Any


_WEBVIEW2_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
_NET_462_RELEASE = 394802
_WEBVIEW2_MAJOR_MINIMO = 86

# O fallback do pywebview é comunicado por este logger. Sem configurar o
# logging, o aviso pode não aparecer para quem iniciou o aplicativo.
logging.basicConfig(level=logging.WARNING)
logging.getLogger("pywebview").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def _valor_registro(winreg: Any, raiz: Any, caminho: str, nome: str) -> Any | None:
    """Lê um valor do registro; chave ou valor ausente significa sem dado."""
    try:
        with winreg.OpenKey(raiz, caminho) as chave:
            valor, _tipo = winreg.QueryValueEx(chave, nome)
            return valor
    except OSError:
        return None


def tem_webview2() -> bool | None:
    """Informa se os pré-requisitos do WebView2 existem no Windows.

    Fora do Windows a pergunta não se aplica, portanto o retorno é ``None``.
    """
    if sys.platform != "win32":
        return None

    import winreg

    release = _valor_registro(
        winreg,
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full",
        "Release",
    )
    try:
        if int(release) < _NET_462_RELEASE:
            return False
    except (TypeError, ValueError):
        return False

    caminhos = [
        rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{_WEBVIEW2_GUID}",
    ]
    # Assim como o pywebview, HKCU usa a chave normal; em Windows não-x86,
    # a instalação por máquina é procurada na visão WOW6432Node.
    caminho_hklm = caminhos[0]
    if platform.machine().lower() != "x86":
        caminho_hklm = rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{_WEBVIEW2_GUID}"

    locais = (
        (winreg.HKEY_CURRENT_USER, caminhos[0]),
        (winreg.HKEY_LOCAL_MACHINE, caminho_hklm),
    )
    for raiz, caminho in locais:
        versao = _valor_registro(winreg, raiz, caminho, "pv")
        try:
            major = int(str(versao).split(".", 1)[0])
        except (TypeError, ValueError):
            continue
        if major >= _WEBVIEW2_MAJOR_MINIMO:
            return True

    return False


def mensagem_sem_webview2() -> str:
    """Orienta a instalação do runtime exigido pela janela."""
    return (
        "O WebView2 Runtime não está instalado ou está desatualizado. "
        "Instale o Microsoft Edge WebView2 Runtime usando o Evergreen "
        "Bootstrapper em "
        "https://developer.microsoft.com/microsoft-edge/webview2/consumer/ "
        "e tente abrir a Esteira novamente."
    )


def abrir_janela() -> None:
    """Abre o Flask em uma janela somente quando o WebView2 está disponível."""
    if tem_webview2() is False:
        raise RuntimeError(mensagem_sem_webview2())

    # Importar pywebview no Windows pode carregar o backend e tocar o registro.
    # Por isso o import ocorre somente depois do guard e é tolerante no Linux.
    try:
        import webview
    except ImportError as erro:
        raise RuntimeError(
            "O componente Python pywebview não está instalado. "
            "Instale as dependências do aplicativo antes de abrir a janela."
        ) from erro

    from app.app import app

    webview.create_window("Esteira", app)
    webview.start(gui="edgechromium")


def main() -> int:
    try:
        abrir_janela()
    except RuntimeError as erro:
        logger.error("%s", erro)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
