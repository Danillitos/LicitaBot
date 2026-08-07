import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui
import pandas as pd
import time
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
    SessionNotCreatedException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from pathlib import Path
import threading
import os
import re
import subprocess
import unicodedata

PRE_INSTRUMENTO = 'XXXXX'
PLANILHA_PATH = 'XXXXX'
DEFAULT_TIMEOUT = 60
SIMILARITY_THRESHOLD = 0.85
MAX_TRIES = 5
MAX_RESTARTS = None
VELOCIDADE_MULTIPLICADOR = 1.0

MARGEM_RENOVACAO_SEG = 300

MAX_RECUPERACOES_LEVES = 2

BTN_SALVAR = 'button.btn.btn-primary:not(.modal-dialog button)'
BTN_MODAL_SIM = '.modal-dialog button.btn.btn-primary'

ICONE_EDITAR = 'i.fa.fa-pencil'

LOGO_PRINCIPAL_ID = 'lnkPrincipal'
URL_PRINCIPAL_LEGADO = ('https://discricionarias.transferegov.sistema.gov.br/voluntarias/'
                        'ForwardAction.do?modulo=Principal&path=/Principal.do')
MENU_PRINCIPAL_ID = 'menuPrincipal'
CRONOMETRO_ID = 'tempoRestante'

MODAL_AUSENTE = 'ausente'
MODAL_SESSAO = 'sessao'
MODAL_DESCONHECIDO = 'desconhecido'

STOP_REQUESTED = threading.Event()

Path("logs").mkdir(exist_ok=True)


class RecuperacaoFalhou(Exception):
    """A recuperação leve (sem captcha) não conseguiu restaurar a navegação."""


def get_relatorio_path():
    return f'logs/relatorio_execucao-{PRE_INSTRUMENTO}.xlsx'

RELATORIO_PATH = get_relatorio_path()


def log(mensagem, nivel="info"):
    """Escreve no console e em logs/execucao-<instrumento>.log.

    O executável é buildado com console=False (app.spec), então print() sozinho
    não chega a lugar nenhum — sem o arquivo, o usuário fica cego quanto ao que
    aconteceu na máquina dele."""
    marcador = {"info": "ℹ️", "ok": "✅", "aviso": "⚠️", "erro": "🚫"}.get(nivel, "")
    linha = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {marcador} {mensagem}"
    print(linha)
    try:
        with open(f'logs/execucao-{PRE_INSTRUMENTO}.log', 'a', encoding='utf-8') as arquivo:
            arquivo.write(linha + "\n")
    except OSError:
        pass


def velocity_sleep(base_seconds):
    global STOP_REQUESTED
    actual_sleep = base_seconds * VELOCIDADE_MULTIPLICADOR
    interval = 0.2

    elapsed = 0
    while elapsed < actual_sleep:
        if STOP_REQUESTED.is_set():
            print("🚫 Parada solicitada durante sleep. Encerrando processo...")
            break
        time.sleep(min(interval, actual_sleep - elapsed))
        elapsed += interval


def aguardar(condicao, timeout=15, intervalo=0.5):
    """Espera `condicao()` virar verdadeira, respeitando a parada do usuário.

    Não passa por VELOCIDADE_MULTIPLICADOR de propósito: renovação de sessão não é
    etapa de preenchimento, e o usuário não deve conseguir deixá-la lenta a ponto de
    perder a janela do token."""
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        if STOP_REQUESTED.is_set():
            return False
        try:
            if condicao():
                return True
        except WebDriverException:
            pass
        time.sleep(intervalo)
    return False


def _normalizar(texto):
    """Minúsculas, sem acento e com espaços colapsados — para comparar texto de tela."""
    decomposto = unicodedata.normalize('NFKD', texto or '')
    sem_acento = ''.join(c for c in decomposto if not unicodedata.combining(c))
    return ' '.join(sem_acento.lower().split())


def _int_seguro(valor, padrao=0):
    """int() que absorve NaN/None/texto — o relatório tem colunas incompletas."""
    try:
        if valor is None or pd.isna(valor):
            return padrao
        return int(valor)
    except (TypeError, ValueError):
        return padrao


