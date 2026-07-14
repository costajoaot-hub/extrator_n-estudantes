# -*- coding: utf-8 -*-
"""
Script para extração do número de estudantes inscritos em Unidades Curriculares (UCs)
no portal Sigarra da FEUP para o ano letivo de determinado.
"""

import os
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# =================================================================
# CONFIGURAÇÕES DE CAMINHOS (Editável)
# =================================================================
# Por padrão, o script procura os ficheiros na mesma pasta onde é executado.
# Se preferires usar o teu caminho absoluto local, podes descomentar a linha abaixo:
# CAMINHO_PASTA = r"C"
CAMINHO_PASTA = os.path.dirname(os.path.abspath(__file__))

FICHEIRO_ENTRADA = os.path.join(CAMINHO_PASTA, "File01.xlsx")
FICHEIRO_SAIDA = os.path.join(CAMINHO_PASTA, "File01_Processado.xlsx")
# =================================================================

def iniciar_chrome_limpo():
    """Inicia uma instância isolada do Chrome para evitar conflitos de perfil."""
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    
    # Define uma pasta temporária para o perfil de navegação dentro do diretório do projeto
    caminho_temporario = os.path.join(CAMINHO_PASTA, ".selenium_profile")
    chrome_options.add_argument(f'--user-data-dir={caminho_temporario}')
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    servico = Service(ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=chrome_options)
    return navegador

def extrair_estudantes_de_ficha(navegador, url_ficha):
    """Acede à ficha de uma ocorrência específica e extrai o número de estudantes inscritos."""
    navegador.get(url_ficha)
    time.sleep(1.5)
    
    soup = BeautifulSoup(navegador.page_source, 'html.parser')
    tabelas = soup.find_all('table')
    
    for tabela in tabelas:
        headers = [th.get_text(strip=True).lower() for th in tabela.find_all('th')]
        termos_pesquisa = ["nº de estudantes", "n.º de estudantes", "num_estudantes", "estudantes"]
        matching_header = [h for h in headers if any(termo in h for termo in termos_pesquisa)]
        
        if matching_header:
            idx_col = headers.index(matching_header[0])
            rows = tabela.find_all('tr')
            for r in rows:
                cols = r.find_all('td')
                if len(cols) > idx_col:
                    valor = cols[idx_col].get_text(strip=True)
                    if valor.isdigit():
                        return int(valor)
    return 0

def extrair_estudantes_uc(navegador, codigo_uc):
    """Submete a pesquisa da UC, obtém todos os links das ocorrências e faz o somatório."""
    url_pesquisa = "https://sigarra.up.pt/feup/pt/ucurr_geral.pesquisa_ucs?pv_tipo="
    navegador.get(url_pesquisa)
    
    try:
        WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except:
        pass
        
    time.sleep(1.5)
    
    try:
        # 1. Forçar seleção do Ano Letivo 20##/20##
        select_ano_elem = navegador.find_element(By.XPATH, "//select[contains(@name, 'pv_ano_lectivo') or contains(@name, 'ano') or option[text()='2024/2025']]")
        select_ano = Select(select_ano_elem)
        select_ano.select_by_visible_text("20##/20##")
        
        # 2. Inserir o Código da UC
        input_codigo = navegador.find_element(By.XPATH, "//input[contains(@name, 'pv_codigo') or contains(@name, 'codigo')]")
        input_codigo.clear()
        input_codigo.send_keys(codigo_uc)
        
        # Submeter formulário de pesquisa
        input_codigo.submit()
        time.sleep(2.5) # Tempo de espera para abrir a página intermédia de resultados
        
        # 3. Capturar o HTML da página intermédia (pesquisa_ocorr_ucs_list)
        soup = BeautifulSoup(navegador.page_source, 'html.parser')
        
        # Procuramos todos os links que levam à ficha de visualização da UC contendo o ID da ocorrência
        links_encontrados = soup.find_all('a', href=re.compile(r'ficha_uc_view\?pv_ocorrencia_id='))
        
        links_ocorrencias = []
        for link in links_encontrados:
            href = link.get('href')
            if not href.startswith('http'):
                href = "https://sigarra.up.pt/feup/pt/" + href
            
            if href not in links_ocorrencias:
                links_ocorrencias.append(href)
                
        if not links_ocorrencias:
            if "ficha_uc_view" in navegador.current_url:
                print(f"    -> Redirecionamento direto para a ficha de UC detetado.")
                return extrair_estudantes_de_ficha(navegador, navegador.current_url)
            print(f"    -> Aviso: Nenhuma ocorrência ou link encontrado para a UC {codigo_uc}.")
            return "Não Encontrado"
            
        print(f"    -> Detetadas {len(links_ocorrencias)} ocorrência(s) de semestre para {codigo_uc}.")
        
        # 4. Visitar cada semestre (ocorrência) e fazer a soma total
        total_estudantes = 0
        for idx_oc, url_oc in enumerate(links_ocorrencias):
            print(f"       A ler ocorrência {idx_oc+1}/{len(links_ocorrencias)}...")
            qtd = extrair_estudantes_de_ficha(navegador, url_oc)
            total_estudantes += qtd
            
        return total_estudantes
                
    except Exception as e:
        print(f"    -> Erro crítico ao processar UC {codigo_uc}: {e}")
        return "Erro na Pesquisa"

