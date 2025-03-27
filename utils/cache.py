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
            df[col] = pd.to_datetime(df[col], errors='coerce')
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
@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={dict: lambda x: str(sorted(x.items())) if isinstance(x, dict) else str(x)})  # Cache válido por 1 hora
def carregar_dados_financeiros_turma_individual(turma_id, alunos_lista, data_inicio=None, data_fim=None):
    """
    Carrega os dados financeiros para uma turma específica
    
    Args:
        turma_id (int): ID da turma
        alunos_lista (list): Lista de IDs de alunos ou objetos de alunos da turma
        data_inicio (str, optional): Data de início no formato YYYY-MM-DD. Se None, usa o primeiro dia do mês atual.
        data_fim (str, optional): Data de fim no formato YYYY-MM-DD. Se None, usa o último dia do mês atual.
        
    Returns:
        float: Valor total da turma (soma de pagos e pendentes)
        list: Lista de detalhes financeiros por aluno com valores pagos e pendentes
    """
    # Log para debug
    print(f"Carregando dados financeiros para turma {turma_id} com {len(alunos_lista) if isinstance(alunos_lista, list) else 'N/A'} alunos")
    
    if not alunos_lista:
        return 0, []
    
    # Inicializar API
    api = SponteAPI()
    
    # Define o período do mês atual se não fornecido
    if data_inicio is None or data_fim is None:
        hoje = date.today()
        primeiro_dia_mes = date(hoje.year, hoje.month, 1)
        if hoje.month == 12:
            ultimo_dia_mes = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia_mes = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
        
        # Formata as datas para a API (YYYY-MM-DD)
        data_inicio = data_inicio or primeiro_dia_mes.strftime('%Y-%m-%d')
        data_fim = data_fim or ultimo_dia_mes.strftime('%Y-%m-%d')
    
    # Lista de IDs de alunos nesta turma
    alunos_ids = []
    if isinstance(alunos_lista, list):
        # Verifica se a lista contém IDs ou objetos de alunos
        if alunos_lista and isinstance(alunos_lista[0], dict) and 'alunoID' in alunos_lista[0]:
            # Extrai alunoID de cada aluno na lista
            for aluno in alunos_lista:
                alunos_ids.append(aluno['alunoID'])
        else:
            # Assume que a lista já contém IDs
            alunos_ids = alunos_lista
    elif isinstance(alunos_lista, dict):
        # Se for um dicionário, extrair IDs
        for aluno_id in alunos_lista.keys():
            alunos_ids.append(aluno_id)
    
    # Valor total da turma
    valor_turma_total = 0
    
    # Detalhe dos valores por aluno
    detalhes_alunos = []
    
    # Carregar dados de alunos para obter nomes
    df_alunos = carregar_dados_alunos()
    
    # Para cada aluno, busca o valor
    for aluno_id in alunos_ids:
        # Obter dados financeiros PAGOS do aluno para o mês atual (situacao=1)
        contas_pagas = api.get_contas_receber(
            situacao=1,  # Contas pagas
            aluno_id=aluno_id,
            data_vencimento_inicio=data_inicio,
            data_vencimento_fim=data_fim
        )
        
        # Obter dados financeiros PENDENTES do aluno para o mês atual (situacao=0)
        contas_pendentes = api.get_contas_receber(
            situacao=0,  # Contas pendentes
            aluno_id=aluno_id,
            data_vencimento_inicio=data_inicio,
            data_vencimento_fim=data_fim
        )
        
        # Calcular o valor total das contas PAGAS do aluno
        valor_pago = 0
        if isinstance(contas_pagas, dict) and 'listDados' in contas_pagas and contas_pagas['listDados']:
            for conta in contas_pagas['listDados']:
                # O valor está em parcelas, que está dentro de cada item em listDados
                if 'parcelas' in conta and isinstance(conta['parcelas'], list):
                    for parcela in conta['parcelas']:
                        if isinstance(parcela, dict) and 'valor' in parcela:
                            try:
                                valor_parcela = float(parcela['valor'])
                                valor_pago += valor_parcela
                            except (ValueError, TypeError):
                                continue
        
        # Calcular o valor total das contas PENDENTES do aluno
        valor_pendente = 0
        if isinstance(contas_pendentes, dict) and 'listDados' in contas_pendentes and contas_pendentes['listDados']:
            for conta in contas_pendentes['listDados']:
                # O valor está em parcelas, que está dentro de cada item em listDados
                if 'parcelas' in conta and isinstance(conta['parcelas'], list):
                    for parcela in conta['parcelas']:
                        if isinstance(parcela, dict) and 'valor' in parcela:
                            try:
                                valor_parcela = float(parcela['valor'])
                                valor_pendente += valor_parcela
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
        
        # Calcular valor total do aluno (pago + pendente)
        valor_total_aluno = valor_pago + valor_pendente
        
        # Adiciona o valor do aluno ao total da turma
        valor_turma_total += valor_total_aluno
        
        # Adiciona detalhe do aluno
        detalhes_alunos.append({
            'id': aluno_id,
            'nome': nome_aluno,
            'valor_pago': valor_pago,
            'valor_pendente': valor_pendente
        })
    
    return valor_turma_total, detalhes_alunos

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
