import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui
import pandas as pd
import time
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# Abertura do browser
driver = uc.Chrome()
driver.execute_cdp_cmd('Storage.clearDataForOrigin', {"origin": '*', "storageTypes": 'all'})
driver.get('https://portal.transferegov.sistema.gov.br/portal/home')

# Trata dados da planilha
df = pd.read_excel('XXXXXX.xlsx') # Planilha na qual serão buscados os dados
df_filtrado = df[df.iloc[:, 4].notna()]
df_filtrado = df_filtrado[df_filtrado.iloc[:, 4] != 0]
descricoes = df_filtrado.iloc[:, 1].astype(str).tolist()
precosUnit = df_filtrado.iloc[:, 4].astype(float).apply(lambda x: f"{x:.2f}").tolist()

log_registros = []

def clickAndWrite(Path, action, text=''):
    wait = WebDriverWait(driver, 15)
    element = wait.until(EC.element_to_be_clickable((By.XPATH, Path)))
    if action == 'click':
        element.click()
    if action == 'write':
        element.clear()
        for letter in text:
            element.send_keys(letter)

def js_click(css, action='click', text='', delay=100, tentativas=10):
    for t in range(tentativas):
        try:
            wait = WebDriverWait(driver, 20)
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
            if action == 'click':
                driver.execute_script("arguments[0].click();", element)
            elif action == 'write':
                driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element, text)
            return True
        except Exception as e:
            print(f"⚠️ Tentativa {t+1} falhou em {css}: {e}")
            if t == tentativas - 1:
                raise
    return False

preInstrumento = 'XXXXX' # NUmero de pre-instrumento a ser preenchido

clickAndWrite('/html/body/portal-root/br-main-layout/div/div/div/main/portal-main/div/div[2]/div[2]/card/div/div/div[3]/button', 'click')
clickAndWrite('//*[@id="form_submit_login"]', 'click')

pyautogui.alert('Por favor, faça o login e realize o captcha. Em seguida, pressione OK para continuar')

clickAndWrite('//*[@id="menuPrincipal"]/div[1]/div[4]', 'click')
clickAndWrite('//*[@id="contentMenu"]/div[1]/ul/li[11]/a', 'click')
clickAndWrite('//*[@id="consultarNumeroConvenio"]', 'write', preInstrumento)
clickAndWrite('//*[@id="form_submit"]', 'click')
clickAndWrite('//*[@id="instrumentoId"]/a', 'click')

clickAndWrite('//*[@id="div_-481524888"]/span', 'click')
clickAndWrite('//*[@id="menu_link_-481524888_-333124204"]/div/span/span', 'click')

js_click('a[title="Exibir Dados Detalhados"]')
js_click('a[title="Planilhas Orçamentárias / Cronogramas Físico Financeiro"]')
js_click('a[title="Editar"]')
js_click('a[title="Planilha Orçamentária"]')

print('Iniciando preenchimento!!!!')

# Sistema de Save/Load
try:
    save = pd.read_excel(f'relatorio_execucao-{preInstrumento}.xlsx')
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
    print(f"Ponto salvo não encontrado! Iniciando da iteração {i}")
except Exception as e:
    print(f"Erro inesperado: {e}")


# Função para salvar ou concatenar o relatório
def saveOrConcat(savedFile):
    df_log = pd.DataFrame(log_registros)

    if savedFile is not None:
        new_Report = pd.read_excel(f'relatorio_execucao-{preInstrumento}.xlsx')
        df_concat = pd.concat([new_Report, df_log])
        df_concat.to_excel(f"relatorio_execucao-{preInstrumento}.xlsx", index=False)
    else:
        df_log.to_excel(f"relatorio_execucao-{preInstrumento}.xlsx", index=False)
        savedFile = pd.read_excel(f'relatorio_execucao-{preInstrumento}.xlsx')

    print(f"📊 Relatório salvo em relatorio_execucao-{preInstrumento}.xlsx")

