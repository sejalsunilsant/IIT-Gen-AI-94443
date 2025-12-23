import os
import csv
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# LangChain
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.tools import tool

# ---------------- ENV ----------------
load_dotenv()

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="Agentic Internship Chatbot", layout="wide")
st.title("🤖 Agentic Internship Chatbot")

# ---------------- SCRAPING LOGIC (NORMAL FUNCTION) ----------------
def scrape_sunbeam_data():
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

# ---------------- TOOL FOR AGENT ----------------
@tool
def scrape_data_tool():
    """Scrapes internship data and saves it to CSV"""
    return scrape_sunbeam_data()

# ---------------- LOAD DATA ONCE ----------------
if "data" not in st.session_state:
    with st.spinner("Scraping internship data..."):
        st.session_state.data = scrape_sunbeam_data()

# ---------------- DISPLAY DATA ----------------
df = pd.DataFrame(st.session_state.data)
st.subheader("📊 Scraped Internship Data")
st.dataframe(df, use_container_width=True)

# ---------------- LLM SETUP ----------------
llm = init_chat_model(
    model="llama-3.3-70b-versatile",
    model_provider="openai",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("groq_Api")
)

agent = create_agent(
    model=llm,
    tools=[scrape_data_tool],
    system_prompt="""
    You are an academic data assistant.
    Answer questions ONLY using the internship data.
    If the answer is not present, say:
    "Not available in the data."
    """
)

# ---------------- CHATBOT ----------------
st.subheader("Ask anything.......")

user_question = st.chat_input("Ask a question based on the internship data")

if user_question:
    prompt = f"""
    Internship Data:
    {df.to_string(index=False)}

    Question:
    {user_question}

    Answer only using the above data.
    give some detail about answer which related to answer
    """

    response = llm.invoke(prompt)
    st.markdown(response.content)
