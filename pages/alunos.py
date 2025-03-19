from operator import index
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.cache import carregar_dados_alunos

def exibir_pagina_alunos():
    """
    Exibe a página de gestão de alunos
    """
    st.header("Gestão de Alunos")
    
    iniciar_alunos = st.button("Carregar dados de alunos", type="primary")

    if iniciar_alunos:
        # Carregar dados dos alunos (apenas ativos) usando a função com cache
        with st.spinner("Carregando alunos..."):
            df_alunos = carregar_dados_alunos(situacao=-1)  # Apenas alunos ativos
        
        # Exibir contagem de alunos
        st.subheader(f"Total de alunos ativos: {len(df_alunos)}")
        
        # Exibir tabela de alunos
        if not df_alunos.empty:
            # Selecionar colunas relevantes para exibição
            colunas_exibir = ['alunoID', 'nomeAluno', 'emailPadrao', 'dataNascimento', 'telefone', 'telefoneComercial', 'celular', 'responsavelFinanceiroID', 'situacao']
            
            # Verificar quais colunas existem no dataframe
            colunas_disponiveis = [col for col in colunas_exibir if col in df_alunos.columns]
            df_exibir = df_alunos[colunas_disponiveis].copy()
            
            # Renomear colunas para melhor visualização
            mapeamento_colunas = {
                'alunoID': 'ID do Aluno',
                'nomeAluno': 'Nome do Aluno',
                'emailPadrao': 'E-mail',
                'dataNascimento': 'Data de Nascimento',
                'telefone': 'Telefone',
                'telefoneComercial': 'Telefone Comercial',
                'celular': 'Celular',
                'responsavelFinanceiroID': 'ID do Responsável Financeiro',
                'situacao': 'Situação'
            }
            df_exibir = df_exibir.rename(columns=mapeamento_colunas)
            
            # Exibir tabela
            st.dataframe(df_exibir, use_container_width=True, hide_index=True)
        else:
            st.info("Não há alunos para exibir.")

    else:
        st.info("Clique em 'Carregar dados de alunos' para carregar os dados.")