def renovou(antes, depois):
    """A renovação valeu? O critério é ter folga, não o contador ter subido.

    Um bounce partindo de um token já cheio (30:00) não faz o número crescer, e exigir
    crescimento reprovava uma renovação perfeitamente boa."""
    if depois is None:
        return antes is None
    return depois > (antes or 0) or depois > MARGEM_RENOVACAO_SEG


def _mmss(segundos):
    if segundos is None:
        return "??:??"
    return f"{segundos // 60:02d}:{segundos % 60:02d}"


def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def similarity(s1, s2):
    s1 = s1.lower().strip().replace(' ', '').replace('.', '').replace('_', '').replace('/', '')
    s2 = s2.lower().strip().replace(' ', '').replace('.', '').replace('_', '').replace('/', '')
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1 - (distance / max_len) if max_len != 0 else 1.0

def get_chrome_major_version():
    """Retorna a versão principal (ex: 149) do Chrome instalado, ou None se não detectada.
    Assim o chromedriver baixado sempre corresponde ao navegador, mesmo após atualizações."""
    if os.name != "nt":
        return None

    import winreg

    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, r"Software\Google\Chrome\BLBeacon") as key:
                version, _ = winreg.QueryValueEx(key, "version")
                return int(version.split(".")[0])
        except (OSError, ValueError, IndexError):
            continue

    candidates = []
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        ) as key:
            candidates.append(winreg.QueryValueEx(key, None)[0])
    except OSError:
        pass
    candidates += [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            try:
                output = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command",
                     f"(Get-Item '{path}').VersionInfo.ProductVersion"],
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                return int(output.strip().split(".")[0])
            except (subprocess.SubprocessError, ValueError, IndexError, OSError):
                continue

    return None

def abrir_chrome(browser_executable_path=None):
    """Sobe um Chrome com o chromedriver correspondente à versão instalada.

    `browser_executable_path` fixa qual navegador usar. Sem ele, o undetected_chromedriver
    escolhe sozinho — e numa máquina com Chrome e Chromium instalados a escolha varia
    entre execuções, o que torna qualquer teste local irreprodutível.

    A segunda tentativa não é luxo: a versão nem sempre é detectável de antemão (fora
    do Windows não há registro para consultar, e o navegador efetivamente lançado pode
    ser outro — um Chromium do sistema em vez do Chrome). A mensagem de erro do driver
    informa a versão real, e é dela que partimos."""
    version_main = get_chrome_major_version()
    if version_main:
        log(f"Chrome detectado: versão {version_main}")
    else:
        log("Versão do Chrome não detectada. Usando a versão mais recente do driver.", "aviso")
    try:
        return uc.Chrome(options=Options(), version_main=version_main,
                         browser_executable_path=browser_executable_path)
    except SessionNotCreatedException as e:
        match = re.search(r"Current browser version is (\d+)", str(e))
        if not match:
            raise
        browser_major = int(match.group(1))
        log(f"Driver incompatível com o navegador. Baixando driver para o Chrome {browser_major}...", "aviso")
        return uc.Chrome(options=Options(), version_main=browser_major,
                         browser_executable_path=browser_executable_path)


def init_driver():
    driver = abrir_chrome()
    driver.execute_cdp_cmd('Storage.clearDataForOrigin', {"origin": '*', "storageTypes": 'all'})
    driver.get('https://portal.transferegov.sistema.gov.br/portal/home')
    return driver

def load_data():
    df = pd.read_excel(PLANILHA_PATH)
    df_filtrado = df[df.iloc[:, 4].notna()]
    df_filtrado = df_filtrado[df_filtrado.iloc[:, 4] != 0]
    descricoes = df_filtrado.iloc[:, 1].astype(str).tolist()
    precosUnit = df_filtrado.iloc[:, 4].astype(float).apply(lambda x: f"{x:.2f}").tolist()
    return descricoes, precosUnit

