# GitHub Data Crawler

Este script é usado para rastrear a web e extrair dados relevantes do GitHub para um conjunto de repositórios.

Este repositório tem como objetivo fornecer a implementação técnica do projeto de pesquisa "Determinantes de Sucesso em Projetos de Software" para o MBA em Gestão de Projetos da POLI-USP.

**Disclaimer**: Este projeto não contempla a coleta de dados, apenas o código fonte para a extração de dados. A reprodução dos dados apresentados no trabalho pode não ser possível devido ao tempo passado desde a coleta original.

O projeto não foi otimizado para coleta em paralelo, mas pode ser facilmente adaptado para tal caso seja necessário e o limite de requisições da API do GitHub seja compatível.

## Estrutura do Projeto

```
.env
.gitignore
notebooks
    exploratory_analysis.ipynb
crawl.py
doc/
    diagram.drawio
    diagram.drawio.png
```

## Requisitos

- Python 3.7+
- Um token de acesso ao GitHub (GITHUB_TOKEN)

## Instalação

1. Clone o repositório:

```sh
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

2. Crie um ambiente virtual e ative-o:

```sh
python -m venv venv
source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
```

3. Instale as dependências:

```sh
pip install -r requirements.txt
```

4. Crie um arquivo .env na raiz do projeto e adicione seu token do GitHub:

```
GITHUB_TOKEN=seu_token_aqui
```

## Uso

Para executar o script, use o seguinte comando:

```sh
python crawl.py
```

O script irá extrair dados da API do GitHub para um conjunto de repositórios definidos no código e consolidar os dados em um banco de dados DuckDB.

Os dados brutos serão armazenados na pasta data.

## Estrutura dos Dados Extraídos

Os dados extraídos serão armazenados na pasta data com a seguinte estrutura:

- `base/`: Dados básicos dos repositórios
- `branches/`: Dados dos branches
- `commits/`: Dados dos commits
- `contributors/`: Dados dos contribuidores
- `issues/`: Dados dos issues
- `pull_requests/`: Dados dos pull requests
- `releases/`: Dados dos releases
- `workflows/`: Dados dos workflows

