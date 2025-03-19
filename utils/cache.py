import streamlit as st
import pandas as pd
from sponte_api_functions import get_alunos_df, get_turmas_df, get_aulas_df, get_contas_receber_df
from sponte_api_financeiro import SponteAPI
from datetime import datetime, date, timedelta

# Função para formatar colunas de data em um DataFrame
def formatar_colunas_data(df):
    """
    Formata todas as colunas que contêm 'data' no nome para o formato dd/mm/YYYY
    
    Args:
        df (pd.DataFrame): DataFrame a ser formatado
        
    Returns:
        pd.DataFrame: DataFrame com as colunas de data formatadas
    """
    if df.empty:
        return df
        
    # Identificar colunas que contêm 'data' no nome (case insensitive)
    colunas_data = [col for col in df.columns if 'data' in col.lower()]
    
    # Formatar cada coluna de data
    for col in colunas_data:
        try:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
            df[col] = df[col].dt.strftime('%d/%m/%Y')
        except Exception as e:
            print(f"Erro ao formatar coluna {col}: {e}")
    
    return df

# Função para carregar dados de alunos com cache
@st.cache_data(ttl=3600)  # Cache válido por 1 hora
def carregar_dados_alunos(situacao=-1):
    """
    Carrega os dados dos alunos com cache
    
    Args:
        situacao (int, optional): Situação do aluno (-1=Ativos, -2=Inativos, etc). Defaults to -1.
        
    Returns:
        pd.DataFrame: DataFrame com os dados dos alunos
    """
    df_alunos = get_alunos_df(situacao=situacao)
    
    # Formatar colunas de data
    df_alunos = formatar_colunas_data(df_alunos)
        
    return df_alunos

# Função para carregar dados de turmas com cache
@st.cache_data(ttl=3600)  # Cache válido por 1 hora
def carregar_dados_turmas(situacao_turma, modalidade=None):
    """
    Carrega os dados das turmas com cache
    
    Args:
        situacao_turma (int): Situação da turma (1=Abertas, 2=Encerradas, 3=Em Formação)
        modalidade (str, optional): Filtro de modalidade
        
    Returns:
        pd.DataFrame: DataFrame com os dados das turmas
    """
    df_turmas = get_turmas_df(
        situacao_turma=situacao_turma,
        modalidade=modalidade if modalidade else None
    )
    
    # Formatar colunas de data
    df_turmas = formatar_colunas_data(df_turmas)
    
    # Adicionar coluna com o número de alunos
    if not df_turmas.empty and 'alunos' in df_turmas.columns:
        try:
            # Se for um dicionário ou lista, contar o número de elementos
            df_turmas['numeroAlunos'] = df_turmas['alunos'].apply(
                lambda x: len(x) if isinstance(x, (dict, list)) else 0
            )
        except Exception as e:
            print(f"Erro ao calcular número de alunos: {e}")
            df_turmas['numeroAlunos'] = 0
            
    return df_turmas

# Função para carregar dados de aulas com cache
@st.cache_data(ttl=3600)  # Cache válido por 1 hora
def carregar_dados_aulas(data_inicio, data_fim, situacao=1):
    """
    Carrega os dados das aulas com cache
    
    Args:
        data_inicio (str): Data inicial no formato YYYY-MM-DD
        data_fim (str): Data final no formato YYYY-MM-DD
        situacao (int, optional): Situação da aula (1=Confirmadas, 0=Pendentes, -1=Todas). Defaults to 1.
        
    Returns:
        pd.DataFrame: DataFrame com os dados das aulas
    """
    df_aulas = get_aulas_df(
        data_aula_inicio=data_inicio,
        data_aula_fim=data_fim,
        situacao=situacao
    )
    
    # Formatar colunas de data
    df_aulas = formatar_colunas_data(df_aulas)
    
    return df_aulas

