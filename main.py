import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui
import pandas as pd
import time
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# Configurações globais
PRE_INSTRUMENTO = 'XXXXX'  # INSERIR NUMERO DO INSTRUMENTO A SER EDITADO
PLANILHA_PATH = 'XXXXX'  # CAMPO DE INSERÇÃO DA PLANILHA ORÇAMENTARIA FORNECIDA PELA CONSTRUTORA
RELATORIO_PATH = f'relatorio_execucao-{PRE_INSTRUMENTO}.xlsx'
DEFAULT_TIMEOUT = 60  # Aumentado para lidar com SPA lenta
SIMILARITY_THRESHOLD = 0.65  # Limiar de similaridade para considerar como match
MAX_TRIES = 5  # Máximo de tentativas para matching antes de pular

# Função para calcular distância de Levenshtein
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

# Função para calcular similaridade baseada em Levenshtein
def similarity(s1, s2):
    s1 = s1.lower().strip().replace(' ', '').replace('.', '').replace('_', '').replace('/', '')
    s2 = s2.lower().strip().replace(' ', '').replace('.', '').replace('_', '').replace('/', '')
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1 - (distance / max_len) if max_len != 0 else 1.0

# Função para inicializar o driver
def init_driver():
    chrome_options = Options()
    driver = uc.Chrome(options=chrome_options, version_main=146)
    driver.execute_cdp_cmd('Storage.clearDataForOrigin', {"origin": '*', "storageTypes": 'all'})
    driver.get('https://portal.transferegov.sistema.gov.br/portal/home')
    return driver

# Função para tratar dados da planilha
def load_data():
    df = pd.read_excel(PLANILHA_PATH)
    df_filtrado = df[df.iloc[:, 4].notna()]
    df_filtrado = df_filtrado[df_filtrado.iloc[:, 4] != 0]
    descricoes = df_filtrado.iloc[:, 1].astype(str).tolist()
    precosUnit = df_filtrado.iloc[:, 4].astype(float).apply(lambda x: f"{x:.2f}").tolist()
    return descricoes, precosUnit

# Função para obter elementos frescos da página com timeout maior e retry
def get_fresh_edit_icons(driver):
    for _ in range(5):  # Mais retries
        try:
            return WebDriverWait(driver, DEFAULT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'i.fa.fa-pencil'))
            )
        except (StaleElementReferenceException, TimeoutException):
            time.sleep(2)
    raise TimeoutException("Falha ao obter ícones de edição após retries")

# Função genérica para clique via JS com mais retries e delay maior
def js_click(driver, css, action='click', text='', retries=10, delay=2):
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            if action == 'click':
                driver.execute_script("arguments[0].click();", element)
            elif action == 'write':
                driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element, text)
            return True
        except (StaleElementReferenceException, TimeoutException, ElementClickInterceptedException) as e:
            print(f"⚠️ Tentativa {attempt+1} falhou em {css}: {type(e).__name__} - {e}")
            time.sleep(delay)
    return False

# Função para clique via XPath com waits maiores
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
        print(f"⚠️ Erro em click_and_write para {path}: {e}")
        return False

# Função para navegar para uma página específica com handling melhorado
def go_to_page(driver, page_num):
    try:
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.pagination.paginacao')))
        
        pagination_buttons = driver.find_elements(By.CSS_SELECTOR, 'ul.pagination.paginacao li a')
        
        for button in pagination_buttons:
            if button.text.strip() == str(page_num + 1):
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                ActionChains(driver).move_to_element(button).click().perform()
                WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'i.fa.fa-pencil')))
                time.sleep(2)  # Delay adicional após navegação
                return True
        
        current_page = pagina_atual(driver)
        next_button_selector = 'ul.pagination.paginacao li:last-child a'
        for _ in range(page_num - current_page):
            next_button = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector)))
            driver.execute_script("arguments[0].click();", next_button)
            WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.staleness_of(next_button))
            WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'i.fa.fa-pencil')))
            time.sleep(2)  # Delay adicional
        return True
    except TimeoutException:
        print(f"Timeout ao navegar para página {page_num+1}")
        return False
    except Exception as e:
        print(f"Erro ao navegar para página {page_num+1}: {e}")
        return False

# Função auxiliar para obter página atual com retry
def pagina_atual(driver):
    try:
        active_page = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.pagination.paginacao li.active a')))
        return int(active_page.text.strip()) - 1
    except:
        return 0

# Função para manejar popup de reinício de sessão com timeout menor para checagem rápida
def handle_session_popup(driver):
    try:
        popup_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn.btn-primary[type="button"]')))
        if popup_button.text.strip() == 'Sim':
            print("🛡️ Detectado popup de reinício de sessão. Clicando em 'Sim'...")
            popup_button.click()
            WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'button.btn.btn-primary[type="button"]')))
            return True
    except TimeoutException:
        return False
    except Exception as e:
        print(f"Erro ao manejar popup: {e}")
        return False