# Função para navegar para uma página específica
def go_to_page(page_num):
    try:
        # Encontra todos os botões de paginação
        pagination_buttons = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ul.pagination.paginacao li a'))
        )
        
        # Tenta encontrar o botão com o número da página
        for button in pagination_buttons:
            if button.text.strip() == str(page_num + 1):  # +1 porque as páginas começam em 1
                driver.execute_script('arguments[0].click()', button)
                time.sleep(1)  # Espera a página carregar
                return True
        
        # Se não encontrou o botão específico, tenta usar o padrão [Previous] 1, 2, 3 [Next]
        if page_num + 2 < len(pagination_buttons):
            driver.execute_script('arguments[0].click()', pagination_buttons[page_num + 2])
            time.sleep(1)
            return True
            
        return False
    except TimeoutException:
        print(f"Timeout ao tentar navegar para a página {page_num+1}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao navegar para a página {page_num+1}: {e}")
        return False

# Função para obter elementos frescos da página
def get_fresh_edit_icons():
    return WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'i.fa.fa-pencil'))
    )

while i_global < len(descricoes):
    try:
        # Navega para a página correta
        if not go_to_page(pagina):
            print(f"Não foi possível navegar para a página {pagina+1}")
            break

        # Pra confirmar que vai pra outra pagina mesmo
        go_to_page(pagina)
            
        # Obter elementos frescos
        icones_editar = get_fresh_edit_icons()
        
        # Verifica se ainda há elementos para editar nesta página
        if i >= len(icones_editar):
            print(f"🌐 Fim dos elementos nesta página, indo para a pagina {pagina + 1}. Indice que estavamos: {i}, de {len(icones_editar)}")
            pagina += 1
            i = 0
            continue

        # Tenta clicar no elemento de edição
        try:
            icone = icones_editar[i]
            link_editar = icone.find_element(By.XPATH, './parent::a')
            driver.execute_script('arguments[0].click()', link_editar)
        except StaleElementReferenceException:
            print(f"🔄 Elemento obsoleto na iteração {i_global}, tentando novamente...")
            time.sleep(1)
            continue

        # Preenchimento
        valor_atual = driver.execute_script("return document.querySelector('input[formcontrolname=\"precoUnitarioLicitado\"]').value;")
        descricao_Site = driver.execute_script("return document.querySelector('p[id=\"descricao\"]').innerText;")
        print(f"🗒️ Iteração {i_global}: Descrição site -> {descricao_Site}")
        print(f"🗒️ Iteração {i_global}: Descrição planilha -> {descricoes[i_global]}")
        print(f"🖌️ Iteração {i_global}: Substituindo {valor_atual} por {precosUnit[i_global]}...")

        if descricao_Site.lower().replace(' ', '') not in descricoes[i_global].lower().replace(' ', ''):
            print('⚠️ Atenção. Descrições divergentes!! Favor verificar.')

        js_click('input[formcontrolname="precoUnitarioLicitado"]', 'write', precosUnit[i_global])
        print(f"✅ Iteração {i_global}: Valor inserido com sucesso!")
        time.sleep(1)
        js_click('button[class="btn btn-primary"]')

        # Espera a operação ser concluída e a página voltar para a primeira página
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'table')))
        
        # Volta para a página correta após o salvamento
        if not go_to_page(pagina):
            print(f"Não foi possível voltar para a página {pagina+1} após salvar. Tentando novamente...")
            break

        log_registros.append({
            "Iteração Geral": i_global,
            "Iteração na pagina": i,
            "Pagina": pagina,
            "Descricao_Site": descricao_Site,
            "Descricao_Planilha": descricoes[i_global],
            "Preco_Atual": valor_atual,
            "Preco_Novo": precosUnit[i_global],
            "Status": "OK" if descricao_Site and precosUnit[i_global] else "ERRO",
            "Obs": "Descrições divergentes" if descricao_Site.lower().replace(' ', '') not in descricoes[i_global].lower().replace(' ', '') else ""
        })

        i += 1
        i_global += 1

        # Salvar progresso a cada 10 iterações
        if i_global % 10 == 0:
            saveOrConcat(save)

    except Exception as e:
        print(f"⚠️ Erro na iteração {i_global}: {e}")
        # Salvar progresso em caso de erro
        saveOrConcat(save)
        
        # Decidir se continua ou para basedo no tipo de erro
        if "stale element reference" in str(e).lower():
            print("Tentando recuperar de elemento obsoleto...")
            time.sleep(1)
            continue
        else:
            # Para outros erros, pode querer parar ou continuar
            break

# Salvar relatório final
saveOrConcat(save)

driver.quit()