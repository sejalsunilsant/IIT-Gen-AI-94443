import pandas as pd
import streamlit as st
import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

# -------- UI --------
st.title("Agentic LLM 🤖")

# -------- Session State --------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": "You are an academic education expert."}
    ]

if "explained" not in st.session_state:
    st.session_state.explained = False

#-----------------
def scrapping_data():
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import csv

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    driver.get("https://www.sunbeaminfo.in/internship")
    driver.implicitly_wait(5)

    table1 = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[@id='collapseSix']//table")
        )
    )

    rows = table1.find_elements(By.XPATH, ".//tbody/tr")

    table_data = []
    with open("table_data.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = [cell.get_attribute("textContent").strip() for cell in cells]
            writer.writerow(row_data)
            table_data.append(row_data)

    driver.quit()
    return table_data

#-----------------
uploaded_file = scrapping_data()
st.session_state.data = uploaded_file

if st.session_state.data:
    st.dataframe(uploaded_file)

# -------- LLM --------
llm = init_chat_model(
    model="llama-3.3-70b-versatile",
    model_provider="openai",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("groq_Api")
)

# -------- Explanation (FIXED) --------
if st.session_state.data and not st.session_state.explained:
    explain_prompt = f"""
Explain the result of the Scrapped data: {uploaded_file} in simple English.
"""
    st.session_state.conversation.append(
        {"role": "user", "content": explain_prompt}
    )

    explained = llm.invoke(st.session_state.conversation)
    st.subheader("Explanation of the Result")
    st.markdown(explained.content)

    st.session_state.explained = True

# -------- Chat Q&A --------
user_question = st.chat_input("Enter your question about the data:")

if user_question and uploaded_file is not None:
    prompt = f"""
You are a data-aware assistant.
Answer ONLY using the provided internship data.
If answer is not present in data, say "Not available in the data."
Asked question: {user_question}
"""

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    st.session_state.conversation.append(
        {"role": "user", "content": prompt}
    )

    response = llm.invoke(st.session_state.conversation)
    st.markdown(response.content)
