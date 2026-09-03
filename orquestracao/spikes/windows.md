# Spike — Windows: o que dá para afirmar sem máquina Windows

**Data:** 2026-09-03 · **Máquina:** Linux. **Nada aqui foi medido em Windows.**

Cada afirmação abaixo veio de documentação oficial ou do código-fonte do
projeto, com a URL. O que não teve fonte virou pergunta com o comando que a
responderia. Spike que inventa medição é pior que spike não feito, porque o
próximo passo é desenhado sobre chute.

**Cobertura:** de quatro perguntas, **uma foi respondida** (WebView2). As
outras três — PyInstaller, SmartScreen e credencial por CLI no Windows —
**não foram levantadas** porque o levantamento bateu no limite de sessão.
Estão na secção final, e não são "sem achados": são **não perguntadas**.

---

## 1. WebView2 e pywebview — RESPONDIDA

### O achado que muda o desenho

**Sem o WebView2 Runtime, o `pywebview` não dá erro. Ele cai para o motor do
Internet Explorer 11, em silêncio.**

Texto literal da documentação:

> On Windows renderer is chosen in the following order: `edgechromium`,
> `mshtml`. `mshtml` is the only renderer that is guaranteed to be available
> on any system.

E a mensagem que ele emite ao cair é um `logger.warning`, não uma exceção:

    MSHTML is deprecated. See https://pywebview.flowrl.com/guide/web_engine.html
    on details how to use Edge Chromium

Se a aplicação não configurar `logging`, **ninguém vê nada**. A janela abre,
e HTMX, `fetch`, CSS grid e ES6+ quebram sem explicação — o app "fica
esquisito" na máquina de uma pessoa e funciona na de outra.

Isto é exatamente o modo de falha que esta casa combate: passa em todo teste
e está errado. E é o mesmo formato da armadilha do `--font-montserrat`, em
que a fonte sumia em silêncio com os dois *gates* verdes.

Fonte: <https://github.com/r0x0r/pywebview/blob/master/docs/guide/web_engine.md>
e `webview/platforms/winforms.py`.

### Forçar `gui='edgechromium'` NÃO resolve

O código decide assim:

    is_chromium = not is_cef and _is_chromium() and forced_gui_ != 'mshtml'

O valor `'edgechromium'` **não aparece em lugar nenhum** como forçador. Se
`_is_chromium()` devolver `False`, cai no `else` do MSHTML de qualquer jeito.
**Não existe modo "WebView2 ou morra" embutido** — o *guard* tem que ser
escrito por nós, antes do `webview.start()`.

### Efeito colateral: só de importar, escreve no registro

`IE._set_ie_mode()` roda no nível de módulo e grava em
`HKCU\Software\Microsoft\Internet Explorer\Main\FeatureControl\...` um DWORD
com o nome do executável. Ou seja: **importar o módulo já altera o registro
do usuário**, mesmo que a janela nunca abra.

E se a chave do Internet Explorer não existir em `HKLM`, o import pode
levantar `OSError` em vez de degradar — isso é leitura do código, não
medição.

### O gate exato que ele usa

.NET Framework `Release >= 394802` (4.6.2) **e** a chave `pv` de um dos 4
GUIDs do EdgeUpdate com *major* >= 86. Atalho: se
`webview.settings['WEBVIEW2_RUNTIME_PATH']` estiver definido, devolve `True`
sem checar nada.

### Disponibilidade

> The Evergreen Runtime is preinstalled onto all Windows 11 devices as a part
> of the Windows 11 operating system. Microsoft installed the WebView2
> Runtime to all eligible Windows 10 devices... Even if your app uses the
> Evergreen distribution mode, we recommend that you distribute the WebView2
> Runtime, to cover edge cases where the Runtime wasn't already installed.

Windows 11: garantido. Windows 10: **a maioria sim, mas sem garantia**.
Fonte: <https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/evergreen-vs-fixed-version>

### Dependências

O único pacote Python extra no Windows é o `pythonnet` (que puxa
`clr_loader` e `cffi`). As DLLs do lado .NET do WebView2 **já vêm dentro do
wheel** do pywebview — não precisa NuGet nem SDK. O que não vem é o runtime
em si (`msedgewebview2.exe`).

Atenção para o empacotamento: `pythonnet 3.1.0` declara
`requires_python >=3.10,<3.15`, o que **trava a faixa de Python** que o
PyInstaller pode usar.

### O que isto obriga o app a fazer

1. **Checar o WebView2 antes de abrir a janela** e recusar-se a subir em
   MSHTML, com mensagem em PT-BR dizendo o que instalar. Degradar em silêncio
   para IE11 é inaceitável — é a mesma classe de falha que a casa combate.
2. **Distribuir o Evergreen Bootstrapper** junto, ou documentar a instalação
   como pré-requisito.
3. **Configurar `logging`** para que o `logger.warning` do pywebview apareça.

---

## 2. O que NÃO foi levantado

Não são "sem achados". São **não perguntadas** — o levantamento parou no
limite de sessão. Quem retomar, retome por aqui:

- **PyInstaller:** onefile × onedir, `--add-data` para Jinja e `static/`,
  `sys._MEIPASS`, ordem de grandeza do bundle, *hook* oficial do pywebview,
  e desligar o *reloader* do Werkzeug no binário.
- **SmartScreen:** a mensagem literal para `.exe` sem assinatura, Mark of
  the Web e `Unblock-File`, caminhos sem comprar certificado numa rede
  corporativa, OV × EV, e falso positivo de antivírus em binário PyInstaller.
- **Credencial por CLI no Windows:** onde `claude`, `codex`, `agy` e
  `opencode` guardam o *token*; se aceitam variável de config-dir; e a
  pergunta que decide o desenho do nó — **se a credencial mora no Credential
  Manager via DPAPI, um processo como SYSTEM não a lê**, e o nó tem que
  rodar como Tarefa Agendada sob o usuário interativo.

---

## 3. A confirmar na máquina Windows

Quando houver uma, rode e cole a saída aqui:

    # WebView2 presente?
    reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" /v pv
    reg query "HKCU\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" /v pv

    # .NET Framework >= 4.6.2 (Release >= 394802)?
    reg query "HKLM\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" /v Release

    # qual renderizador o pywebview escolheria
    python -c "from webview.platforms.winforms import _is_chromium; print('WebView2:', _is_chromium())"

    # onde cada CLI guarda credencial
    dir "%USERPROFILE%\.claude" & dir "%USERPROFILE%\.codex" & dir "%APPDATA%"
    cmdkey /list