# Função para carregar dados financeiros de uma única turma
@st.cache_data(ttl=3600)  # Cache válido por 1 hora
def carregar_dados_financeiros_turma_individual(turma_id, alunos_lista):
    """
    Carrega os dados financeiros para uma turma específica
    
    Args:
        turma_id (int): ID da turma
        alunos_lista (list/dict): Lista ou dicionário de alunos da turma
        
    Returns:
        float: Valor total da turma
        list: Lista de detalhes financeiros por aluno
    """
    if not alunos_lista:
        return 0, []
    
    # Importar API
    from sponte_api_financeiro import SponteAPI
    
    # Define o período do mês atual
    hoje = date.today()
    primeiro_dia_mes = date(hoje.year, hoje.month, 1)
    if hoje.month == 12:
        ultimo_dia_mes = date(hoje.year + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia_mes = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
    
    # Formata as datas para a API (YYYY-MM-DD)
    data_inicio = primeiro_dia_mes.strftime('%Y-%m-%d')
    data_fim = ultimo_dia_mes.strftime('%Y-%m-%d')
    
    # Lista de IDs de alunos nesta turma
    alunos_ids = []
    if isinstance(alunos_lista, list):
        # Extrai alunoID de cada aluno na lista
        for aluno in alunos_lista:
            if isinstance(aluno, dict) and 'alunoID' in aluno:
                alunos_ids.append(aluno['alunoID'])
    elif isinstance(alunos_lista, dict):
        # Se for um dicionário, tenta pegar os IDs diretamente
        alunos_ids = [aluno['alunoID'] for aluno in alunos_lista.values() 
                    if isinstance(aluno, dict) and 'alunoID' in aluno]
    
    # Valor total da turma
    valor_turma = 0
    
    # Detalhe dos valores por aluno
    detalhes_alunos = []
    
    # API Direta
    api = SponteAPI()
    
    # Carregar dados de alunos para obter nomes
    df_alunos = carregar_dados_alunos()
    
    # Para cada aluno, busca o valor
    for aluno_id in alunos_ids:
        # Obter dados financeiros do aluno para o mês atual
        contas = api.get_contas_receber(
            aluno_id=aluno_id,
            data_vencimento_inicio=data_inicio,
            data_vencimento_fim=data_fim
        )
        
        # Calcular o valor total das contas do aluno
        valor_aluno = 0
        if isinstance(contas, dict) and 'listDados' in contas and contas['listDados']:
            for conta in contas['listDados']:
                # O valor está em parcelas, que está dentro de cada item em listDados
                if 'parcelas' in conta and isinstance(conta['parcelas'], list):
                    for parcela in conta['parcelas']:
                        if isinstance(parcela, dict) and 'valor' in parcela:
                            try:
                                valor_parcela = float(parcela['valor'])
                                valor_aluno += valor_parcela
                            except (ValueError, TypeError):
                                continue
        
        # Busca nome do aluno no DataFrame de alunos
        nome_aluno = f"Aluno {aluno_id}"  # Valor padrão
        
        # Tentar encontrar o nome no DataFrame de alunos
        if not df_alunos.empty:
            # Filtrar pelo ID do aluno
            aluno_row = df_alunos[df_alunos['alunoID'] == aluno_id]
            if not aluno_row.empty and 'nomeAluno' in aluno_row.columns:
                nome_aluno = aluno_row['nomeAluno'].iloc[0]
        
        # Adiciona o valor do aluno ao total da turma
        valor_turma += valor_aluno
        
        # Adiciona detalhe do aluno
        detalhes_alunos.append({
            'id': aluno_id,
            'nome': nome_aluno,
            'valor': valor_aluno
        })
    
    return valor_turma, detalhes_alunos

# Função para carregar dados básicos para o dashboard com cache
@st.cache_data(ttl=3600)  # Cache válido por 1 hora
def carregar_dados_basicos():
    """
    Carrega os dados básicos para o dashboard
    
    Returns:
        tuple: (df_alunos, df_turmas, modalidades, cursos, estagios, professores) - DataFrames com dados de alunos e turmas, e listas de modalidades, cursos, estágios e professores
    """
    alunos = get_alunos_df(situacao=-1)  # Alunos ativos (valor -1)
    turmas = get_turmas_df(situacao_turma=1)  # Apenas turmas abertas
    
    # Formatar colunas de data
    alunos = formatar_colunas_data(alunos)
    turmas = formatar_colunas_data(turmas)
    
    # Adicionar coluna com o número de alunos nas turmas
    if not turmas.empty and 'alunos' in turmas.columns:
        try:
            turmas['numeroAlunos'] = turmas['alunos'].apply(
                lambda x: len(x) if isinstance(x, (dict, list)) else 0
            )
        except Exception as e:
            print(f"Erro ao calcular número de alunos: {e}")
            turmas['numeroAlunos'] = 0
    
    # Obter listas para filtros
    modalidades = sorted(turmas['modalidade'].dropna().unique().tolist()) if 'modalidade' in turmas.columns else []
    cursos = sorted(turmas['nomeCurso'].dropna().unique().tolist()) if 'nomeCurso' in turmas.columns else []
    estagios = sorted(turmas['nomeEstagio'].dropna().unique().tolist()) if 'nomeEstagio' in turmas.columns else []
    professores = sorted(turmas['nomeFuncionario'].dropna().unique().tolist()) if 'nomeFuncionario' in turmas.columns else []
    
    # Para compatibilidade com código existente, retornar apenas 3 valores
    return alunos, turmas, modalidades