def get_fresh_edit_icons(driver):
    for _ in range(5):
        try:
            return WebDriverWait(driver, DEFAULT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ICONE_EDITAR))
            )
        except (StaleElementReferenceException, TimeoutException):
            velocity_sleep(2)
    raise TimeoutException("Falha ao obter ícones de edição após retries")

def js_click(driver, css, action='click', text='', retries=10, delay=2):
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            velocity_sleep(0.5)
            if action == 'click':
                driver.execute_script("arguments[0].click();", element)
            elif action == 'write':
                driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element, text)
            return True
        except (StaleElementReferenceException, TimeoutException, ElementClickInterceptedException) as e:
            log(f"Tentativa {attempt+1} falhou em {css}: {type(e).__name__}", "aviso")
            velocity_sleep(delay)
    return False

def click_and_write(driver, path, action, text=''):
    try:
        element = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, path)))
        if action == 'click':
            element.click()
        elif action == 'write':
            element.clear()
            element.send_keys(text)
        return True
    except Exception as e:
        log(f"Erro em click_and_write para {path}: {e}", "aviso")
        return False

def go_to_page(driver, page_num):
    try:
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.pagination.paginacao')))
        
        pagination_buttons = driver.find_elements(By.CSS_SELECTOR, 'ul.pagination.paginacao li a')
        
        for button in pagination_buttons:
            if button.text.strip() == str(page_num + 1):
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                ActionChains(driver).move_to_element(button).click().perform()
                WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, ICONE_EDITAR)))
                velocity_sleep(2)
                return True
        
        current_page = pagina_atual(driver)
        next_button_selector = 'ul.pagination.paginacao li:last-child a'
        for _ in range(page_num - current_page):
            next_button = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector)))
            driver.execute_script("arguments[0].click();", next_button)
            WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.staleness_of(next_button))
            WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, ICONE_EDITAR)))
            velocity_sleep(2)
        return True
    except TimeoutException:
        log(f"Timeout ao navegar para página {page_num+1}", "aviso")
        return False
    except Exception as e:
        log(f"Erro ao navegar para página {page_num+1}: {e}", "aviso")
        return False

def pagina_atual(driver):
    try:
        active_page = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.pagination.paginacao li.active a')))
        return int(active_page.text.strip()) - 1
    except:
        return 0


def tempo_restante(driver):
    """Segundos de vida restantes do token, lidos de #tempoRestante ("MM:SS").

    O cronômetro é do shell externo do TransfereGov e acompanha toda a navegação,
    inclusive o formulário de edição. Custo de ~5ms — pode ser chamado a cada item."""
    try:
        texto = driver.execute_script(
            "var el = document.querySelector('#%s');"
            "return el ? el.textContent.trim() : null;" % CRONOMETRO_ID
        )
    except WebDriverException:
        return None
    if not texto:
        return None
    match = re.match(r'^(\d+):(\d{2})$', texto)
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2))


def inspecionar_modal(driver):
    """Estado do diálogo modal na tela, como (estado, html).

    O modal é criado e destruído dinamicamente — não fica escondido no DOM. Logo a
    ausência de `.modal-dialog` já é resposta definitiva, sem custo de espera.

    Um `.modal-dialog` que NÃO seja o de sessão devolve MODAL_DESCONHECIDO: clicar no
    botão primário de um diálogo que não sabemos o que é seria confirmar de olhos
    fechados, então o chamador registra e escala em vez de clicar."""
    try:
        dados = driver.execute_script(
            "var el = document.querySelector('.modal-dialog');"
            "return el ? {texto: el.innerText, html: el.outerHTML} : null;"
        )
    except WebDriverException:
        return MODAL_AUSENTE, None

    if not dados:
        return MODAL_AUSENTE, None

    if 'reiniciar sessao' in _normalizar(dados.get('texto')):
        return MODAL_SESSAO, dados.get('html')
    return MODAL_DESCONHECIDO, dados.get('html')