# Função para navegação inicial e login com verificações e delays
def navigate_and_login(driver):
    try:
        if not click_and_write(driver, '/html/body/portal-root/br-main-layout/div/div/div/main/portal-main/div/div[2]/div[2]/card/div/div/div[3]/button', 'click'):
            raise Exception("Falha ao clicar no botão inicial")
        time.sleep(1)  # Delay para SPA
        if not click_and_write(driver, '//*[@id="form_submit_login"]', 'click'):
            raise Exception("Falha ao clicar no submit login")
        time.sleep(1)

        pyautogui.alert('Por favor, faça o login e realize o captcha. Em seguida, pressione OK para continuar')

        if not click_and_write(driver, '//*[@id="menuPrincipal"]/div[1]/div[4]', 'click'):
            raise Exception("Falha ao clicar no menu principal")
        time.sleep(1)
        if not click_and_write(driver, '//*[@id="contentMenu"]/div[1]/ul/li[11]/a', 'click'):
            raise Exception("Falha ao clicar no item de menu")
        time.sleep(1)
        if not click_and_write(driver, '//*[@id="consultarNumeroConvenio"]', 'write', PRE_INSTRUMENTO):
            raise Exception("Falha ao escrever número do convênio")
        time.sleep(1)
        if not click_and_write(driver, '//*[@id="form_submit"]', 'click'):
            raise Exception("Falha ao submeter formulário")
        time.sleep(1)
        if not click_and_write(driver, '//*[@id="instrumentoId"]/a', 'click'):
            raise Exception("Falha ao clicar no instrumento ID")
        time.sleep(1)

        if not click_and_write(driver, '//*[@id="div_-481524888"]/span', 'click'):
            raise Exception("Falha ao clicar na div span")
        time.sleep(1)
        if not click_and_write(driver, '//*[@id="menu_link_-481524888_-333124204"]/div/span/span', 'click'):
            raise Exception("Falha ao clicar no menu link")
        time.sleep(1)

        if not js_click(driver, 'a[title="Exibir Dados Detalhados"]'):
            raise Exception("Falha ao clicar em Exibir Dados Detalhados")
        time.sleep(1)
        if not js_click(driver, 'a[title="Planilhas Orçamentárias / Cronogramas Físico Financeiro"]'):
            raise Exception("Falha ao clicar em Planilhas Orçamentárias")
        time.sleep(1)

        metas = get_fresh_edit_icons(driver)
        meta = metas[0]
        icone_meta = meta.find_element(By.XPATH, './parent::a')
        driver.execute_script('arguments[0].click()', icone_meta)
        time.sleep(1)

        if not js_click(driver, 'a[title="Planilha Orçamentária"]'):
            raise Exception("Falha ao clicar em Planilha Orçamentária")
        time.sleep(1)

        WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'i.fa.fa-pencil')))

        print('Iniciando preenchimento!!!!')
        return True
    except Exception as e:
        print(f"Erro durante navegação/login: {e}")
        return False

# Função para salvar ou concatenar relatório
def save_or_concat(log_registros, save):
    df_log = pd.DataFrame(log_registros)
    if save is not None:
        new_report = pd.read_excel(RELATORIO_PATH)
        df_concat = pd.concat([new_report, df_log])
        df_concat.to_excel(RELATORIO_PATH, index=False)
    else:
        df_log.to_excel(RELATORIO_PATH, index=False)
    print(f"📊 Relatório salvo em {RELATORIO_PATH}")

# Loop principal com reinício automático
descricoes, precosUnit = load_data()
log_registros = []

# Carregar progresso salvo
try:
    save = pd.read_excel(RELATORIO_PATH)
    save_index_per_page = int(save.iloc[-1, 1])
    save_general_index = int(save.iloc[-1, 0])
    save_page = int(save.iloc[-1, 2])
    i = save_index_per_page
    i_global = save_general_index
    pagina = save_page
    print(f"Ponto salvo encontrado! Iniciando da iteração {i_global}, página {pagina+1}, item {i+1}")
except FileNotFoundError:
    save = None
    i = 0
    i_global = 0
    pagina = 0
    print("Ponto salvo não encontrado! Iniciando do zero.")
except Exception as e:
    print(f"Erro ao carregar save: {e}")
    save = None
    i = 0
    i_global = 0
    pagina = 0

