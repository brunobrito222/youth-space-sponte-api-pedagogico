import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.cache import carregar_dados_turmas, carregar_dados_basicos, carregar_dados_financeiros_turma_individual
from datetime import datetime, timedelta
import numpy as np

def exibir_pagina_turmas():
    st.header("Gestão de Turmas")
    
    # Carregar dados básicos - utilizados no dashboard e em outras funções
    with st.spinner("Carregando dados. Aguarde um minuto"):
        df_alunos_todas, df_turmas_todas, df_aulas_todas = carregar_dados_basicos()
    
    # Filtros
    # Filtro de situação da turma
    situacoes = [
        (1, "Abertas"),
        (3, "Em Formação")
    ]
    
    # Criar colunas para os filtros
    col1, col2 = st.columns(2)
    
    with col1:
        situacao_turma = st.selectbox(
            "Situação da Turma",
            options=situacoes,
            format_func=lambda x: x[1],
            index=0  # Seleciona "Abertas" por padrão (primeiro item na lista)
        )
    
    with col2:
        # Filtro de modalidade
        if not df_turmas_todas.empty and 'modalidade' in df_turmas_todas.columns:
            # Obter lista de modalidades únicas
            modalidades = df_turmas_todas['modalidade'].unique().tolist()
            modalidades.sort()  # Ordenar alfabeticamente
            
            # Multi-select para modalidades
            modalidades_selecionadas = st.multiselect(
                "Modalidades", 
                options=modalidades,
                default=None
            )
        else:
            modalidades_selecionadas = []

    # Carregar dados de turmas usando a função com cache apenas se a situação for diferente de 1 (Abertas)
    with st.spinner("Carregando dados de turmas..."):
        if situacao_turma[1] == "Abertas":
            # Usar as turmas já carregadas pelo carregar_dados_basicos
            df_turmas = df_turmas_todas.copy()
        else:
            # Carregar turmas para outras situações
            df_turmas = carregar_dados_turmas(
                situacao_turma=situacao_turma[0],
                modalidade=None
            )
        
        # Filtrar por modalidades selecionadas
        if modalidades_selecionadas and not df_turmas.empty:
            df_turmas = df_turmas[df_turmas['modalidade'].isin(modalidades_selecionadas)]
    
    # Exibir dados e análises
    if not df_turmas.empty:
        # Informações gerais
        st.write(f"Total de turmas: {len(df_turmas)}")
        
        # Colunas para o dataframe
        colunas_exibir = [
            'nomeTurma', 'turmaID', 'nomeCurso', 'nomeEstagio', 
            'dataInicio', 'dataTermino', 'nomeFuncionario', 
            'modalidade', 'numeroAlunos'
        ]
        
        # Filtrar apenas as colunas disponíveis
        colunas_disponiveis = [col for col in colunas_exibir if col in df_turmas.columns]
        
        df_exibir = df_turmas[colunas_disponiveis].copy()
        
        # Adicionar coluna 'Dia da semana'
        dias_semana = {
            0: 'Segunda-feira',
            1: 'Terça-feira',
            2: 'Quarta-feira',
            3: 'Quinta-feira',
            4: 'Sexta-feira',
            5: 'Sábado',
            6: 'Domingo'
        }
        
        def extrair_dia_semana(row):
            # Tentar extrair da dataInicio primeiro, se disponível
            if pd.notna(row.get('dataInicio')):
                try:
                    data = pd.to_datetime(row['dataInicio'])
                    return dias_semana[data.weekday()]
                except:
                    pass
            
            # Se não conseguir, tentar extrair da dataTermino
            if pd.notna(row.get('dataTermino')):
                try:
                    data = pd.to_datetime(row['dataTermino'])
                    return dias_semana[data.weekday()]
                except:
                    pass
            
            # Se nenhuma data válida for encontrada, retornar valor nulo
            return np.nan
        
        # Aplicar a função em cada linha do dataframe
        df_exibir['Dia da semana'] = df_exibir.apply(extrair_dia_semana, axis=1)
        
        # Reordenar colunas para que 'Dia da semana' fique na terceira posição
        colunas = list(df_exibir.columns)
        colunas.remove('Dia da semana')
        colunas.insert(2, 'Dia da semana')
        df_exibir = df_exibir[colunas]
        
        # Renomear colunas para melhor visualização
        mapeamento_colunas = {
            'nomeTurma': 'Nome da Turma',
            'turmaID': 'ID da Turma',
            'nomeCurso': 'Curso',
            'nomeEstagio': 'Estágio',
            'dataInicio': 'Data de Início',
            'dataTermino': 'Data de Término',
            'nomeFuncionario': 'Professor',
            'modalidade': 'Modalidade',
            'numeroAlunos': 'Número de Alunos'
        }
        
        # Aplicar renomeação apenas para colunas que existem no dataframe
        renomear = {col: mapeamento_colunas[col] for col in colunas_disponiveis if col in mapeamento_colunas}
        df_exibir = df_exibir.rename(columns=renomear)
        
        # Exibir dataframe
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
        
        # Opção para download
        csv = df_exibir.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Baixar dados como CSV",
            csv,
            "turmas.csv",
            "text/csv",
            key='download-turmas-csv'
        )
        
        # Seção para consultar valores financeiros
        st.subheader("Consulta de Valores Financeiros")
        st.write("Selecione uma turma para visualizar os valores financeiros do mês atual:")
        
        # Criar selectbox com as turmas disponíveis
        if 'Nome da Turma' in df_exibir.columns and 'ID da Turma' in df_exibir.columns:
            opcoes_turmas = [(row['ID da Turma'], row['Nome da Turma']) 
                        for _, row in df_exibir.iterrows()]
            
            # Opção padrão no início
            opcoes_turmas = [(-1, "Selecione uma turma...")] + opcoes_turmas
            
            # Criar select box para escolher a turma
            turma_selecionada = st.selectbox(
                "Turma:",
                options=opcoes_turmas,
                format_func=lambda x: x[1]
            )
            
            # Botão para buscar valores
            if turma_selecionada[0] != -1:
                if st.button("Consultar Valores", key="btn_consultar_valores"):
                    with st.spinner("Carregando valores financeiros..."):
                        # Encontrar o índice da turma selecionada no DataFrame original
                        idx = df_turmas[df_turmas['turmaID'] == turma_selecionada[0]].index[0]
                        
                        # Obter a lista de alunos da turma
                        alunos = df_turmas.loc[idx, 'alunos'] if 'alunos' in df_turmas.columns else []
                        
                        # Carregar dados financeiros para esta turma
                        valor_total, detalhes_alunos = carregar_dados_financeiros_turma_individual(
                            turma_selecionada[0], alunos
                        )
                        
                        # Exibir valor total da turma
                        st.metric(
                            f"Valor Total da Turma {turma_selecionada[1]} este mês:",
                            f"R$ {valor_total:.2f}".replace('.', ',')
                        )
                        
                        # Exibir detalhes dos alunos em um expander
                        with st.expander("Ver detalhes por aluno"):
                            if detalhes_alunos:
                                # Criar DataFrame com os detalhes
                                df_detalhes = pd.DataFrame(detalhes_alunos)
                                df_detalhes.columns = ["ID do Aluno", "Nome do Aluno", "Valor"]
                                
                                # Formatar coluna de valor
                                df_detalhes["Valor"] = df_detalhes["Valor"].apply(
                                    lambda x: f"R$ {x:.2f}".replace('.', ',')
                                )
                                
                                # Exibir DataFrame
                                st.dataframe(df_detalhes, hide_index=True)
                            else:
                                st.info("Não foram encontrados detalhes financeiros para os alunos desta turma.")
        
        # Análises adicionais
        st.subheader("Análises")
        
        # Distribuição por modalidade
        if 'modalidade' in df_turmas.columns:
            st.write("Distribuição de Turmas por Modalidade")
            
            # Preparar dados para o gráfico
            modalidade_counts = df_turmas.groupby('modalidade').agg({
                'turmaID': 'count',
                'numeroAlunos': ['sum', 'mean']
            }).reset_index()
            
            # Renomear colunas para facilitar o acesso
            modalidade_counts.columns = ['modalidade', 'num_turmas', 'total_alunos', 'media_alunos']
            
            # Ordenar por número de turmas em ordem decrescente
            modalidade_counts = modalidade_counts.sort_values('num_turmas', ascending=False)
            
            # Criar gráfico de barras para número de turmas
            fig = px.bar(
                modalidade_counts,
                x='modalidade',
                y='num_turmas',
                title='Número de Turmas por Modalidade',
                labels={'modalidade': 'Modalidade', 'num_turmas': 'Número de Turmas'},
                color='modalidade',
                height=400
            )
            
            # Configurar layout
            fig.update_layout(
                xaxis_title='Modalidade',
                yaxis_title='Número de Turmas',
                showlegend=False
            )
            
            # Exibir gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Exibir média de alunos por modalidade específica
            st.write("Média de Alunos por Modalidade")
            
            # Criar colunas para exibir as métricas
            col1, col2, col3 = st.columns(3)
            
            # Função para obter a média de alunos para uma modalidade específica
            def get_media_alunos(modalidade_nome):
                filtro = modalidade_counts['modalidade'] == modalidade_nome
                if filtro.any():
                    return modalidade_counts.loc[filtro, 'media_alunos'].values[0]
                return 0
            
            # Exibir métricas para modalidades específicas
            with col1:
                media_action = get_media_alunos('ACTION')
                st.metric("ACTION", f"{media_action:.1f}")
            
            with col2:
                media_gl = get_media_alunos('GENERAL LANGUAGE')
                st.metric("GENERAL LANGUAGE", f"{media_gl:.1f}")
            
            with col3:
                media_tec = get_media_alunos('TECNOLOGIA')
                st.metric("TECNOLOGIA", f"{media_tec:.1f}")
    else:
        st.info("Não há turmas para exibir com os filtros selecionados.")
