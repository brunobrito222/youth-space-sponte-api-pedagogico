import streamlit as st
from datetime import datetime, timedelta

def criar_sidebar():
    """
    Cria a barra lateral com navegação e filtros globais
    
    Returns:
        tuple: (página selecionada, data_inicio, data_fim)
    """
    st.sidebar.title("Navegação")
    pagina = st.sidebar.radio(
        "Selecione uma página:",
        ["Dashboard", "Alunos", "Turmas", "Financeiro", "Aulas"]
    )
    
    # Filtros globais
    st.sidebar.title("Filtros")
    data_inicio = st.sidebar.date_input(
        "Data Inicial",
        datetime.now() - timedelta(days=30)
    )
    data_fim = st.sidebar.date_input(
        "Data Final",
        datetime.now()
    )
    
    return pagina, data_inicio, data_fim