while i_global < len(descricoes):
    driver = None
    try:
        driver = init_driver()
        if not navigate_and_login(driver):
            raise Exception("Falha na navegação/login inicial")
        
        while i_global < len(descricoes):
            handle_session_popup(driver)
            
            if not go_to_page(driver, pagina):
                raise TimeoutException("Falha ao navegar para página")
            
            icones_editar = get_fresh_edit_icons(driver)
            
            if i >= len(icones_editar):
                print(f"🌐 Fim dos elementos na página {pagina+1}. Avançando...")
                pagina += 1
                i = 0
                continue
            
            tentativas = 0
            while True:
                for attempt in range(5):  # Tentativas para clicar no editar
                    try:
                        icones_editar = get_fresh_edit_icons(driver)
                        icone = icones_editar[i]
                        link_editar = icone.find_element(By.XPATH, './parent::a')
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_editar)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", link_editar)
                        break
                    except StaleElementReferenceException as e:
                        print(f"🔄 Elemento stale na iteração {i_global}, tentativa {attempt+1}: {e}")
                        time.sleep(3)
                else:
                    raise StaleElementReferenceException("Falha persistente em stale element ao clicar edit")

                time.sleep(3)  # Delay para form carregar
                
                handle_session_popup(driver)
                
                try:
                    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="precoUnitarioLicitado"]')))
                except TimeoutException as e:
                    print(f"Timeout esperando campo de preço unitário: {e}")
                    raise
                
                valor_atual = driver.execute_script("return document.querySelector('input[formcontrolname=\"precoUnitarioLicitado\"]').value;")
                descricao_site = driver.execute_script("return document.querySelector('p[id=\"descricao\"]').innerText;")
                
                print(f"🗒️ Iteração {i_global}: Descrição site -> {descricao_site}")
                print(f"🗒️ Iteração {i_global}: Descrição planilha -> {descricoes[i_global]}")
                
                # Calcular similaridade
                sim = similarity(descricao_site, descricoes[i_global])
                print(f"📏 Similaridade Levenshtein: {sim:.2f}")
                
                if sim >= SIMILARITY_THRESHOLD:
                    print('✅ Descrições semelhantes o suficiente.')
                    
                    print(f"🖌️ Iteração {i_global}: Substituindo {valor_atual} por {precosUnit[i_global]}...")
                    
                    if not js_click(driver, 'input[formcontrolname="precoUnitarioLicitado"]', 'write', precosUnit[i_global]):
                        raise Exception("Falha ao escrever valor")
                    
                    print(f"✅ Iteração {i_global}: Valor inserido com sucesso!")
                    time.sleep(2)
                    
                    if not js_click(driver, 'button[class="btn btn-primary"]'):
                        raise Exception("Falha ao clicar em salvar")
                    
                    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.visibility_of_element_located((By.CLASS_NAME, 'table')))
                    time.sleep(2)  # Delay adicional após salvar
                    
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
                        "Obs": ""
                    })
                    
                    i += 1
                    i_global += 1
                    break  # Sai do loop de tentativas
                    
                else:
                    obs = f"Descrições divergentes (similaridade {sim:.2f} < {SIMILARITY_THRESHOLD})"
                    print(f'⚠️ Atenção. {obs}! Favor verificar. Tentando novamente após voltar...')
                    
                    # Clique no botão "Voltar" específico
                    if not js_click(driver, 'button.btn.btn-secondary.botao-voltar'):
                        print("Falha ao clicar no botão Voltar com .btn.btn-secondary.botao-voltar. Tentando fallback...")
                        js_click(driver, 'button.botao-voltar')
                    
                    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.visibility_of_element_located((By.CLASS_NAME, 'table')))
                    time.sleep(2)  # Delay após voltar
                    
                    # Log da tentativa falha
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
                        "Obs": obs + f" - Tentativa {tentativas + 1}"
                    })
                    
                    tentativas += 1
                    if tentativas >= MAX_TRIES:
                        print(f"🚫 Máximo de tentativas ({MAX_TRIES}) atingido para iteração {i_global}. Pulando item...")
                        log_registros[-1]["Status"] = "SKIPPED"
                        log_registros[-1]["Obs"] += " - Pulado após max tentativas"
                        i += 1
                        i_global += 1
                        break
                    # Continua o loop para tentar novamente o mesmo item
            
            if i_global % 10 == 0:
                save_or_concat(log_registros, save)
                log_registros = []
                save = pd.read_excel(RELATORIO_PATH)
        
    except Exception as e:
        print(f"⚠️ Erro crítico na iteração {i_global}: {e}. Reiniciando processo...")
        if log_registros:
            save_or_concat(log_registros, save)
            log_registros = []
        if driver:
            driver.quit()
        time.sleep(10)  # Delay maior antes de reiniciar
        continue

# Salvar relatório final
if log_registros:
    save_or_concat(log_registros, save)

if driver:
    driver.quit()