def renovar_via_modal(driver):
    """Clica "Sim" no modal de reinício de sessão — caminho mais barato: ~2s e não
    tira a automação do lugar. Confirma o sucesso pelo cronômetro, não pela fé."""
    antes = tempo_restante(driver)
    try:
        clicado = driver.execute_script(
            "var btns = document.querySelectorAll('%s');"
            "if (!btns.length) return false;" % BTN_MODAL_SIM +
            "for (var i = 0; i < btns.length; i++) {"
            "  if (btns[i].textContent.trim().toLowerCase().indexOf('sim') === 0) {"
            "    btns[i].click(); return true;"
            "  }"
            "}"
            "btns[0].click(); return true;"
        )
    except WebDriverException as e:
        log(f"Erro ao clicar em 'Sim' no modal: {e}", "aviso")
        return False

    if not clicado:
        log("Modal de sessão sem botão primário clicável.", "aviso")
        return False

    if not aguardar(lambda: inspecionar_modal(driver)[0] == MODAL_AUSENTE):
        log("Cliquei em 'Sim' mas o modal não sumiu.", "aviso")
        return False

    depois = tempo_restante(driver)
    if not renovou(antes, depois):
        log(f"Modal fechou mas o token não renovou ({_mmss(antes)} → {_mmss(depois)}).", "aviso")
        return False

    log(f"Sessão renovada pelo modal. Tempo restante: {_mmss(depois)}", "ok")
    return True


def bounce_logo(driver):
    """Renova o token clicando na logo do TransfereGov (#lnkPrincipal).

    É uma navegação real do módulo legado (ForwardAction.do), não um router link do
    Angular. Três efeitos de uma vez: renova a sessão do sistema externo, reconstrói
    a árvore Angular inteira (nenhuma referência stale sobrevive) e devolve à Página
    Principal, de onde `navegar_ate_planilha` sabe continuar — sem login nem captcha.

    O clique é via JS justamente para atravessar o backdrop caso o modal esteja
    aberto e o "Sim" tenha falhado."""
    antes = tempo_restante(driver)
    try:
        clicado = driver.execute_script(
            "var el = document.querySelector('#%s');"
            "if (!el) return false;"
            "el.click(); return true;" % LOGO_PRINCIPAL_ID
        )
    except WebDriverException as e:
        log(f"Erro ao clicar na logo: {e}", "erro")
        return False

    if not clicado:
        log(f"Logo #{LOGO_PRINCIPAL_ID} ausente na tela. Indo direto à Página Principal.")
        try:
            driver.get(URL_PRINCIPAL_LEGADO)
        except WebDriverException as e:
            log(f"Falha ao navegar para a Página Principal: {e}", "erro")
            return False

    try:
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, MENU_PRINCIPAL_ID))
        )
    except TimeoutException:
        log(f"Após a logo, #{MENU_PRINCIPAL_ID} não apareceu — não voltamos à Página Principal.", "erro")
        return False

    depois = tempo_restante(driver)
    if not renovou(antes, depois):
        log(f"Voltei à Página Principal mas o token não renovou ({_mmss(antes)} → {_mmss(depois)}).", "aviso")
        return False

    log(f"Sessão renovada pela logo. Tempo restante: {_mmss(depois)}", "ok")
    return True


def sessao_expirada(driver):
    """True quando o navegador foi jogado para fora da área autenticada.

    Deliberadamente restrito ao domínio de SSO: um falso positivo aqui força um
    reinício completo com captcha, que é exatamente o que estamos tentando evitar."""
    try:
        url = (driver.current_url or '').lower()
    except WebDriverException:
        return True
    return 'sso.acesso.gov.br' in url


def recuperar_navegacao(driver, pagina):
    """Recuperação leve: renova pela logo e refaz o caminho até a planilha, mantendo
    o mesmo navegador e a mesma sessão gov.br. Sem captcha, sem intervenção humana."""
    if not bounce_logo(driver):
        raise RecuperacaoFalhou("não consegui renovar pela logo")
    if not navegar_ate_planilha(driver):
        raise RecuperacaoFalhou("não consegui re-navegar até a planilha")
    if not go_to_page(driver, pagina):
        raise RecuperacaoFalhou(f"não consegui voltar para a página {pagina + 1}")
    log(f"Recuperação leve concluída — de volta à página {pagina + 1}.", "ok")
    return True


