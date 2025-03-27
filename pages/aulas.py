import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.cache import carregar_dados_aulas
from datetime import datetime, timedelta

def exibir_pagina_aulas(data_inicio=None, data_fim=None):
    """
    Exibe a página de gestão de aulas
    
    Args:
        data_inicio (datetime.date, optional): Data inicial para filtro
        data_fim (datetime.date, optional): Data final para filtro
    """
    st.header("Gestão de Aulas")
    
    # Obtém a data atual
    data_atual = datetime.now().date()
    
    # Filtros para aulas no topo da página em duas colunas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data_aula_inicio = st.date_input(
            "Data Inicial",
            value=data_atual,  # Por padrão mostra aulas do dia atual
            key="aula_data_inicio"
        )
    
    with col2:
        data_aula_fim = st.date_input(
            "Data Final",
            value=data_atual,  # Por padrão mostra aulas do dia atual
            key="aula_data_fim"
        )
    
    with col3:
        # Filtro de situação da aula
        situacao_opcoes = [
            ("Todas", -1),
            ("Confirmadas", 1),
            ("Pendentes", 0)
        ]
        
        situacao_index = 1  # Índice para "Confirmadas" como valor padrão
        situacao = st.selectbox(
            "Situação da Aula",
            options=situacao_opcoes,
            format_func=lambda x: x[0],
            index=situacao_index
        )
    
    # Botão para aplicar filtros
    filtrar = st.button("Aplicar Filtros", type="primary")
    
    # Inicializa o DataFrame vazio para evitar erros caso nenhum filtro seja aplicado ainda
    if 'df_aulas' not in st.session_state:
        st.session_state.df_aulas = pd.DataFrame()
    
    # Separador visual
    st.divider()
    
    # Carregar dados das aulas somente após clicar no botão
    if filtrar:
        with st.spinner("Carregando aulas..."):
            st.session_state.df_aulas = carregar_dados_aulas(
                data_inicio=data_aula_inicio.strftime("%Y-%m-%d"),
                data_fim=data_aula_fim.strftime("%Y-%m-%d"),
                situacao=situacao[1]
            )
            
            # Processar informações de presenças e faltas
            if 'alunos' in st.session_state.df_aulas.columns:
                # Adicionar colunas de contagem de presenças e faltas
                presenças = []
                faltas = []
                
                for i, row in st.session_state.df_aulas.iterrows():
                    if isinstance(row['alunos'], list):
                        # Contar presenças e faltas
                        num_presencas = sum(1 for aluno in row['alunos'] if aluno.get('presenca') == 'Presenca')
                        num_faltas = sum(1 for aluno in row['alunos'] if aluno.get('presenca') == 'Falta')
                        
                        presenças.append(num_presencas)
                        faltas.append(num_faltas)
                    else:
                        presenças.append(0)
                        faltas.append(0)
                
                # Adicionar as colunas ao DataFrame
                st.session_state.df_aulas['num_presencas'] = presenças
                st.session_state.df_aulas['num_faltas'] = faltas
            
            # Criar identificador único para cada aula (combinação de turmaID e dataAula)
            if 'turmaID' in st.session_state.df_aulas.columns and 'dataAula' in st.session_state.df_aulas.columns:
                # Converter dataAula para string caso não seja
                if st.session_state.df_aulas['dataAula'].dtype != 'object':
                    st.session_state.df_aulas['dataAula'] = st.session_state.df_aulas['dataAula'].astype(str)
                
                # Criar a coluna de ID único
                st.session_state.df_aulas['aula_id_unico'] = st.session_state.df_aulas['turmaID'].astype(str) + '_' + st.session_state.df_aulas['dataAula']
                
                # Remover duplicatas mantendo a primeira ocorrência
                contagem_antes = len(st.session_state.df_aulas)
                st.session_state.df_aulas = st.session_state.df_aulas.drop_duplicates(subset=['aula_id_unico'])
                contagem_depois = len(st.session_state.df_aulas)
                
                # Informar sobre as duplicatas removidas (apenas para debug)
                duplicatas_removidas = contagem_antes - contagem_depois
                if duplicatas_removidas > 0:
                    st.session_state.duplicatas_removidas = duplicatas_removidas
            
            st.session_state.aulas_filtradas = True
    
    # Exibir dados das aulas
    if not st.session_state.df_aulas.empty:
        # Exibir contagem de aulas
        st.subheader(f"Total de aulas: {len(st.session_state.df_aulas)}")
        
        # Selecionar colunas relevantes para exibição (excluindo a coluna de ID único)
        colunas_exibir = ['dataAula', 'turmaID', 'nomeProfessor', 'situacao', 'num_presencas', 'num_faltas']
        colunas_disponiveis = [col for col in colunas_exibir if col in st.session_state.df_aulas.columns]
        df_exibir = st.session_state.df_aulas[colunas_disponiveis].copy()
        
        # Renomear colunas para melhor visualização
        mapeamento_colunas = {
            'dataAula': 'Data da Aula',
            'turmaID': 'ID da Turma',
            'nomeProfessor': 'Nome do Professor',
            'situacao': 'Situação',
            'num_presencas': 'Presenças',
            'num_faltas': 'Faltas'
        }
        df_exibir = df_exibir.rename(columns={col: mapeamento_colunas.get(col, col) for col in df_exibir.columns})
        
        # Exibir tabela
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
        
        # Análises dos dados de aulas
        st.subheader("Análises")
        
        # Gráfico de aulas por professor
        if 'Nome do Professor' in df_exibir.columns:
            try:
                contagem_professor = df_exibir['Nome do Professor'].value_counts().reset_index()
                contagem_professor.columns = ['Nome do Professor', 'Quantidade de Aulas']
                
                fig = px.bar(
                    contagem_professor,
                    x='Nome do Professor',
                    y='Quantidade de Aulas',
                    title='Quantidade de Aulas por Professor',
                    labels={'Nome do Professor': '', 'Quantidade de Aulas': ''},
                    color='Quantidade de Aulas'
                )
                
                # Remover os títulos dos eixos
                fig.update_layout(
                    xaxis_title=None,
                    yaxis_title=None,
                    coloraxis_showscale=False  # Remover a escala de cor
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar gráfico de aulas por professor: {str(e)}")
        
        # Gráfico de aulas por situação
        if 'Situação' in df_exibir.columns:
            try:
                contagem_situacao = df_exibir['Situação'].value_counts().reset_index()
                contagem_situacao.columns = ['Situação', 'Quantidade']
                
                fig = px.pie(
                    contagem_situacao,
                    values='Quantidade',
                    names='Situação',
                    title='Distribuição de Aulas por Situação'
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar gráfico de aulas por situação: {str(e)}")
        
        # Gráfico de faltas por professor
        if 'Nome do Professor' in df_exibir.columns and 'Faltas' in df_exibir.columns and 'Presenças' in df_exibir.columns:
            try:
                # Agrupar faltas e presenças por professor
                dados_professor = df_exibir.groupby('Nome do Professor').agg({
                    'Faltas': 'sum',
                    'Presenças': 'sum'
                }).reset_index()
                
                # Calcular o total de alunos e o percentual de faltas
                dados_professor['Total Alunos'] = dados_professor['Faltas'] + dados_professor['Presenças']
                dados_professor['Percentual de Faltas'] = (dados_professor['Faltas'] / dados_professor['Total Alunos'] * 100).round(1)
                
                # Ordenar pelo percentual de faltas (decrescente)
                dados_professor = dados_professor.sort_values('Percentual de Faltas', ascending=False)
                
                # Criar o gráfico de barras com percentual
                fig = px.bar(
                    dados_professor,
                    x='Nome do Professor',
                    y='Percentual de Faltas',
                    title='Percentual de Faltas por Professor',
                    labels={'Nome do Professor': '', 'Percentual de Faltas': ''},
                    color='Percentual de Faltas',
                    text='Percentual de Faltas'  # Mostrar o valor no gráfico
                )
                
                # Ajustar o layout para mostrar o percentual com símbolo %
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                
                # Ajustar o eixo Y para percentual e remover títulos dos eixos
                fig.update_layout(
                    yaxis=dict(ticksuffix='%'),
                    xaxis_title=None,
                    yaxis_title=None,
                    coloraxis_showscale=False  # Remover a escala de cor
                )
                
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar gráfico de percentual de faltas por professor: {str(e)}")
    else:
        if 'aulas_filtradas' in st.session_state:
            st.info("Não foram encontradas aulas para o período e situação selecionados.")
        else:
            st.info("Clique em 'Aplicar Filtros' para carregar as aulas com os critérios selecionados.")
