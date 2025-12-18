import pandas as pd
import streamlit as st
import os
from pandasql import sqldf
import langchain
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    table_name = os.path.splitext(uploaded_file.name)[0].replace(" ", "_")
    st.info(f"Table name: **{table_name}**")
    if st.button("Display Table"):
        st.subheader(" Uploaded Table")
        st.dataframe(df)

user_question = st.text_area("Enter your question about the data:")

llm = init_chat_model(
    model="llama-3.3-70b-versatile",
    model_provider="openai",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("groq_Api")
)

conversation = [
    {"role": "system", "content": "You are SQLite expert developer with 10 years of experience."}   
]

if user_question and uploaded_file is not None:
    query_prompt = f""" Generate an SQLite query to answer the question: {user_question} based on the table {table_name}.Generate SQL query only in plain text format and nothing else.
            If you cannot generate the query, then output 'Error'."""
    conversation.append({"role": "user", "content": query_prompt})

    response = llm.invoke(conversation)
    sql_query = response.content.strip()
    st.subheader("Generated SQL Query")
    st.code(sql_query, language="sql")

    try:
        env = {table_name: df}
        query_result = sqldf(sql_query, env)
        st.subheader("Query Result")
        st.dataframe(query_result)
    except Exception as e:
        st.error(f"SQL Error: {e}")
# ask to explain result in English.
    explain_prompt = f"""Explain the result of the SQL query: {sql_query} in simple English."""
    conversation.append({"role": "user", "content": explain_prompt})

    explanation = llm.invoke(conversation)
    st.subheader("Explanation of the Result")
    st.markdown(explanation.content)