def garantir_sessao(driver, pagina):
    """Guarda de sessão. Chamar em ponto seguro: entre itens, sem formulário aberto.

    Prevenir custa menos que remediar — por isso o limiar de renovação (5:00) fica
    acima do momento em que o modal nasce (~3:00): na prática o modal quase nunca
    chega a aparecer, e nunca aparece no meio de um preenchimento."""
    estado, html = inspecionar_modal(driver)

    if estado == MODAL_DESCONHECIDO:
        log(f"Modal não reconhecido na tela. Não vou clicar em nada. HTML: {(html or '')[:400]}", "aviso")
        return False

    if estado == MODAL_SESSAO:
        log("Modal de reinício de sessão detectado. Clicando em 'Sim'...")
        if renovar_via_modal(driver):
            return False
        log("'Sim' não resolveu. Caindo para o bounce na logo (atravessa o backdrop)...", "aviso")
        return recuperar_navegacao(driver, pagina)

    restante = tempo_restante(driver)
    if restante is None:
        return False

    if restante <= MARGEM_RENOVACAO_SEG:
        log(f"Token com {_mmss(restante)} restantes (limiar {_mmss(MARGEM_RENOVACAO_SEG)}). Renovando preventivamente...")
        return recuperar_navegacao(driver, pagina)

    return False


def dispensar_avisos(driver):
    """Fecha caixas de comunicado do portal (ex.: o aviso da CGU) que ficam sobre a
    tela e interceptam cliques nativos.

    Casamos pelo texto do botão, não por posição no DOM: o TransfereGov publica esses
    comunicados sem aviso prévio, e um seletor posicional quebraria no próximo. Custo
    de uma consulta JS — não espera nada quando não há aviso."""
    try:
        fechados = driver.execute_script("""
            var alvos = ['ok, entendi', 'ok entendi', 'entendi'];
            var n = 0;
            document.querySelectorAll('button, a.btn, input[type=button]').forEach(function (b) {
                if (!b.offsetParent) return;
                var t = (b.innerText || b.value || '').trim().toLowerCase();
                if (alvos.indexOf(t) >= 0) { b.click(); n++; }
            });
            return n;
        """)
    except WebDriverException:
        return False
    if fechados:
        log(f"{fechados} aviso(s) do portal dispensado(s).")
    return bool(fechados)


def login_inicial(driver):
    """Do portal até a sessão autenticada. Único trecho que exige o usuário presente
    (captcha), e por isso o único que a recuperação leve precisa evitar."""
    try:
        if not click_and_write(driver, '/html/body/portal-root/br-main-layout/div/div/div/main/portal-main/div/div[2]/div[2]/card/div/div/div[3]/button', 'click'):
            raise Exception("Falha ao clicar no botão inicial")
        velocity_sleep(1)

        aguardar(lambda: dispensar_avisos(driver), timeout=8, intervalo=0.5)

        if not click_and_write(driver, '//*[@id="form_submit_login"]', 'click'):
            raise Exception("Falha ao clicar no submit login")
        velocity_sleep(1)

        pyautogui.alert('Por favor, faça o login e realize o captcha. Em seguida, pressione OK para continuar')
        return True
    except Exception as e:
        log(f"Erro durante o login inicial: {e}", "erro")
        return False