def processar_lista_estudantes():
    print(f"A ler o ficheiro: {FICHEIRO_ENTRADA}...")
    if not os.path.exists(FICHEIRO_ENTRADA):
        print(f"Erro: Ficheiro não encontrado em: {FICHEIRO_ENTRADA}")
        return

    df = pd.read_excel(FICHEIRO_ENTRADA)
    coluna_uc = df.columns[0] # Assume a 1ª coluna do ficheiro
        
    print(f"Coluna identificada para códigos das UCs: '{coluna_uc}'")
    
    navegador = iniciar_chrome_limpo()
    
    lista_inscritos = []
    total = len(df)
    
    # --- PASSO DO LOGIN (60 Segundos para Autenticação e MFA) ---
    navegador.get("https://sigarra.up.pt/feup/pt/web_page.inicial")
    print("\n" + "="*70)
    print("[AUTENTICAÇÃO] Uma nova janela do Chrome acabou de se abrir.")
    print("Por favor, FAÇA LOGIN no Sigarra usando as suas credenciais da FEUP.")
    print("Tem 60 segundos para efetuar o login e a dupla autenticação (MFA)...")
    print("="*70 + "\n")
    
    for tempo_restante in range(60, 0, -10):
        print(f"Restam {tempo_restante} segundos para efetuar o login...")
        time.sleep(10)
    
    print(f"\nTempo de autenticação esgotado. A iniciar a extração de {total} UCs...")

    for idx, row in df.iterrows():
        codigo_uc = str(row[coluna_uc]).strip()
        
        if codigo_uc and not pd.isna(row[coluna_uc]) and codigo_uc.lower() not in ['nan', 'none', '']:
            print(f"[{idx+1}/{total}] A processar a UC: {codigo_uc}...")
            num_inscritos = extrair_estudantes_uc(navegador, codigo_uc)
            print(f"    -> SOMA TOTAL de inscritos: {num_inscritos}")
        else:
            print(f"[{idx+1}/{total}] Linha vazia ou inválida.")
            num_inscritos = "N/A"
            
        lista_inscritos.append(num_inscritos)
        
        # Salvaguarda incremental de dados em tempo real no Excel de saída
        df_temp = df.copy()
        df_temp.loc[:len(lista_inscritos)-1, 'N_ESTUD_INSCR'] = lista_inscritos
        df_temp.to_excel(FICHEIRO_SAIDA, index=False)
        
    navegador.quit()
    
    # Guardar o resultado final consolidado
    df['N_ESTUD_INSCR'] = lista_inscritos
    df.to_excel(FICHEIRO_SAIDA, index=False)
    print("-" * 50)
    print(f"PROCESSO CONCLUÍDO! O ficheiro atualizado foi guardado em:\n{FICHEIRO_SAIDA}")

if __name__ == "__main__":
    processar_lista_estudantes()
