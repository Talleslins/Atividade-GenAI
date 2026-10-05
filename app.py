import os
import re
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# 1. Configuração da Página e Carregamento de Variáveis
st.set_page_config(page_title="CineData Analytics", page_icon="🎬", layout="wide")
load_dotenv()

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    st.error("Chave da API não encontrada. Verifique o arquivo .env.")
    st.stop()

MODEL_NAME = "google/gemini-3.5-flash-lite"
DB_PATH = "cinerocket.db"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


# 2. Funções de Banco de Dados e Guardrails
def get_database_schema():
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        st.error(f"O arquivo '{DB_PATH}' não foi encontrado ou está vazio.")
        st.stop()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        schemas = cursor.fetchall()
        return "\n\n".join([schema[0] for schema in schemas if schema[0]])


DB_SCHEMA = get_database_schema()

DOMAIN_CONTEXT = """
Regras de Negócio e Contexto do Domínio (CineData Analytics):
1. "Receita", "Faturamento" e "Bilheteria" são equivalentes. Utilize as colunas correspondentes em fact_movies_performance.
2. "Lucro" deve ser calculado subtraindo o orçamento (budget) da receita (revenue). Filtre apenas registros onde ambas as colunas sejam maiores que zero.
3. Relacionamentos do modelo dimensional:
   - Filmes e gêneros: utilize bridge_movie_genre ligando dim_movies a dim_genres.
   - Filmes e pessoas (elenco/direção): utilize bridge_movie_person ligando dim_movies a dim_people.
4. Utilize sintaxe estrita do SQLite3.
"""


def is_safe_query(query: str) -> bool:
    forbidden_pattern = r"(?i)(^\s*|;\s*)(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|REPLACE|GRANT|REVOKE)\b"
    return not bool(re.search(forbidden_pattern, query))


def run_query(query: str):
    if not is_safe_query(query):
        return "Erro de Segurança: A query foi bloqueada pois apenas operações de leitura são permitidas."
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn)
    except Exception as e:
        return str(e)


# 3. Motor Text-to-SQL
def generate_sql_with_self_correction(user_question: str, max_retries: int = 2):
    system_prompt = f"""
    Você é um Engenheiro de Dados especialista em SQLite.
    SCHEMA DO BANCO DE DADOS:
    {DB_SCHEMA}

    REGRAS DO DOMÍNIO:
    {DOMAIN_CONTEXT}

    Retorne APENAS o código SQL puro para SQLite3. Não inclua formatação markdown ou textos explicativos.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Pergunta: {user_question}"}
    ]

    for attempt in range(max_retries):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.0,
            max_tokens=500
        )
        sql_query = response.choices[0].message.content.strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        result = run_query(sql_query)

        if isinstance(result, str):
            messages.append({"role": "assistant", "content": sql_query})
            messages.append({
                "role": "user",
                "content": f"Erro retornado pelo banco: {result}. Corrija a query e retorne apenas o código SQL corrigido."
            })
        else:
            return sql_query, result
    return None, None


# 4. Geração de Gráficos
def generate_chart(df: pd.DataFrame, title: str):
    if df.shape[1] == 2 and not df.empty:
        num_cols = df.select_dtypes(include=['number']).columns
        cat_cols = df.select_dtypes(exclude=['number']).columns

        if len(num_cols) == 1 and len(cat_cols) == 1:
            fig, ax = plt.subplots(figsize=(10, 5))
            df_plot = df.sort_values(by=num_cols[0], ascending=False).head(10)
            sns.barplot(
                data=df_plot, x=num_cols[0], y=cat_cols[0],
                hue=cat_cols[0], palette="viridis", legend=False, ax=ax
            )
            ax.set_title(f"Análise: {title}", fontsize=12, pad=15)
            ax.set_xlabel(num_cols[0].replace('_', ' ').title(), fontsize=10)
            ax.set_ylabel(cat_cols[0].replace('_', ' ').title(), fontsize=10)
            plt.tight_layout()
            return fig
    return None


# 5. Interface Gráfica Streamlit
st.title("🎬 CineData Analytics")
st.markdown("Faça perguntas em linguagem natural sobre o catálogo de filmes.")

# Gerenciamento de Estado (Memória da Sessão)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Renderiza o histórico da conversa
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            if "error" in msg:
                st.error(msg["error"])
            else:
                st.code(msg["sql"], language="sql")
                st.dataframe(msg["df"], use_container_width=True)
                if msg.get("fig") is not None:
                    st.pyplot(msg["fig"])

# Campo de entrada do usuário
if prompt := st.chat_input("Ex: Quais são os Top 10 filmes com maior receita?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analisando o banco de dados..."):
            sql_query, df_result = generate_sql_with_self_correction(prompt)

            if isinstance(df_result, str):
                st.error(df_result)
                st.session_state.messages.append({"role": "assistant", "error": df_result})
            elif df_result is None or df_result.empty:
                st.warning("A consulta não retornou resultados.")
                st.session_state.messages.append({"role": "assistant", "error": "A consulta não retornou resultados."})
            else:
                st.code(sql_query, language="sql")
                st.dataframe(df_result, use_container_width=True)
                fig = generate_chart(df_result, prompt)
                if fig:
                    st.pyplot(fig)

                # Salva no histórico
                st.session_state.messages.append({
                    "role": "assistant",
                    "sql": sql_query,
                    "df": df_result,
                    "fig": fig
                })