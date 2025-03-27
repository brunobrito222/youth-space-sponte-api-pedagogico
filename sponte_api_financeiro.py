import os
from typing import Optional, Dict, List, Any, Union
import requests
from dotenv import load_dotenv
import base64
import sys
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Carrega as variáveis do arquivo .env
load_dotenv()

class SponteAPI:
    def __init__(self):
        self.login_user = os.getenv('LOGIN')
        self.senha = os.getenv('SENHA')
        self.cod_cliente = 3751  # Código do cliente Sponte obrigatório
        
        # Verifica se as credenciais foram carregadas
        if not self.login_user or not self.senha:
            print("Erro: Credenciais não encontradas no arquivo .env")
            print(f"Login: {self.login_user}")
            print(f"Senha: {self.senha}")
            sys.exit(1)
            
        self.base_url = 'https://integracao.sponteweb.net.br'
        self.token = None
        
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
        if not self.token:
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
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f'Erro: {response.status_code}')
                print(f'Mensagem: {response.text}')
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar {full_url}: {e}")
            return None

    def get_alunos(self, situacao: int = -1, pagina: int = 1) -> Optional[Dict]:
        """
        Obtém a lista de alunos
        :param situacao: Situação do aluno (padrão: -1)
        :param pagina: Número da página para paginação (padrão: 1)
        :return: Dicionário com os dados dos alunos ou None se falhar
        """
        params = {"pagina": pagina}
        
        if situacao is not None:
            params["situacao"] = situacao
            
        return self.get_data('/api/v1/alunos', params)

    def get_contas_receber(self, 
                          situacao: Optional[int] = None,
                          aluno_id: Optional[int] = None,
                          data_vencimento_inicio: Optional[str] = None,
                          data_vencimento_fim: Optional[str] = None,
                          data_pagamento_inicio: Optional[str] = None,
                          data_pagamento_fim: Optional[str] = None,
                          plano_contas_id: Optional[int] = None,
                          valor_minimo: Optional[float] = None,
                          valor_maximo: Optional[float] = None,
                          pagina: int = 1,
                          todas_paginas: bool = False) -> Optional[Dict]:
        """
        Obtém contas a receber com base nos filtros fornecidos
        :param situacao: 0 para pendentes, 1 para pagas, -1 para todas
        :param aluno_id: ID do aluno para filtrar
        :param data_vencimento_inicio: Data inicial de vencimento (YYYY-MM-DD)
        :param data_vencimento_fim: Data final de vencimento (YYYY-MM-DD)
        :param data_pagamento_inicio: Data inicial de pagamento (YYYY-MM-DD)
        :param data_pagamento_fim: Data final de pagamento (YYYY-MM-DD)
        :param plano_contas_id: ID do plano de contas para filtrar
        :param valor_minimo: Valor mínimo das parcelas
        :param valor_maximo: Valor máximo das parcelas
        :param pagina: Número da página para paginação
        :param todas_paginas: Se True, retorna todas as páginas em uma única lista
        :return: Dicionário com os dados das contas ou None se falhar
        """
        params = {"pagina": pagina}
        
        if situacao is not None:
            params["situacao"] = situacao
        if aluno_id is not None:
            params["alunoID"] = aluno_id
        if data_vencimento_inicio:
            params["dataVencimentoInicio"] = data_vencimento_inicio
        if data_vencimento_fim:
            params["dataVencimentoFim"] = data_vencimento_fim
        if data_pagamento_inicio:
            params["dataPagamentoInicio"] = data_pagamento_inicio
        if data_pagamento_fim:
            params["dataPagamentoFim"] = data_pagamento_fim
        if plano_contas_id is not None:
            params["planoContasID"] = plano_contas_id
            
        if not todas_paginas:
            response = self.get_data('/api/v1/contasReceber', params)
            
            # Filtra por valor se necessário (pós-processamento)
            if response and response.get('listDados') and (valor_minimo is not None or valor_maximo is not None):
                filtered_dados = []
                for conta in response['listDados']:
                    try:
                        valor = float(conta.get('valor', 0))
                        if (valor_minimo is None or valor >= valor_minimo) and \
                           (valor_maximo is None or valor <= valor_maximo):
                            filtered_dados.append(conta)
                    except (ValueError, TypeError):
                        continue
                
                # Atualiza a lista de dados com os filtrados
                response['listDados'] = filtered_dados
                response['totalRegistros'] = len(filtered_dados)
                
            return response
            
        # Busca todas as páginas
        todas_contas = []
        while True:
            response = self.get_data('/api/v1/contasReceber', params)
            if not response or not response.get('listDados'):
                break
                
            # Filtra por valor se necessário
            if valor_minimo is not None or valor_maximo is not None:
                for conta in response['listDados']:
                    try:
                        valor = float(conta.get('valor', 0))
                        if (valor_minimo is None or valor >= valor_minimo) and \
                           (valor_maximo is None or valor <= valor_maximo):
                            todas_contas.append(conta)
                    except (ValueError, TypeError):
                        continue
            else:
                todas_contas.extend(response['listDados'])
            
            if pagina >= response.get('totalPaginas', 0):
                break
                
            pagina += 1
            params["pagina"] = pagina
            
        return {
            'listDados': todas_contas,
            'totalRegistros': len(todas_contas),
            'totalPaginas': 1,
            'paginaAtual': 1
        }

    def get_contas_pagar(self, 
                        situacao: Optional[int] = None,
                        aluno_id: Optional[int] = None,
                        conta_pagar_id: Optional[int] = None,
                        data_vencimento_inicio: Optional[str] = None,
                        data_vencimento_fim: Optional[str] = None,
                        data_pagamento_inicio: Optional[str] = None,
                        data_pagamento_fim: Optional[str] = None,
                        pagina: int = 1,
                        todas_paginas: bool = False) -> Optional[Dict]:
        """
        Obtém contas a pagar com base nos filtros fornecidos
        :param situacao: 0 para pendentes, 1 para pagas
        :param aluno_id: ID do aluno para filtrar
        :param conta_pagar_id: ID específico da conta a pagar
        :param data_vencimento_inicio: Data inicial de vencimento (YYYY-MM-DD)
        :param data_vencimento_fim: Data final de vencimento (YYYY-MM-DD)
        :param data_pagamento_inicio: Data inicial de pagamento (YYYY-MM-DD)
        :param data_pagamento_fim: Data final de pagamento (YYYY-MM-DD)
        :param pagina: Número da página para paginação
        :param todas_paginas: Se True, retorna todas as páginas em uma única lista
        :return: Dicionário com os dados das contas ou None se falhar
        """
        params = {"pagina": pagina}
        
        if situacao is not None:
            params["situacao"] = situacao
        if aluno_id is not None:
            params["alunoID"] = aluno_id
        if conta_pagar_id is not None:
            params["contaPagarID"] = conta_pagar_id
        if data_vencimento_inicio:
            params["dataVencimentoInicio"] = data_vencimento_inicio
        if data_vencimento_fim:
            params["dataVencimentoFim"] = data_vencimento_fim
        if data_pagamento_inicio:
            params["dataPagamentoInicio"] = data_pagamento_inicio
        if data_pagamento_fim:
            params["dataPagamentoFim"] = data_pagamento_fim
            
        if not todas_paginas:
            return self.get_data('/api/v1/contasPagar', params)
            
        # Busca todas as páginas
        todas_contas = []
        while True:
            response = self.get_data('/api/v1/contasPagar', params)
            if not response or not response.get('listDados'):
                break
                
            todas_contas.extend(response['listDados'])
            
            if pagina >= response.get('totalPaginas', 0):
                break
                
            pagina += 1
            params["pagina"] = pagina
            
        return {
            'listDados': todas_contas,
            'totalRegistros': len(todas_contas),
            'totalPaginas': 1,
            'paginaAtual': 1
        }

    def get_total_recebido_periodo(self, 
                                 data_inicio: str, 
                                 data_fim: str) -> float:
        """
        Calcula o total recebido em um período específico
        :param data_inicio: Data inicial (YYYY-MM-DD)
        :param data_fim: Data final (YYYY-MM-DD)
        :return: Valor total recebido no período
        """
        response = self.get_contas_receber(
            situacao=1,  # Apenas contas pagas
            data_pagamento_inicio=data_inicio,
            data_pagamento_fim=data_fim,
            todas_paginas=True
        )
        
        if not response or not response.get('listDados'):
            return 0.0
            
        return sum(float(conta.get('valor', 0)) for conta in response['listDados'])

    def get_parcelas_vencidas(self, dias_atraso: Optional[int] = None, categorizar: bool = False) -> Union[List[Dict], Dict[str, List[Dict]]]:
        """
        Obtém lista de parcelas vencidas
        :param dias_atraso: Filtrar por número mínimo de dias de atraso
        :param categorizar: Se True, retorna as parcelas categorizadas por faixas de atraso
        :return: Lista de parcelas vencidas ou dicionário com parcelas categorizadas
        """
        response = self.get_contas_receber(
            situacao=0,  # Apenas contas pendentes
            todas_paginas=True
        )
        
        if not response or not response.get('listDados'):
            return [] if not categorizar else {
                "ate_15_dias": [],
                "16_30_dias": [],
                "31_60_dias": [],
                "61_90_dias": [],
                "acima_90_dias": []
            }
            
        todas_parcelas = []
        data_atual = datetime.now()
        
        # Categorias para classificação
        categorias = {
            "ate_15_dias": [],
            "16_30_dias": [],
            "31_60_dias": [],
            "61_90_dias": [],
            "acima_90_dias": []
        }
        
        # Filtra as parcelas vencidas
        for parcela in response['listDados']:
            try:
                valor = float(parcela.get('valor', 0))
                if valor <= 0:  # Ignora parcelas sem valor ou com valor inválido
                    continue
                    
                data_vencimento = self.parse_date(parcela.get('dataVencimento'))
                if not data_vencimento:  # Ignora parcelas sem data de vencimento
                    continue
                    
                if data_vencimento < data_atual:
                    dias_vencidos = (data_atual - data_vencimento).days
                    
                    # Adiciona informações úteis à parcela
                    parcela['dias_atraso'] = dias_vencidos
                    parcela['valor_float'] = valor  # Valor já convertido para float
                    parcela['data_vencimento_obj'] = data_vencimento
                    
                    # Calcula juros estimados (1% ao mês, proporcional aos dias)
                    taxa_juros_diaria = 0.01 / 30  # 1% ao mês dividido por 30 dias
                    juros_estimados = valor * taxa_juros_diaria * dias_vencidos
                    parcela['juros_estimados'] = round(juros_estimados, 2)
                    parcela['valor_atualizado'] = round(valor + juros_estimados, 2)
                    
                    if dias_atraso is None or dias_vencidos >= dias_atraso:
                        todas_parcelas.append(parcela)
                        
                        # Categoriza a parcela
                        if dias_vencidos <= 15:
                            categorias["ate_15_dias"].append(parcela)
                        elif 16 <= dias_vencidos <= 30:
                            categorias["16_30_dias"].append(parcela)
                        elif 31 <= dias_vencidos <= 60:
                            categorias["31_60_dias"].append(parcela)
                        elif 61 <= dias_vencidos <= 90:
                            categorias["61_90_dias"].append(parcela)
                        else:
                            categorias["acima_90_dias"].append(parcela)
            except (ValueError, TypeError) as e:
                print(f"Erro ao processar parcela: {e}")
                continue
        
        # Ordena as parcelas pelo número de dias de atraso (decrescente)
        todas_parcelas.sort(key=lambda p: p.get('dias_atraso', 0), reverse=True)
        
        if categorizar:
            # Adiciona estatísticas para cada categoria
            for categoria, parcelas in categorias.items():
                total_valor = sum(p.get('valor_float', 0) for p in parcelas)
                total_atualizado = sum(p.get('valor_atualizado', 0) for p in parcelas)
                
                categorias[categoria] = {
                    'parcelas': parcelas,
                    'quantidade': len(parcelas),
                    'valor_total': round(total_valor, 2),
                    'valor_atualizado': round(total_atualizado, 2)
                }
            
            return categorias
                    
        return todas_parcelas

    def get_resumo_financeiro(self, 
                            mes: Optional[int] = None, 
                            ano: Optional[int] = None,
                            incluir_detalhes: bool = False) -> Dict[str, Any]:
        """
        Gera um resumo financeiro do período especificado
        :param mes: Mês para análise (1-12)
        :param ano: Ano para análise (YYYY)
        :param incluir_detalhes: Se True, inclui listas detalhadas de parcelas no resultado
        :return: Dicionário com o resumo financeiro
        :raises ValueError: Se os parâmetros de mês ou ano forem inválidos
        :raises RequestError: Se houver erro na comunicação com a API
        """
        # Se mês e ano não forem especificados, usa o mês atual
        if mes is None or ano is None:
            hoje = datetime.now()
            mes = mes or hoje.month
            ano = ano or hoje.year

        # Valida os parâmetros
        if not (1 <= mes <= 12):
            raise ValueError("Mês deve estar entre 1 e 12")
        if ano < 2000:
            raise ValueError("Ano inválido")

        # Define o período de análise
        data_inicio = f"{ano}-{mes:02d}-01"
        if mes == 12:
            data_fim = f"{ano+1}-01-01"
        else:
            data_fim = f"{ano}-{mes+1:02d}-01"
        
        # Restante da função permanece igual
        try:
            # Obtém dados financeiros
            total_recebido = self.get_total_recebido_periodo(data_inicio, data_fim)
            parcelas_vencidas = self.get_parcelas_vencidas()
            
            # Filtra parcelas com valores válidos
            parcelas_vencidas = [p for p in parcelas_vencidas if p.get('valor')]
            
            # Calcula totais
            total_vencido = sum(float(p.get('valor', 0)) for p in parcelas_vencidas)
            total_vencido_mes = sum(
                float(p.get('valor', 0)) 
                for p in parcelas_vencidas 
                if p.get('dataVencimento', '').startswith(f"{ano}-{mes:02d}")
            )
            
            # Obtém contas a receber do mês (pagas e pendentes)
            response = self.get_contas_receber(
                data_vencimento_inicio=data_inicio,
                data_vencimento_fim=data_fim,
                todas_paginas=True
            )
            
            if not response or not response.get('listDados'):
                contas_mes = []
            else:
                # Filtra contas com valores válidos
                contas_mes = [c for c in response['listDados'] if c.get('valor')]
                
            # Calcula totais do mês
            total_previsto = sum(float(c.get('valor', 0)) for c in contas_mes)
            total_pendente = sum(
                float(c.get('valor', 0)) 
                for c in contas_mes 
                if c.get('situacao') == 0
            )
            
            try:
                # Calcula percentuais
                taxa_inadimplencia = (total_vencido / total_previsto * 100) if total_previsto > 0 else 0
                taxa_recebimento = (total_recebido / total_previsto * 100) if total_previsto > 0 else 0
            except ZeroDivisionError:
                taxa_inadimplencia = 0
                taxa_recebimento = 0
            
            resumo = {
                'periodo': f"{mes:02d}/{ano}",
                'total_recebido': round(total_recebido, 2),
                'total_previsto': round(total_previsto, 2),
                'total_pendente': round(total_pendente, 2),
                'total_vencido': round(total_vencido, 2),
                'total_vencido_mes': round(total_vencido_mes, 2),
                'parcelas_vencidas': len(parcelas_vencidas),
                'taxa_inadimplencia': round(taxa_inadimplencia, 2),
                'taxa_recebimento': round(taxa_recebimento, 2)
            }
            
            if incluir_detalhes:
                resumo['contas_mes'] = contas_mes
                resumo['parcelas_vencidas'] = parcelas_vencidas
            
            return resumo
            
        except requests.exceptions.RequestException as e:
            print(f"Erro na comunicação com a API: {e}")
            raise
        except ValueError as e:
            print(f"Erro de validação: {e}")
            raise
        except Exception as e:
            print(f"Erro inesperado ao gerar resumo financeiro: {e}")
            raise

    def print_resumo_financeiro(self, resumo: Optional[Dict[str, Any]]) -> None:
        """
        Imprime o resumo financeiro de forma organizada
        :param resumo: Dicionário com o resumo financeiro
        """
        if not resumo:
            print("\nNão foi possível gerar o resumo financeiro")
            return
            
        print(f"\nResumo Financeiro - {resumo['periodo']}")
        print("=" * 50)
        
        # Informações gerais
        print("\n-- Visão Geral --")
        print(f"Total Previsto: R$ {resumo.get('total_previsto', 0):,.2f}")
        print(f"Total Recebido: R$ {resumo.get('total_recebido', 0):,.2f}")
        print(f"Total Pendente: R$ {resumo.get('total_pendente', 0):,.2f}")
        print(f"Total Vencido: R$ {resumo.get('total_vencido', 0):,.2f}")
        print(f"Total Vencido no Mês: R$ {resumo.get('total_vencido_mes', 0):,.2f}")
        
        # Informações adicionais se disponíveis
        if 'ticket_medio' in resumo:
            print(f"Ticket Médio: R$ {resumo['ticket_medio']:,.2f}")
        
        # Indicadores
        print("\n-- Indicadores --")
        print(f"Parcelas Vencidas: {resumo.get('parcelas_vencidas', 0)}")
        print(f"Taxa de Inadimplência: {resumo.get('taxa_inadimplencia', 0):.1f}%")
        print(f"Taxa de Recebimento: {resumo.get('taxa_recebimento', 0):.1f}%")
        
        if 'taxa_pendencia' in resumo:
            print(f"Taxa de Pendência: {resumo['taxa_pendencia']:.1f}%")
        
        # Análise de faixas de atraso se disponível
        if 'faixas_atraso' in resumo:
            print("\n-- Análise de Inadimplência por Faixa de Atraso --")
            faixas = resumo['faixas_atraso']
            
            # Formata os nomes das faixas para exibição
            nomes_faixas = {
                'ate_15_dias': 'Até 15 dias',
                '16_30_dias': '16 a 30 dias',
                '31_60_dias': '31 a 60 dias',
                '61_90_dias': '61 a 90 dias',
                'acima_90_dias': 'Acima de 90 dias'
            }
            
            for chave, nome in nomes_faixas.items():
                if chave in faixas:
                    faixa = faixas[chave]
                    if isinstance(faixa, dict):
                        qtd = faixa.get('quantidade', 0)
                        valor = faixa.get('valor', 0)
                        print(f"{nome}: {qtd} parcelas - R$ {valor:,.2f}")
        
        print("=" * 50)
        
        # Se há detalhes disponíveis, oferece opção de visualizá-los
        if 'detalhes' in resumo:
            print("\nDetalhes adicionais disponíveis:")
            if 'parcelas_vencidas' in resumo['detalhes']:
                print(f"- {len(resumo['detalhes']['parcelas_vencidas'])} parcelas vencidas")
            if 'contas_mes' in resumo['detalhes']:
                print(f"- {len(resumo['detalhes']['contas_mes'])} contas do mês")
            if 'contas_pagas' in resumo['detalhes']:
                print(f"- {len(resumo['detalhes']['contas_pagas'])} contas pagas")
            if 'parcelas_pendentes' in resumo['detalhes']:
                print(f"- {len(resumo['detalhes']['parcelas_pendentes'])} contas pendentes")
        
        print("=" * 50)

    def print_alunos(self, data: Dict[str, Any], title: str) -> None:
        """
        Imprime informações dos alunos de forma organizada
        :param data: Dados dos alunos a serem impressos
        :param title: Título da seção
        """
        print(f"\n{title}")
        print("=" * len(title))
        
        if not data or not data.get('listDados'):
            print("Nenhum aluno encontrado")
            return
            
        for aluno in data['listDados']:
            print("\nCampos disponíveis:", aluno.keys())
            
            nome = aluno.get('nomeAluno', 'Não informado')
            print(f"\nNome: {nome}")
                
            email = aluno.get('emailPadrao')
            if email:
                print(f"Email: {email}")
                
            cpf = aluno.get('cpf')
            if cpf:
                print(f"CPF: {cpf}")
                
            celular = aluno.get('celular')
            if celular:
                print(f"Celular: {celular}")
                
            telefone = aluno.get('telefone')
            if telefone:
                print(f"Telefone: {telefone}")
                
            situacao_id = aluno.get('situacaoID')
            if situacao_id is not None:
                print(f"ID da Situação: {situacao_id}")
                
            situacao = aluno.get('situacao', 'Não informado')
            print(f"Status: {situacao}")
            
            print("-" * 50)
        
        print(f"\nPágina atual: {data.get('paginaAtual', 1)}")
        print(f"Total de páginas: {data.get('totalPaginas', 0)}")

    def print_total_recebido(self, valor: float, periodo: str) -> None:
        """
        Imprime o total recebido em um período
        :param valor: Valor total recebido
        :param periodo: Descrição do período
        """
        print(f"\nTotal Recebido - {periodo}")
        print("=" * (15 + len(periodo)))
        print(f"R$ {valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))

    def print_parcelas_vencidas(self, parcelas: List[Dict], title: str) -> None:
        """
        Imprime informações das parcelas vencidas
        :param parcelas: Lista de parcelas vencidas
        :param title: Título da seção
        """
        print(f"\n{title}")
        print("=" * len(title))
        
        if not parcelas:
            print("Nenhuma parcela vencida encontrada")
            return
            
        # Calcula totais
        total_valor_original = sum(float(p.get('valor_float', p.get('valor', 0))) for p in parcelas)
        total_juros = sum(float(p.get('juros_estimados', 0)) for p in parcelas)
        total_atualizado = sum(float(p.get('valor_atualizado', p.get('valor', 0))) for p in parcelas)
        
        # Imprime resumo
        print(f"\nTotal de parcelas vencidas: {len(parcelas)}")
        print(f"Valor original total: R$ {total_valor_original:,.2f}")
        print(f"Juros estimados total: R$ {total_juros:,.2f}")
        print(f"Valor atualizado total: R$ {total_atualizado:,.2f}")
        print("-" * 50)
        
        # Agrupa por faixas de atraso para análise
        faixas = {
            "Até 15 dias": [],
            "16 a 30 dias": [],
            "31 a 60 dias": [],
            "61 a 90 dias": [],
            "Acima de 90 dias": []
        }
        
        for parcela in parcelas:
            dias = parcela.get('dias_atraso', 0)
            if dias <= 15:
                faixas["Até 15 dias"].append(parcela)
            elif 16 <= dias <= 30:
                faixas["16 a 30 dias"].append(parcela)
            elif 31 <= dias <= 60:
                faixas["31 a 60 dias"].append(parcela)
            elif 61 <= dias <= 90:
                faixas["61 a 90 dias"].append(parcela)
            else:
                faixas["Acima de 90 dias"].append(parcela)
        
        # Imprime análise por faixa de atraso
        print("\nAnálise por faixa de atraso:")
        for faixa, items in faixas.items():
            if items:
                valor_faixa = sum(float(p.get('valor_float', p.get('valor', 0))) for p in items)
                print(f"{faixa}: {len(items)} parcelas - R$ {valor_faixa:,.2f}")
        
        print("-" * 50)
        
        # Imprime detalhes de cada parcela
        print("\nDetalhes das parcelas:")
        for parcela in parcelas:
            print(f"\nAluno ID: {parcela.get('alunoID', 'N/A')}")
            print(f"Plano: {parcela.get('planoContasDescricao', 'N/A')}")
            
            valor = float(parcela.get('valor_float', parcela.get('valor', 0)))
            print(f"Valor original: R$ {valor:.2f}")
            
            if 'juros_estimados' in parcela:
                print(f"Juros estimados: R$ {parcela.get('juros_estimados', 0):.2f}")
                print(f"Valor atualizado: R$ {parcela.get('valor_atualizado', 0):.2f}")
            
            vencimento = parcela.get('dataVencimento', 'N/A').split('T')[0]
            print(f"Vencimento: {vencimento}")
            print(f"Dias em atraso: {parcela.get('dias_atraso', 0)}")
            print("-" * 50)

    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Converte string de data para objeto datetime
        :param date_str: String de data no formato ISO
        :return: Objeto datetime ou None se inválido
        """
        if not date_str:
            return None
            
        try:
            # Remove Z e ajusta para UTC
            clean_date = date_str.replace('Z', '+00:00')
            return datetime.fromisoformat(clean_date)
        except (ValueError, AttributeError):
            return None

    def _ultimo_dia_mes(self, mes: int, ano: int) -> int:
        """
        Retorna o último dia do mês
        :param mes: Mês (1-12)
        :param ano: Ano
        :return: Último dia do mês
        """
        if mes == 12:
            ultimo_dia = (datetime(ano + 1, 1, 1) - relativedelta(days=1)).day
        else:
            ultimo_dia = (datetime(ano, mes + 1, 1) - relativedelta(days=1)).day
        return ultimo_dia
        
if __name__ == '__main__':
    print("Iniciando teste da API Sponte...")
    api = SponteAPI()
    
    # Testa o login
    if not api.login():
        sys.exit(1)

    # Teste dos endpoints contasPagar e contasReceber
    
    # 1. Teste de contas a receber pendentes
    print("\n=== TESTE DO ENDPOINT contasReceber (PENDENTES) ===")
    hoje = datetime.now()
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    # Define o período de seleção
    mes_anterior = mes_atual - 1
    if mes_anterior == 0:
        mes_anterior = 12
        ano_atual -= 1
    
    data_inicio = f"{ano_atual}-{mes_anterior:02d}-01"
    data_fim = f"{ano_atual}-{mes_atual:02d}-01"
    
    print(f"Buscando contas a receber pendentes para o período: {data_inicio} a {data_fim}")
    parcelas_pendentes = api.get_contas_receber(
        situacao=0,  # Pendentes
        data_vencimento_inicio=data_inicio,
        data_vencimento_fim=data_fim,
        pagina=2
    )
    
    if parcelas_pendentes and parcelas_pendentes.get('listDados'):
        print(f"Total de contas pendentes encontradas: {len(parcelas_pendentes['listDados'])}")
        print("Exemplo da primeira conta:")
        primeira_conta = parcelas_pendentes['listDados'][0]
        print(f"  Conta Receber ID: {primeira_conta.get('contaReceberID')}")
        print(f"  Aluno ID: {primeira_conta.get('alunoID')}")
        print(f"  Plano: {primeira_conta.get('planoContasDescricao')}")
        print(f"  Valor do Plano: R$ {primeira_conta.get('valorPlano')}")

        
        # Verifica se há parcelas
        if 'parcelas' in primeira_conta and primeira_conta['parcelas']:
            print("  Informações da primeira parcela:")
            parcela = primeira_conta['parcelas'][0]
            print(f"    Número da Parcela: {parcela.get('numeroParcela')}")
            print(f"    Situação: {parcela.get('situacao')}")
            print(f"    Valor: R$ {parcela.get('valor')}")
            print(f"    Data de Vencimento: {parcela.get('dataVencimento')}")
    else:
        print("Nenhuma conta pendente encontrada para o período especificado.")
    


    # 2. Teste de contas a receber pagas
    print("\n=== TESTE DO ENDPOINT contasReceber (QUITADAS) ===")
    parcelas_quitadas = api.get_contas_receber(
        situacao=1,  # Quitadas
        data_pagamento_inicio=data_inicio,
        data_pagamento_fim=data_fim
    )
    
    if parcelas_quitadas and parcelas_quitadas.get('listDados'):
        print(f"Total de contas quitadas encontradas: {len(parcelas_quitadas['listDados'])}")
        print("Exemplo da primeira conta quitada:")
        primeira_conta = parcelas_quitadas['listDados'][0]
        print(f"  Conta Receber ID: {primeira_conta.get('contaReceberID')}")
        print(f"  Aluno ID: {primeira_conta.get('alunoID')}")
        print(f"  Plano: {primeira_conta.get('planoContasDescricao')}")
        print(f"  Valor do Plano: R$ {primeira_conta.get('valorPlano')}")
        
        # Verifica se há parcelas
        if 'parcelas' in primeira_conta and primeira_conta['parcelas']:
            print("  Informações da primeira parcela:")
            parcela = primeira_conta['parcelas'][0]
            print(f"    Número da Parcela: {parcela.get('numeroParcela')}")
            print(f"    Situação: {parcela.get('situacao')}")
            print(f"    Valor: R$ {parcela.get('valor')}")
            print(f"    Valor Pago: R$ {parcela.get('valorPago')}")
            print(f"    Data de Pagamento: {parcela.get('dataPagamento')}")
    else:
        print("Nenhuma conta paga encontrada para o período especificado.")
    


    # 3. Teste de contas a pagar (pendentes)
    print("\n=== TESTE DO ENDPOINT contasPagar (PENDENTES) ===")
    contas_pagar = api.get_contas_pagar(
        data_vencimento_inicio=data_inicio,
        data_vencimento_fim=data_fim,
        situacao=0
    )
    
    if contas_pagar and contas_pagar.get('listDados'):
        print(f"Total de contas a pagar encontradas: {len(contas_pagar['listDados'])}")
        print("Exemplo da primeira conta a pagar:")
        primeira_conta = contas_pagar['listDados'][0]
        print(f"  Conta Pagar ID: {primeira_conta.get('contaPagarID')}")
        print(f"  Funcionário ID: {primeira_conta.get('funcionarioID')}")
        print(f"  Empresa ID: {primeira_conta.get('empresaID')}")
        print(f"  Plano: {primeira_conta.get('planoContasDescricao')}")
        print(f"  Valor do Plano: R$ {primeira_conta.get('valorPlano')}")
        
        # Verifica se há parcelas
        if 'parcelas' in primeira_conta and primeira_conta['parcelas']:
            print("  Informações da primeira parcela:")
            parcela = primeira_conta['parcelas'][0]
            print(f"    Número da Parcela: {parcela.get('numeroParcela')}")
            print(f"    Situação: {parcela.get('situacao')}")
            print(f"    Valor: R$ {parcela.get('valor')}")
            print(f"    Data de Vencimento: {parcela.get('dataVencimento')}")
    else:
        print("Nenhuma conta a pagar encontrada para o período especificado.")
    


    # 4. Teste de contas a pagar (quitadas)
    print("\n=== TESTE DO ENDPOINT contasPagar (QUITADAS) ===")
    contas_pagar = api.get_contas_pagar(
        data_vencimento_inicio=data_inicio,
        data_vencimento_fim=data_fim,
        situacao=1 # Quitadas
    )
    
    if contas_pagar and contas_pagar.get('listDados'):
        print(f"Total de contas a pagar encontradas: {len(contas_pagar['listDados'])}")
        print("Exemplo da primeira conta a pagar:")
        primeira_conta = contas_pagar['listDados'][0]
        print(f"  Conta Pagar ID: {primeira_conta.get('contaPagarID')}")
        print(f"  Funcionário ID: {primeira_conta.get('funcionarioID')}")
        print(f"  Empresa ID: {primeira_conta.get('empresaID')}")
        print(f"  Plano: {primeira_conta.get('planoContasDescricao')}")
        print(f"  Valor do Plano: R$ {primeira_conta.get('valorPlano')}")
        
        # Verifica se há parcelas
        if 'parcelas' in primeira_conta and primeira_conta['parcelas']:
            print("  Informações da primeira parcela:")
            parcela = primeira_conta['parcelas'][0]
            print(f"    Número da Parcela: {parcela.get('numeroParcela')}")
            print(f"    Situação: {parcela.get('situacao')}")
            print(f"    Valor: R$ {parcela.get('valor')}")
            print(f"    Data de Vencimento: {parcela.get('dataVencimento')}")
    else:
        print("Nenhuma conta a pagar encontrada para o período especificado.")
    

    # Comentando as chamadas para as outras funções que podem não estar implementadas
    # print("\nGerando análise de tendências...")
    # tendencia = api.get_analise_tendencia()
    # SponteAPI.print_analise_tendencia(tendencia)
    
    # print("\nGerando fluxo de caixa...")
    # fluxo = api.get_fluxo_caixa()
    # SponteAPI.print_fluxo_caixa(fluxo)
    
    # print("\nGerando análise de rentabilidade das turmas...")
    # rentabilidade = api.get_rentabilidade_turmas()
    # SponteAPI.print_rentabilidade_turmas(rentabilidade)
