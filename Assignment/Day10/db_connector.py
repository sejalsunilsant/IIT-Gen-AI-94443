import mysql.connector
import streamlit as st
import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="MySQL Chatbot", layout="wide")
st.title("MySQL Database Chatbot")

host = "localhost"
user = "root"
password = "manager"
database = "sunbeam"
table_name = "employees"

try:
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    cursor = conn.cursor()
except Exception as e:
    st.error(e)
    st.stop()

if st.checkbox("Preview Table"):
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    st.table([dict(zip(columns, row)) for row in rows])

user_question = st.text_area("Ask a question about the data")

llm = init_chat_model(
    model="llama-3.3-70b-versatile",
    model_provider="openai",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("groq_Api")
)

conversation = [
    {
        "role": "system",
        "content": "You are an expert MySQL developer. Generate valid MySQL queries only."
    }
]

if user_question:
    sql_prompt = f"""
    Generate a MySQL SQL query for the question:
    "{user_question}"
    using table {table_name}.
    Output only SQL.
    no description ,no markdowns pure sql query only.
    """

    conversation.append({"role": "user", "content": sql_prompt})
    response = llm.invoke(conversation)
    sql_query = response.content.strip()

    st.code(sql_query, language="sql")

    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        st.table(result)
    except Exception as e:
        st.error(e)
        st.stop()

    explain_prompt = f"Explain the result of this SQL query in simple English: {sql_query}"
    conversation.append({"role": "user", "content": explain_prompt})
    explanation = llm.invoke(conversation)
    st.markdown(explanation.content)

cursor.close()
conn.close()
