import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.cache import carregar_dados_basicos
from sponte_api_functions import (
    get_alunos_df, 
    get_turmas_df, 
    get_aulas_df,
    get_contas_receber_df,
    get_contas_pagar_df,
    get_fluxo_caixa_df
)

# Importar páginas
from pages.alunos import exibir_pagina_alunos
from pages.turmas import exibir_pagina_turmas
from pages.aulas import exibir_pagina_aulas

# Carregar variáveis de ambiente
load_dotenv()

# Verificar se as credenciais estão disponíveis
def verificar_credenciais():
    login = os.getenv('LOGIN')
    senha = os.getenv('SENHA')
    
    # Se as credenciais não estiverem no .env, verificar se foram configuradas no Streamlit Cloud
    if not login or not senha:
        # Tentar obter das variáveis de ambiente do Streamlit Cloud
        login = st.secrets.get("LOGIN", None) if hasattr(st, "secrets") else None
        senha = st.secrets.get("SENHA", None) if hasattr(st, "secrets") else None
        
        # Se encontrou as credenciais no st.secrets, definir como variáveis de ambiente
        if login and senha:
            os.environ['LOGIN'] = login
            os.environ['SENHA'] = senha
            return True
        else:
            return False
    return True

# Configuração da página
st.set_page_config(
    page_title="Dashboard Sponte",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ocultar menu nativo do Streamlit
hide_menu = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_menu, unsafe_allow_html=True)

# Verificar credenciais antes de exibir o conteúdo
if not verificar_credenciais():
    st.error("Credenciais não encontradas. Configure as variáveis LOGIN e SENHA no Streamlit Cloud ou no arquivo .env local.")
    st.info("Para configurar no Streamlit Cloud, vá para Configurações > Secrets e adicione as variáveis LOGIN e SENHA.")
    st.stop()

# Título principal
st.title("Dashboard Sponte")

# Sidebar para navegação e filtros
st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "Selecione uma página:",
    ["Turmas", "Alunos", "Aulas"],
    index=0
)

# Exibir página selecionada
if pagina == "Turmas":
    exibir_pagina_turmas()
elif pagina == "Alunos":
    exibir_pagina_alunos()
elif pagina == "Aulas":
    exibir_pagina_aulas()
