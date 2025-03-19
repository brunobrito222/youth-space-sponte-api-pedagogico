import os
from typing import Optional, Dict, List, Any, Union
import requests
from dotenv import load_dotenv
import pandas as pd
import sys
from datetime import datetime

# Carrega as variáveis do arquivo .env
load_dotenv()

class SponteAPI:
    def __init__(self):
        self.login_user = os.getenv('LOGIN')
        self.senha = os.getenv('SENHA')
        self.cod_cliente = 3751  # Código do cliente Sponte obrigatório
        
        # Tenta carregar o token do arquivo .env
        self.token = os.getenv('token')
        
        # Verifica se as credenciais foram carregadas
        if not self.login_user or not self.senha:
            print("Erro: Credenciais não encontradas no arquivo .env")
            print(f"Login: {self.login_user}")
            print(f"Senha: {self.senha}")
            sys.exit(1)
            
        self.base_url = 'https://integracao.sponteweb.net.br'
        
    def login(self) -> Optional[str]:
        """
        Faz login na API para obter o token
        :return: Token de autenticação ou None se falhar
        """
        login_endpoint = f'{self.base_url}/api/v1/login'
        
        login_data = {
            "login": self.login_user,
            "senha": self.senha
        }
        
        try:
            print(f"\nTentando fazer login em: {login_endpoint}")
            response = requests.post(
                login_endpoint,
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Status do login: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                self.token = response_data.get('token')
                if self.token:
                    print("Login realizado com sucesso!")
                    return self.token
                else:
                    print("Token não encontrado na resposta")
                    return None
            else:
                print(f"Erro no login: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erro ao tentar fazer login: {e}")
            return None

    def get_data(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Obtém dados da API usando o token de autenticação
        :param endpoint: Endpoint da API a ser acessado
        :param params: Parâmetros opcionais da requisição
        :return: Dados da resposta ou None se falhar
        """
        # Se não tiver token, tenta fazer login
        if not self.token:
            print("Token não encontrado. Tentando fazer login...")
            self.token = self.login()
            if not self.token:
                print("Não foi possível obter o token de autenticação")
                return None
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Garante que o codCliSponte está presente em todas as requisições
        if params is None:
            params = {}
        params['codCliSponte'] = self.cod_cliente
        
        full_url = f'{self.base_url}{endpoint}'
        print(f"\nAcessando: {full_url}")
        print(f"Parâmetros: {params}")
        
        try:
            response = requests.get(full_url, headers=headers, params=params)
            print(f"Status: {response.status_code}")
            
            # Se o token expirou, tenta fazer login novamente e refaz a requisição
            if response.status_code == 401:
                print("Token expirado ou inválido. Tentando fazer login novamente...")
                self.token = self.login()
                if not self.token:
                    return None
                
                # Atualiza o header com o novo token
                headers['Authorization'] = f'Bearer {self.token}'
                response = requests.get(full_url, headers=headers, params=params)
                print(f"Novo status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f'Erro: {response.status_code}')
                print(f'Mensagem: {response.text}')
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar {full_url}: {e}")
            return None

    def get_all_pages_df(self, endpoint: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Obtém dados de todas as páginas de um endpoint e retorna como DataFrame
        :param endpoint: Endpoint da API a ser acessado
        :param params: Parâmetros opcionais da requisição
        :return: DataFrame pandas com todos os dados
        """
        if params is None:
            params = {}
        
        # Garante que estamos começando da página 1
        params['pagina'] = 1
        
        # Primeira chamada para obter o número total de páginas
        response = self.get_data(endpoint, params)
        if not response or not response.get('listDados'):
            return pd.DataFrame()
        
        total_paginas = response.get('totalPaginas', 0)
        print(f'Total de páginas: {total_paginas}')
        
        # Inicializa o DataFrame
        df = pd.DataFrame(response['listDados'])
        
        # Se só tem uma página, retorna o DataFrame
        if total_paginas <= 1:
            return df
        
        # Busca as demais páginas
        for i in range(2, total_paginas + 1):
            print(f'Lendo página {i}...')
            params['pagina'] = i
            page_response = self.get_data(endpoint, params)
            
            if not page_response or not page_response.get('listDados'):
                continue
                
            df_temp = pd.DataFrame(page_response['listDados'])
            df = pd.concat([df, df_temp], axis=0, ignore_index=True)
            
            print()
        
        return df

    def get_alunos(self, situacao: int = -1, **kwargs) -> pd.DataFrame:
        """
        Obtém a lista de alunos como DataFrame
        :param situacao: Situação do aluno (padrão: -1)
        :param kwargs: Parâmetros adicionais para a requisição
        :return: DataFrame com os dados dos alunos
        """
        params = kwargs.copy()
        if situacao is not None:
            params["situacao"] = situacao
            
        return self.get_all_pages_df('/api/v1/alunos', params)

    def get_turmas(self, modalidade: Optional[str] = None, 
                  situacao_turma: int = 1, idioma_id: int = 0, 
                  estagio_id: int = 0, **kwargs) -> pd.DataFrame:
        """
        Obtém a lista de turmas como DataFrame
        :param modalidade: Filtrar por modalidade (ex: 'TECNOLOGIA', 'GENERAL LANGUAGE')
        :param situacao_turma: Situação da turma (Aberta: 1, Encerrada: 2, Em Formação: 3)
        :param idioma_id: ID do idioma (padrão: 0)
        :param estagio_id: ID do estágio (padrão: 0)
        :param kwargs: Parâmetros adicionais para a requisição
        :return: DataFrame com os dados das turmas
        """
        params = kwargs.copy()
        
        if modalidade is not None:
            params["modalidade"] = modalidade
            
        # Adiciona os parâmetros
        params["situacaoTurma"] = situacao_turma
        params["idiomaId"] = idioma_id
        params["estagioId"] = estagio_id
            
        return self.get_all_pages_df('/api/v1/turmas', params)

    def get_aulas(self, data_aula_inicio: Optional[str] = None,
                 data_aula_fim: Optional[str] = None,
                 situacao: Optional[int] = None,
                 aluno_id: int = 0,
                 turma_id: int = 0,
                 professor_id: int = 0,
                 **kwargs) -> pd.DataFrame:
        """
        Obtém a lista de aulas
        :param data_aula_inicio: Data inicial das aulas (formato: YYYY-MM-DD)
        :param data_aula_fim: Data final das aulas (formato: YYYY-MM-DD)
        :param situacao: Situação das aulas (1 = Confirmada, 0 = Pendente)
        :param aluno_id: ID do aluno para filtrar
        :param turma_id: ID da turma para filtrar
        :param professor_id: ID do professor para filtrar
        :param kwargs: Parâmetros adicionais para a requisição
        :return: DataFrame com os dados das aulas
        """
        params = kwargs.copy()
        if data_aula_inicio is not None:
            params["dataAulaInicio"] = data_aula_inicio
        if data_aula_fim is not None:
            params["dataAulaFim"] = data_aula_fim
        if situacao is not None:
            params["situacao"] = situacao
        if aluno_id > 0:
            params["alunoId"] = aluno_id
        if turma_id > 0:
            params["turmaId"] = turma_id
        if professor_id > 0:
            params["professorId"] = professor_id
        return self.get_all_pages_df('/api/v1/aulas', params)

    def get_contas_receber(self, situacao: Optional[int] = -1,
                          data_vencimento_inicio: Optional[str] = None,
                          data_vencimento_fim: Optional[str] = None,
                          **kwargs) -> pd.DataFrame:
        """
        Obtém contas a receber com base nos filtros fornecidos
        :param situacao: 0 para pendentes, 1 para pagas, -1 para todas
        :param data_vencimento_inicio: Data inicial de vencimento (YYYY-MM-DD)
        :param data_vencimento_fim: Data final de vencimento (YYYY-MM-DD)
        :param kwargs: Parâmetros adicionais para a requisição
        :return: DataFrame com os dados das contas
        """
        params = kwargs.copy()
        
        if situacao is not None:
            params["situacao"] = situacao
        if data_vencimento_inicio is not None:
            params["dataVencimentoInicio"] = data_vencimento_inicio
        if data_vencimento_fim is not None:
            params["dataVencimentoFim"] = data_vencimento_fim
            
        return self.get_all_pages_df('/api/v1/contasReceber', params)

    def get_contas_pagar(self, situacao: Optional[int] = -1,
                        data_vencimento_inicio: Optional[str] = None,
                        data_vencimento_fim: Optional[str] = None,
                        **kwargs) -> pd.DataFrame:
        """
        Obtém contas a pagar com base nos filtros fornecidos
        :param situacao: 0 para pendentes, 1 para pagas, -1 para todas
        :param data_vencimento_inicio: Data inicial de vencimento (YYYY-MM-DD)
        :param data_vencimento_fim: Data final de vencimento (YYYY-MM-DD)
        :param kwargs: Parâmetros adicionais para a requisição
        :return: DataFrame com os dados das contas
        """
        params = kwargs.copy()
        
        if situacao is not None:
            params["situacao"] = situacao
        if data_vencimento_inicio is not None:
            params["dataVencimentoInicio"] = data_vencimento_inicio
        if data_vencimento_fim is not None:
            params["dataVencimentoFim"] = data_vencimento_fim
            
        return self.get_all_pages_df('/api/v1/contasPagar', params)

    def get_fluxo_caixa(self, data_inicio: str, data_fim: str, agrupamento: str = 'dia') -> pd.DataFrame:
        """
        Gera um relatório de fluxo de caixa para um período específico
        
        Args:
            data_inicio (str): Data inicial no formato YYYY-MM-DD
            data_fim (str): Data final no formato YYYY-MM-DD
            agrupamento (str, optional): Tipo de agrupamento ('dia', 'semana', 'mes'). Defaults to 'dia'.
            
        Returns:
            pd.DataFrame: DataFrame com o fluxo de caixa
        """
        # Converter strings para datas
        try:
            data_inicio_dt = pd.to_datetime(data_inicio)
            data_fim_dt = pd.to_datetime(data_fim)
        except Exception as e:
            print(f"Erro ao converter datas: {e}")
            return pd.DataFrame()
        
        # Obter contas a receber e pagar
        df_receber = self.get_contas_receber(
            data_vencimento_inicio=data_inicio,
            data_vencimento_fim=data_fim
        )
        
        df_pagar = self.get_contas_pagar(
            data_vencimento_inicio=data_inicio,
            data_vencimento_fim=data_fim
        )
        
        # Criar DataFrame base com todas as datas do período
        datas = pd.date_range(start=data_inicio_dt, end=data_fim_dt)
        df_fluxo = pd.DataFrame(datas, columns=['data'])
        df_fluxo['receitas'] = 0.0
        df_fluxo['despesas'] = 0.0
        df_fluxo['saldo'] = 0.0
        
        # Processar receitas
        if not df_receber.empty and 'dataVencimento' in df_receber.columns:
            df_receber['dataVencimento'] = pd.to_datetime(df_receber['dataVencimento'], errors='coerce')
            receitas_por_data = df_receber.groupby(df_receber['dataVencimento'].dt.date)['valor'].sum()
            
            for data, valor in receitas_por_data.items():
                try:
                    data_dt = pd.to_datetime(data)
                    idx = df_fluxo[df_fluxo['data'].dt.date == data_dt.date()].index
                    if len(idx) > 0:
                        df_fluxo.loc[idx[0], 'receitas'] = valor
                except Exception as e:
                    print(f"Erro ao processar receita para data {data}: {e}")
        
        # Processar despesas
        if not df_pagar.empty and 'dataVencimento' in df_pagar.columns:
            df_pagar['dataVencimento'] = pd.to_datetime(df_pagar['dataVencimento'], errors='coerce')
            despesas_por_data = df_pagar.groupby(df_pagar['dataVencimento'].dt.date)['valor'].sum()
            
            for data, valor in despesas_por_data.items():
                try:
                    data_dt = pd.to_datetime(data)
                    idx = df_fluxo[df_fluxo['data'].dt.date == data_dt.date()].index
                    if len(idx) > 0:
                        df_fluxo.loc[idx[0], 'despesas'] = valor
                except Exception as e:
                    print(f"Erro ao processar despesa para data {data}: {e}")
        
        # Calcular saldo
        df_fluxo['saldo'] = df_fluxo['receitas'] - df_fluxo['despesas']
        
        # Agrupar conforme solicitado
        if agrupamento.lower() == 'dia':
            df_agrupado = df_fluxo.copy()
            df_agrupado['periodo'] = df_agrupado['data'].dt.strftime('%d/%m/%Y')
        
        elif agrupamento.lower() == 'semana':
            df_fluxo['semana'] = df_fluxo['data'].dt.isocalendar().week
            df_fluxo['ano'] = df_fluxo['data'].dt.isocalendar().year
            df_agrupado = df_fluxo.groupby(['ano', 'semana']).agg({
                'receitas': 'sum',
                'despesas': 'sum',
                'saldo': 'sum',
                'data': 'first'  # Para referência
            }).reset_index()
            df_agrupado['periodo'] = df_agrupado.apply(
                lambda x: f"Semana {int(x['semana'])} de {int(x['ano'])}", axis=1
            )
        
        elif agrupamento.lower() == 'mes':
            df_fluxo['mes'] = df_fluxo['data'].dt.month
            df_fluxo['ano'] = df_fluxo['data'].dt.year
            df_agrupado = df_fluxo.groupby(['ano', 'mes']).agg({
                'receitas': 'sum',
                'despesas': 'sum',
                'saldo': 'sum',
                'data': 'first'  # Para referência
            }).reset_index()
            df_agrupado['periodo'] = df_agrupado['data'].dt.strftime('%m/%Y')
        
        else:
            # Agrupamento padrão: dia
            df_agrupado = df_fluxo.copy()
            df_agrupado['periodo'] = df_agrupado['data'].dt.strftime('%d/%m/%Y')
        
        return df_agrupado[['periodo', 'receitas', 'despesas', 'saldo']]

# Funções de acesso direto para importação em outros arquivos
def get_api_instance():
    """
    Retorna uma instância da API já inicializada
    :return: Instância da SponteAPI
    """
    api = SponteAPI()
    # Não faz login automaticamente, pois usa o token do .env
    return api

def get_alunos_df(situacao: int = -1, **kwargs) -> pd.DataFrame:
    """
    Obtém os alunos da API e retorna como DataFrame
    
    Args:
        situacao (int, optional): Situação dos alunos:
            -1 = Ativos
            -2 = Inativos
            -3 = Interessados
            -4 = Formados
            -5 = Desistentes
            Defaults to -1.
        **kwargs: Parâmetros adicionais para a API
        
    Returns:
        pd.DataFrame: DataFrame com os alunos
    """
    api = SponteAPI()
    return api.get_alunos(situacao, **kwargs)

def get_turmas_df(modalidade: Optional[str] = None, 
                situacao_turma: int = 1, idioma_id: int = 0, 
                estagio_id: int = 0, **kwargs) -> pd.DataFrame:
    """
    Obtém as turmas da API e retorna como DataFrame
    
    Args:
        modalidade (str, optional): Modalidade das turmas. Defaults to None.
        situacao_turma (int, optional): Situação das turmas (1=Abertas, 2=Encerradas, 3=Em Formação). Defaults to 1.
        idioma_id (int, optional): ID do idioma. Defaults to 0.
        estagio_id (int, optional): ID do estágio. Defaults to 0.
        **kwargs: Parâmetros adicionais para a API
        
    Returns:
        pd.DataFrame: DataFrame com as turmas
    """
    api = SponteAPI()
    return api.get_turmas(modalidade, situacao_turma, idioma_id, estagio_id, **kwargs)

def get_aulas_df(data_aula_inicio: Optional[str] = None,
               data_aula_fim: Optional[str] = None,
               situacao: Optional[int] = None,
               turma_id: int = 0,
               professor_id: int = 0,
               **kwargs) -> pd.DataFrame:
    """
    Obtém as aulas da API e retorna como DataFrame
    
    Args:
        data_aula_inicio (str, optional): Data inicial das aulas (formato YYYY-MM-DD). Defaults to None.
        data_aula_fim (str, optional): Data final das aulas (formato YYYY-MM-DD). Defaults to None.
        situacao (int, optional): Situação das aulas (0=Pendentes, 1=Confirmadas). Defaults to None.
        turma_id (int, optional): ID da turma. Defaults to 0.
        professor_id (int, optional): ID do professor. Defaults to 0.
        **kwargs: Parâmetros adicionais para a API
        
    Returns:
        pd.DataFrame: DataFrame com as aulas
    """
    api = SponteAPI()
    
    # Preparar parâmetros
    params = kwargs.copy()
    if data_aula_inicio is not None:
        params["dataAulaInicio"] = data_aula_inicio
    if data_aula_fim is not None:
        params["dataAulaFim"] = data_aula_fim
    if situacao is not None:
        params["situacao"] = situacao
    if turma_id > 0:
        params["turmaId"] = turma_id
    if professor_id > 0:
        params["professorId"] = professor_id
    
    # Obter dados da API
    try:
        df = api.get_aulas(**params)
        return df
    except Exception as e:
        print(f"Erro ao obter aulas: {e}")
        return pd.DataFrame()

def get_contas_receber_df(situacao: Optional[int] = -1,
                        data_vencimento_inicio: Optional[str] = None,
                        data_vencimento_fim: Optional[str] = None,
                        **kwargs) -> pd.DataFrame:
    """
    Obtém as contas a receber da API e retorna como DataFrame
    
    Args:
        situacao (int, optional): Situação das contas (-1=Todas, 0=Pendentes, 1=Pagas). Defaults to -1.
        data_vencimento_inicio (str, optional): Data inicial de vencimento (formato YYYY-MM-DD). Defaults to None.
        data_vencimento_fim (str, optional): Data final de vencimento (formato YYYY-MM-DD). Defaults to None.
        **kwargs: Parâmetros adicionais para a API
        
    Returns:
        pd.DataFrame: DataFrame com as contas a receber
    """
    api = SponteAPI()
    
    # Preparar parâmetros
    params = kwargs.copy()
    if situacao != -1:
        params["situacao"] = situacao
    if data_vencimento_inicio is not None:
        params["dataVencimentoInicio"] = data_vencimento_inicio
    if data_vencimento_fim is not None:
        params["dataVencimentoFim"] = data_vencimento_fim
    
    # Obter dados da API
    try:
        df = api.get_contas_receber(situacao, data_vencimento_inicio, data_vencimento_fim, **params)
        return df
    except Exception as e:
        print(f"Erro ao obter contas a receber: {e}")
        return pd.DataFrame()

def get_contas_pagar_df(situacao: Optional[int] = -1,
                      data_vencimento_inicio: Optional[str] = None,
                      data_vencimento_fim: Optional[str] = None,
                      **kwargs) -> pd.DataFrame:
    """
    Obtém as contas a pagar da API e retorna como DataFrame
    
    Args:
        situacao (int, optional): Situação das contas (-1=Todas, 0=Pendentes, 1=Pagas). Defaults to -1.
        data_vencimento_inicio (str, optional): Data inicial de vencimento (formato YYYY-MM-DD). Defaults to None.
        data_vencimento_fim (str, optional): Data final de vencimento (formato YYYY-MM-DD). Defaults to None.
        **kwargs: Parâmetros adicionais para a API
        
    Returns:
        pd.DataFrame: DataFrame com as contas a pagar
    """
    api = SponteAPI()
    
    # Preparar parâmetros
    params = kwargs.copy()
    if situacao != -1:
        params["situacao"] = situacao
    if data_vencimento_inicio is not None:
        params["dataVencimentoInicio"] = data_vencimento_inicio
    if data_vencimento_fim is not None:
        params["dataVencimentoFim"] = data_vencimento_fim
    
    # Obter dados da API
    try:
        df = api.get_contas_pagar(situacao, data_vencimento_inicio, data_vencimento_fim, **params)
        return df
    except Exception as e:
        print(f"Erro ao obter contas a pagar: {e}")
        return pd.DataFrame()

def get_fluxo_caixa_df(data_inicio: str, data_fim: str, agrupamento: str = 'dia') -> pd.DataFrame:
    """
    Gera um relatório de fluxo de caixa para um período específico
    
    Args:
        data_inicio (str): Data inicial no formato YYYY-MM-DD
        data_fim (str): Data final no formato YYYY-MM-DD
        agrupamento (str, optional): Tipo de agrupamento ('dia', 'semana', 'mes'). Defaults to 'dia'.
        
    Returns:
        pd.DataFrame: DataFrame com o fluxo de caixa
    """
    api = SponteAPI()
    return api.get_fluxo_caixa(data_inicio, data_fim, agrupamento)

if __name__ == '__main__':

    print("Iniciando teste da API Sponte...")
    api = SponteAPI()
    
    # Testa se o token já está disponível
    if not api.token:
        print("Token não encontrado no .env. Tentando fazer login...")
        if not api.login():
            sys.exit(1)

    # Testa busca de alunos
    print("\nBuscando todos os alunos...")
    df_alunos = api.get_alunos()
    print(f"Total de alunos: {len(df_alunos)}")
    print(df_alunos.head())

    # Testa busca de aulas
    print("\nBuscando aulas do mês atual...")
    hoje = datetime.now()
    mes_atual = hoje.month
    ano_atual = hoje.year
    data_inicio = f"{ano_atual}-{mes_atual:02d}-01"
    data_fim = f"{ano_atual}-{mes_atual:02d}-{hoje.day:02d}"
    
    df_aulas = api.get_aulas(
        data_aula_inicio=data_inicio,
        data_aula_fim=data_fim
    )
    print(f"Total de aulas no período: {len(df_aulas)}")
    if not df_aulas.empty:
        print(df_aulas.head())