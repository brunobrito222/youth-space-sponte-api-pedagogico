# Dashboard Sponte

Um dashboard interativo para visualização de dados da API Sponte, desenvolvido com Streamlit.

## Funcionalidades

- **Página de Turmas**: Visualização de turmas ativas, encerradas ou em formação, com filtros por modalidade, curso, estágio e professor.
- **Página de Alunos**: Lista de alunos ativos com informações detalhadas.
- **Página de Aulas**: Visualização de aulas confirmadas ou pendentes, com filtros por data.
- **Consulta Financeira**: Visualização de valores financeiros por turma.

## Requisitos

- Python 3.8+
- Bibliotecas listadas em `requirements.txt`

## Configuração Local

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/youth-dashboard.git
   cd youth-dashboard
   ```

2. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Crie um arquivo `.env` na raiz do projeto com suas credenciais:
   ```
   LOGIN=seu_login_sponte
   SENHA=sua_senha_sponte
   ```

4. Execute o aplicativo localmente:
   ```bash
   streamlit run app.py
   ```

## Deploy no Streamlit Cloud

1. Faça o upload do código para um repositório GitHub (certifique-se de que o arquivo `.env` está no `.gitignore`).

2. Acesse [Streamlit Cloud](https://share.streamlit.io/) e faça login com sua conta GitHub.

3. Clique em "New app" e selecione seu repositório.

4. Configure as seguintes opções:
   - **Repository**: Seu repositório GitHub
   - **Branch**: main (ou a branch que contém seu código)
   - **Main file path**: app.py

5. Em "Advanced settings" > "Secrets", adicione suas credenciais da API Sponte:
   ```
   LOGIN=seu_login_sponte
   SENHA=sua_senha_sponte
   ```

6. Clique em "Deploy" e aguarde o processo de implantação.

## Estrutura do Projeto

- `app.py`: Arquivo principal do aplicativo
- `pages/`: Módulos para cada página do dashboard
- `utils/`: Funções utilitárias e de cache
- `sponte_api_functions.py`: Funções para interação com a API Sponte
- `sponte_api_financeiro.py`: Funções para dados financeiros da API Sponte
- `requirements.txt`: Lista de dependências do projeto

## Manutenção

Para atualizar o aplicativo no Streamlit Cloud após alterações no código:
1. Faça commit e push das alterações para o GitHub
2. O Streamlit Cloud detectará automaticamente as alterações e reimplantará o aplicativo