def navegar_ate_planilha(driver):
    """Da Página Principal até a listagem de itens da planilha orçamentária.

    Ponto de entrada compartilhado pelo fluxo normal e pela recuperação leve — é
    exatamente onde a logo do TransfereGov nos deixa, o que permite reentrar aqui
    sem refazer login."""
    try:
        if not click_and_write(driver, '//*[@id="menuPrincipal"]/div[1]/div[4]', 'click'):
            raise Exception("Falha ao clicar no menu principal")
        velocity_sleep(1)
        if not click_and_write(driver, '//*[@id="contentMenu"]/div[1]/ul/li[11]/a', 'click'):
            raise Exception("Falha ao clicar no item de menu")
        velocity_sleep(1)
        if not click_and_write(driver, '//*[@id="consultarNumeroConvenio"]', 'write', PRE_INSTRUMENTO):
            raise Exception("Falha ao escrever número do convênio")
        velocity_sleep(1)
        if not click_and_write(driver, '//*[@id="form_submit"]', 'click'):
            raise Exception("Falha ao submeter formulário")
        velocity_sleep(1)
        if not click_and_write(driver, '//*[@id="instrumentoId"]/a', 'click'):
            raise Exception("Falha ao clicar no instrumento ID")
        velocity_sleep(1)

        if not click_and_write(driver, '//*[@id="div_-481524888"]/span', 'click'):
            raise Exception("Falha ao clicar na div span")
        velocity_sleep(1)
        if not click_and_write(driver, '//*[@id="menu_link_-481524888_-333124204"]/div/span/span', 'click'):
            raise Exception("Falha ao clicar no menu link")
        velocity_sleep(1)

        if not js_click(driver, 'a[title="Exibir Dados Detalhados"]'):
            raise Exception("Falha ao clicar em Exibir Dados Detalhados")
        velocity_sleep(1)
        if not js_click(driver, 'a[title="Planilhas Orçamentárias / Cronogramas Físico Financeiro"]'):
            raise Exception("Falha ao clicar em Planilhas Orçamentárias")
        velocity_sleep(1)

        metas = get_fresh_edit_icons(driver)
        meta = metas[0]
        icone_meta = meta.find_element(By.XPATH, './parent::a')
        driver.execute_script('arguments[0].click()', icone_meta)
        velocity_sleep(1)

        if not js_click(driver, 'a[title="Planilha Orçamentária"]'):
            raise Exception("Falha ao clicar em Planilha Orçamentária")
        velocity_sleep(1)

        WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, ICONE_EDITAR)))

        log(f"Listagem da planilha carregada. Token com {_mmss(tempo_restante(driver))} restantes.", "ok")
        return True
    except Exception as e:
        log(f"Erro durante a navegação até a planilha: {e}", "erro")
        return False


def save_or_concat(log_registros, save):
    df_log = pd.DataFrame(log_registros)
    if save is not None:
        new_report = pd.read_excel(RELATORIO_PATH)
        df_concat = pd.concat([new_report, df_log])
        df_concat.to_excel(RELATORIO_PATH, index=False)
    else:
        df_log.to_excel(RELATORIO_PATH, index=False)
    log(f"Relatório salvo em {RELATORIO_PATH}")


def carregar_progresso():
    """Último ponto salvo: (save, i, i_global, pagina, inicializacoes).

    Toda leitura passa por _int_seguro porque as linhas de MISMATCH gravam a coluna
    de inicializações vazia — um int(NaN) aqui derrubava a carga inteira e fazia a
    automação recomeçar do item 1, reescrevendo tudo."""
    try:
        save = pd.read_excel(RELATORIO_PATH)
    except FileNotFoundError:
        log("Ponto salvo não encontrado. Iniciando do zero.")
        return None, 0, 0, 0, 1
    except Exception as e:
        log(f"Não foi possível abrir o relatório ({e}). Iniciando do zero.", "aviso")
        return None, 0, 0, 0, 1

    try:
        i_global = _int_seguro(save.iloc[-1, 0])
        i = _int_seguro(save.iloc[-1, 1])
        pagina = _int_seguro(save.iloc[-1, 2])

        coluna = next((c for c in ("Inicializacoes", "inicializacoes") if c in save.columns), None)
        if coluna is not None:
            valores = pd.to_numeric(save[coluna], errors="coerce").dropna()
            inicializacoes = int(valores.max()) + 1 if len(valores) else 1
        else:
            inicializacoes = 1

        log(f"Ponto salvo encontrado! Retomando da iteração {i_global}, página {pagina+1}, item {i+1}.")
        return save, i, i_global, pagina, inicializacoes
    except Exception as e:
        log(f"Relatório ilegível ({e}). Iniciando do zero.", "aviso")
        return None, 0, 0, 0, 1


