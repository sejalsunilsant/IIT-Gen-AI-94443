import pandas as pd
import streamlit as st
import os
from pandasql import sqldf

st.set_page_config(layout="wide")
st.title("SQL on CSV App ")

def run_sql(query, df, table_name):
    env = {table_name: df}
    return sqldf(query, env)

left_col, right_col = st.columns([1, 2])

with left_col:
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        table_name = os.path.splitext(uploaded_file.name)[0].replace(" ", "_")
        st.info(f"Table name: **{table_name}**")

        show_data = st.button("Display Table")

        query = st.text_area(
            "Enter SQL Query",
            f"SELECT * FROM {table_name} LIMIT 5"
        )

        run_query = st.button("Show Result")

with right_col:
    if uploaded_file is not None:
        try:
            if show_data:
                st.subheader(" Uploaded Table")
                st.dataframe(df)

            if query and run_query:
                st.subheader(" Query Result")
                result = run_sql(query, df, table_name)
                st.dataframe(result)
                st.snow()


        except Exception as e:
            st.error(f"SQL Error: {e}")
