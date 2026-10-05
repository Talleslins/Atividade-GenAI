# CineData Analytics - Agente GenAI Text-to-SQL

Projeto desenvolvido para a Atividade GenAI do Rocket Lab 2026 da Visagio. A aplicação consiste em um agente de Inteligência Artificial capaz de realizar consultas e análises sobre o catálogo de filmes da CineData Analytics utilizando linguagem natural. 

O agente traduz perguntas de usuários não técnicos para consultas SQL (Text-to-SQL) operando diretamente sobre a camada Gold do Data Lakehouse (banco SQLite `cinerocket.db`), gerando respostas tabulares e visuais em tempo real.

## Funcionalidades Implementadas

* **Tradução Text-to-SQL com Self-Correction:** O agente gera consultas SQL a partir de linguagem natural e possui um mecanismo de auto-correção caso o banco de dados retorne erros de sintaxe ou de mapeamento.
* **Interface Gráfica Interativa:** Aplicação web completa desenvolvida com Streamlit, contendo histórico de conversa e renderização nativa de DataFrames.
* **Visualização de Dados Automática (Bônus):** Geração automática de gráficos de barras horizontais utilizando Matplotlib e Seaborn para consultas analíticas (ex: Top 10, Maior Lucro).
* **Segurança e Guardrails (Bônus):** Implementação de bloqueios via Regex contra injeção de comandos destrutivos (DROP, DELETE, UPDATE), garantindo que apenas operações de leitura sejam executadas na base de dados.
* **Otimização de Cota (Single-Call Pipeline & Caching):** Arquitetura desenhada para consumir o mínimo de tokens possível de contas gratuitas no OpenRouter, combinando chamadas únicas ao LLM e cache de respostas em memória.

## Tecnologias Utilizadas

* Python 3.10+
* Streamlit (Interface Web)
* OpenAI API via OpenRouter (Modelo utilizado: gemini-3.5-flash-lite)
* Pandas, Matplotlib e Seaborn (Manipulação e Visualização de Dados)
* SQLite3 (Banco de Dados Local)

## Como Executar o Projeto

Siga o passo a passo abaixo para rodar a aplicação localmente a partir do zero.

### 1. Clonar o Repositório e Preparar o Banco de Dados
Clone este repositório para a sua máquina local:
```bash
git clone https://github.com/Talleslins/Atividade-GenAI.git
cd Atividade GenAI
```
**Importante:** Faça o download do arquivo `cinerocket.db` disponibilizado na pasta da atividade e coloque-o na raiz do projeto (mesmo diretório do arquivo `app.py`).

### 2. Criar e Ativar o Ambiente Virtual
É recomendado o uso de um ambiente virtual para isolar as dependências do projeto.
```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar no Windows:
venv\Scripts\activate
# Ativar no Linux/Mac:
source venv/bin/activate
```

### 3. Instalar as Dependências
Com o ambiente ativado, execute o comando abaixo no terminal para instalar todas as bibliotecas necessárias:
```bash
pip install openai pandas matplotlib seaborn python-dotenv streamlit
```

### 4. Configurar Variáveis de Ambiente
Crie um arquivo chamado `.env` na raiz do projeto e adicione a sua chave de API do OpenRouter:
```text
OPENROUTER_API_KEY=sua_chave_api_aqui
```

### 5. Iniciar a Aplicação
Execute o servidor do Streamlit com o comando:
```bash
streamlit run app.py
```
A aplicação abrirá automaticamente no seu navegador padrão no endereço `http://localhost:8501`.

## Exemplos de Consultas Suportadas

O agente responde a perguntas de diversas categorias analíticas. Experimente os seguintes comandos na interface:

* "Quais são os Top 10 filmes com maior receita em R$?"
* "Qual diretor possui a maior nota média? Considere apenas diretores com no mínimo 5 filmes."
* "Qual é a produtora com o maior lucro total considerando todos os seus filmes?"
* "Quantidade de filmes por gênero"