def check_stop():
    return STOP_REQUESTED.is_set()


def run_filling():
    global RELATORIO_PATH
    RELATORIO_PATH = get_relatorio_path()

    global STOP_REQUESTED
    STOP_REQUESTED = threading.Event()

    descricoes, precosUnit = load_data()
    log_registros = []

    save, i, i_global, pagina, inicializacoes = carregar_progresso()

    driver = None
    reinicios = 0

    while i_global < len(descricoes):
        if check_stop():
            break

        if MAX_RESTARTS is not None and reinicios > MAX_RESTARTS:
            log(f"Limite de {MAX_RESTARTS} reinicializações atingido. Encerrando.", "erro")
            break

        driver = None
        try:
            driver = init_driver()
            if not login_inicial(driver):
                raise Exception("Falha no login inicial")
            if not navegar_ate_planilha(driver):
                raise Exception("Falha na navegação inicial até a planilha")

            falhas_leves = 0

            while i_global < len(descricoes):
                if check_stop():
                    break

                try:
                    garantir_sessao(driver, pagina)

                    if not go_to_page(driver, pagina):
                        raise TimeoutException("Falha ao navegar para página")

                    icones_editar = get_fresh_edit_icons(driver)
                    falhas_leves = 0

                    if i >= len(icones_editar):
                        log(f"Fim dos elementos na página {pagina+1}. Avançando...")
                        pagina += 1
                        i = 0
                        continue

                    tentativas = 0
                    while True:
                        if check_stop():
                            break

                        for attempt in range(5):
                            if check_stop():
                                break

                            try:
                                icones_editar = get_fresh_edit_icons(driver)
                                icone = icones_editar[i]
                                link_editar = icone.find_element(By.XPATH, './parent::a')
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_editar)
                                velocity_sleep(1)
                                driver.execute_script("arguments[0].click();", link_editar)
                                break
                            except StaleElementReferenceException:
                                log(f"Elemento stale na iteração {i_global}, tentativa {attempt+1}", "aviso")
                                velocity_sleep(3)
                        else:
                            raise StaleElementReferenceException("Falha persistente em stale element ao clicar edit")

                        velocity_sleep(3)

                        try:
                            WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="precoUnitarioLicitado"]')))
                        except TimeoutException as e:
                            log(f"Timeout esperando campo de preço unitário: {e}", "aviso")
                            raise

                        valor_atual = driver.execute_script("return document.querySelector('input[formcontrolname=\"precoUnitarioLicitado\"]').value;")
                        descricao_site = driver.execute_script("return document.querySelector('p[id=\"descricao\"]').innerText;")

                        log(f"Iteração {i_global}: site -> {descricao_site}")
                        log(f"Iteração {i_global}: planilha -> {descricoes[i_global]}")

                        sim = similarity(descricao_site, descricoes[i_global])
                        log(f"Similaridade Levenshtein: {sim:.2f}")

                        if sim >= SIMILARITY_THRESHOLD:
                            log('Descrições semelhantes o suficiente.', "ok")

                            log(f"Iteração {i_global}: substituindo {valor_atual} por {precosUnit[i_global]}...")

                            if not js_click(driver, 'input[formcontrolname="precoUnitarioLicitado"]', 'write', precosUnit[i_global]):
                                raise Exception("Falha ao escrever valor")

                            velocity_sleep(2)

                            estado_modal, _ = inspecionar_modal(driver)
                            if estado_modal == MODAL_SESSAO:
                                log("Modal apareceu com o formulário aberto. Renovando antes de salvar...", "aviso")
                                renovar_via_modal(driver)

                            if not js_click(driver, BTN_SALVAR):
                                raise Exception("Falha ao clicar em salvar")

                            WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.visibility_of_element_located((By.CLASS_NAME, 'table')))
                            velocity_sleep(2)

                            log(f"Iteração {i_global}: valor inserido com sucesso!", "ok")

                            log_registros.append({
                                "Iteração Geral": i_global,
                                "Iteração na pagina": i,
                                "Pagina": pagina,
                                "Descricao_Site": descricao_site,
                                "Descricao_Planilha": descricoes[i_global],
                                "Preco_Atual": valor_atual,
                                "Preco_Novo": precosUnit[i_global],
                                "Similaridade": sim,
                                "Status": "OK",
                                "Obs": "",
                                "inicializacoes": inicializacoes
                            })

                            i += 1
                            i_global += 1
                            break

                        else:
                            obs = f"Descrições divergentes (similaridade {sim:.2f} < {SIMILARITY_THRESHOLD})"
                            log(f'{obs}! Favor verificar. Tentando novamente após voltar...', "aviso")

                            if not js_click(driver, 'button.btn.btn-secondary.botao-voltar'):
                                log("Falha no Voltar com .btn.btn-secondary.botao-voltar. Tentando fallback...", "aviso")
                                js_click(driver, 'button.botao-voltar')

                            WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.visibility_of_element_located((By.CLASS_NAME, 'table')))
                            velocity_sleep(2)

                            log_registros.append({
                                "Iteração Geral": i_global,
                                "Iteração na pagina": i,
                                "Pagina": pagina,
                                "Descricao_Site": descricao_site,
                                "Descricao_Planilha": descricoes[i_global],
                                "Preco_Atual": valor_atual,
                                "Preco_Novo": precosUnit[i_global],
                                "Similaridade": sim,
                                "Status": "MISMATCH",
                                "Obs": obs + f" - Tentativa {tentativas + 1}",
                                "inicializacoes": inicializacoes
                            })

                            tentativas += 1
                            if tentativas >= MAX_TRIES:
                                log(f"Máximo de tentativas ({MAX_TRIES}) atingido para iteração {i_global}. Pulando item...", "aviso")
                                log_registros[-1]["Status"] = "SKIPPED"
                                log_registros[-1]["Obs"] += " - Pulado após max tentativas"
                                i += 1
                                i_global += 1
                                break

                    if i_global % 10 == 0:
                        save_or_concat(log_registros, save)
                        log_registros = []
                        save = pd.read_excel(RELATORIO_PATH)

                except RecuperacaoFalhou as e:
                    log(f"Recuperação leve falhou: {e}", "erro")
                    raise
                except Exception as e:
                    if check_stop():
                        break

                    falhas_leves += 1
                    log(f"Falha no item {i_global}: {type(e).__name__} - {e}", "aviso")

                    if sessao_expirada(driver):
                        log("A sessão gov.br caiu de fato — reinício completo é inevitável.", "erro")
                        raise
                    if falhas_leves > MAX_RECUPERACOES_LEVES:
                        log(f"{falhas_leves} falhas seguidas. Escalando para reinício completo.", "erro")
                        raise

                    log(f"Recuperação leve {falhas_leves}/{MAX_RECUPERACOES_LEVES}, sem captcha...")
                    recuperar_navegacao(driver, pagina)

        except Exception as e:
            log(f"Erro crítico na iteração {i_global}: {e}. Reiniciando o navegador...", "erro")
            if log_registros:
                save_or_concat(log_registros, save)
                log_registros = []
                try:
                    save = pd.read_excel(RELATORIO_PATH)
                except Exception:
                    save = None
            if driver:
                try:
                    driver.quit()
                except WebDriverException:
                    pass
                driver = None
            reinicios += 1
            inicializacoes += 1
            if check_stop():
                break
            time.sleep(10)
            continue

    if log_registros:
        save_or_concat(log_registros, save)

    if driver:
        try:
            driver.quit()
        except WebDriverException:
            pass

    if STOP_REQUESTED.is_set():
        log("Processo interrompido pelo usuário.", "aviso")
    else:
        log(f"Preenchimento concluído. {reinicios} reinicialização(ões) pesada(s).", "ok")

if __name__ == "__main__":
    run_filling()
