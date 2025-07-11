import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.cache import carregar_dados_turmas, carregar_dados_basicos, carregar_dados_financeiros_turma_individual
from datetime import datetime, timedelta
import numpy as np
import io

def exibir_pagina_turmas():
    st.header("Gestão de Turmas")
    
    # Carregar dados básicos - utilizados no dashboard e em outras funções
    with st.spinner("Carregando dados. Aguarde um minuto..."):
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
    
    # Nova linha de filtros para Curso, Estágio e Professor
    col3, col4, col5 = st.columns(3)
    
    with col3:
        # Filtro de Curso
        if not df_turmas_todas.empty and 'nomeCurso' in df_turmas_todas.columns:
            # Obter lista de cursos únicos
            cursos = df_turmas_todas['nomeCurso'].dropna().unique().tolist()
            cursos.sort()  # Ordenar alfabeticamente
            
            # Adicionar opção "Todos" no início da lista
            cursos_opcoes = ["Todos"] + cursos
            
            # Select box para cursos
            curso_selecionado = st.selectbox(
                "Curso", 
                options=cursos_opcoes,
                index=0  # Seleciona "Todos" por padrão
            )
        else:
            curso_selecionado = "Todos"
    
    with col4:
        # Filtro de Estágio
        if not df_turmas_todas.empty and 'nomeEstagio' in df_turmas_todas.columns:
            # Obter lista de estágios únicos
            estagios = df_turmas_todas['nomeEstagio'].dropna().unique().tolist()
            estagios.sort()  # Ordenar alfabeticamente
            
            # Adicionar opção "Todos" no início da lista
            estagios_opcoes = ["Todos"] + estagios
            
            # Select box para estágios
            estagio_selecionado = st.selectbox(
                "Estágio", 
                options=estagios_opcoes,
                index=0  # Seleciona "Todos" por padrão
            )
        else:
            estagio_selecionado = "Todos"
    
    with col5:
        # Filtro de Professor
        if not df_turmas_todas.empty and 'nomeFuncionario' in df_turmas_todas.columns:
            # Obter lista de professores únicos
            professores = df_turmas_todas['nomeFuncionario'].dropna().unique().tolist()
            professores.sort()  # Ordenar alfabeticamente
            
            # Adicionar opção "Todos" no início da lista
            professores_opcoes = ["Todos"] + professores
            
            # Select box para professores
            professor_selecionado = st.selectbox(
                "Professor", 
                options=professores_opcoes,
                index=0  # Seleciona "Todos" por padrão
            )
        else:
            professor_selecionado = "Todos"

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
        
        # Aplicar filtros adicionais
        if not df_turmas.empty:
            # Filtrar por curso selecionado
            if curso_selecionado != "Todos" and 'nomeCurso' in df_turmas.columns:
                df_turmas = df_turmas[df_turmas['nomeCurso'] == curso_selecionado]
            
            # Filtrar por estágio selecionado
            if estagio_selecionado != "Todos" and 'nomeEstagio' in df_turmas.columns:
                df_turmas = df_turmas[df_turmas['nomeEstagio'] == estagio_selecionado]
            
            # Filtrar por professor selecionado
            if professor_selecionado != "Todos" and 'nomeFuncionario' in df_turmas.columns:
                df_turmas = df_turmas[df_turmas['nomeFuncionario'] == professor_selecionado]
    
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
                    data = pd.to_datetime(row['dataInicio'], dayfirst=True)
                    return dias_semana[data.weekday()]
                except:
                    pass
            
            # Se não conseguir, tentar extrair da dataTermino
            if pd.notna(row.get('dataTermino')):
                try:
                    data = pd.to_datetime(row['dataTermino'], dayfirst=True)
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
        with io.BytesIO() as excel_file:
            df_exibir.to_excel(excel_file, index=False)
            excel = excel_file.getvalue()

        st.download_button(
            "Baixar dados como CSV",
            csv,
            "turmas.csv",
            key='download-turmas-csv'
        )
        
        # Botão para download em Excel
        st.download_button(
            "Baixar dados como Excel",
            excel,
            "turmas.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key='download-turmas-excel'
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
                        
                        # Extrair apenas os IDs dos alunos para melhorar o cache
                        alunos_ids = []
                        if isinstance(alunos, list):
                            for aluno in alunos:
                                if isinstance(aluno, dict) and 'alunoID' in aluno:
                                    alunos_ids.append(aluno['alunoID'])
                        
                        # Carregar dados financeiros para esta turma
                        valor_total, valor_pago, valor_pendente, detalhes_alunos = carregar_dados_financeiros_turma_individual(
                            turma_selecionada[0], alunos_ids
                        )
                        
                        # Exibir valor total da turma
                        st.metric(
                            f"Valor TOTAL este mês:",
                            f"R$ {valor_total:.2f}".replace('.', ',')
                        )
                        
                        # Exibir valor Pago da turma
                        st.metric(
                            f"Valor PAGO este mês:",
                            f"R$ {valor_pago:.2f}".replace('.', ',')
                        )
                        
                        # Exibir valor Pendente da turma
                        st.metric(
                            f"Valor PENDENTE este mês:",
                            f"R$ {valor_pendente:.2f}".replace('.', ',')
                        )   

                        # Exibir detalhes dos alunos
                        st.write("Detalhes por aluno")

                        if detalhes_alunos:
                            # Criar DataFrame com os detalhes
                            df_detalhes = pd.DataFrame(detalhes_alunos)
                            df_detalhes.columns = ["ID do Aluno", "Nome do Aluno", "Valor Pago", "Valor Pendente"]
                            
                            # Formatar colunas de valor
                            df_detalhes["Valor Pago"] = df_detalhes["Valor Pago"].apply(
                                lambda x: f"R$ {x:.2f}".replace('.', ',')
                            )
                            df_detalhes["Valor Pendente"] = df_detalhes["Valor Pendente"].apply(
                                lambda x: f"R$ {x:.2f}".replace('.', ',')
                            )
                            
                            # Adicionar coluna de valor total
                            df_detalhes["Valor Total"] = df_detalhes.apply(
                                lambda row: f"R$ {float(row['Valor Pago'].replace('R$ ', '').replace(',', '.')) + float(row['Valor Pendente'].replace('R$ ', '').replace(',', '.')):.2f}".replace('.', ','),
                                axis=1
                            )
                            
                            # Exibir DataFrame
                            st.dataframe(df_detalhes, hide_index=True)
                        else:
                            st.info("Não foram encontrados detalhes financeiros para os alunos desta turma.")
        
        # Análises adicionais
        st.subheader("Análises")
        
        # Distribuição por modalidade
        if 'modalidade' in df_turmas.columns:
            
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

            # Criar gráfico de barras para número de alunos por modalidade
            fig_alunos = px.bar(
                modalidade_counts,
                x='modalidade',
                y='total_alunos',
                title='Número de Alunos por Modalidade',
                labels={'modalidade': 'Modalidade', 'total_alunos': 'Número de Alunos'},
                color='modalidade',
                height=400
            )
            
            # Configurar layout
            fig_alunos.update_layout(
                xaxis_title='Modalidade',
                yaxis_title='Número de Alunos',
                showlegend=False
            )
            
            # Exibir gráfico
            st.plotly_chart(fig_alunos, use_container_width=True)

            # Criar mapa de calor por Dia da Semana e Modalidade
            st.subheader("Distribuição de Turmas por Dia da Semana e Modalidade")
            
            # Verificar se temos as colunas necessárias
            if 'Dia da semana' in df_exibir.columns and 'Modalidade' in df_exibir.columns:
                # Criar um dataframe de contagem para o mapa de calor
                heatmap_data = df_exibir.groupby(['Dia da semana', 'Modalidade']).size().reset_index(name='Contagem')
                
                # Pivotear o dataframe para formato adequado ao mapa de calor (invertendo linhas e colunas)
                heatmap_pivot = heatmap_data.pivot_table(
                    values='Contagem', 
                    index='Modalidade',  # Agora modalidade está nas linhas
                    columns='Dia da semana',  # Dias da semana nas colunas
                    fill_value=0
                )
                
                # Ordenar os dias da semana corretamente (sem domingo)
                ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado']
                heatmap_pivot = heatmap_pivot.reindex(columns=ordem_dias)  # Reordenar colunas em vez de linhas
                
                # Criar o mapa de calor
                fig_heatmap = px.imshow(
                    heatmap_pivot,
                    labels=dict(x="Dia da Semana", y="Modalidade", color=""),  # Rótulo vazio para a cor
                    x=heatmap_pivot.columns,
                    y=heatmap_pivot.index,
                    color_continuous_scale="Viridis",
                    title="Mapa de Calor: Turmas por Modalidade e Dia da Semana",
                    #height=500
                )
                
                # Ajustar layout
                fig_heatmap.update_layout(
                    xaxis_title=None,  # Remover título do eixo X
                    yaxis_title=None,  # Remover título do eixo Y
                    xaxis={'side': 'top'},
                    coloraxis_showscale=False  # Ocultar a legenda de cores
                )
                
                # Adicionar anotações com os valores
                for i, modalidade in enumerate(heatmap_pivot.index):
                    for j, dia in enumerate(heatmap_pivot.columns):
                        valor = heatmap_pivot.iloc[i, j]
                        if valor > 0:  # Só mostrar valores maiores que zero
                            fig_heatmap.add_annotation(
                                x=dia,
                                y=modalidade,
                                text=str(int(valor)),
                                showarrow=False,
                                font=dict(
                                    color="white" if valor < 20 else "black",
                                    size=14  # Aumentar o tamanho da fonte
                                )
                            )
                
                # Exibir o mapa de calor
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
            else:
                st.warning("Não foi possível criar o mapa de calor. Verifique se as colunas 'Dia da semana' e 'Modalidade' estão disponíveis.")

            # Exibir média de alunos por modalidade específica
            st.write("Média de Alunos por Turma de Modalidade")
            
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
