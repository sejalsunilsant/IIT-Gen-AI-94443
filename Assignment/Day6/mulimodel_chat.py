import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv
load_dotenv()

# ----------------- Functions -----------------
def groq_chat(message):
    api_key = os.getenv("groq_Api")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7,
        "max_tokens": 512
    }
    start = time.perf_counter()
    response = requests.post(url, headers=headers, json=payload)
    end = time.perf_counter()
    if response.status_code != 200:
        return "GROQ Error"
    reply = response.json()["choices"][0]["message"]["content"]
    reply += f"\n\n⏱ Time: {end - start:.2f}s"
    return reply

def lm_studio_chat(message):
    url = "http://127.0.0.1:1234/v1/chat/completions"
    headers = {"Authorization": "Bearer dummy-key", "Content-Type": "application/json"}
    payload = {"model": "phi-3.1-mini-4k-instruct", "messages": [{"role": "user", "content": message}]}
    start = time.perf_counter()
    response = requests.post(url, headers=headers, json=payload)
    end = time.perf_counter()
    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
        return f"{reply}\n\n⏱ Time: {end - start:.2f}s"
    else:
        return "LM Studio Error"

# ----------------- App Config -----------------
st.set_page_config(page_title="Multi Chatbot", page_icon="🤖")
st.title("🤖 Multi-Chatbot Interface")


# Sidebar
with st.sidebar:
    st.header("Select Chatbot")
    chatbot_options = ["GROQ", "LM Studio"]
    selected_bot = st.selectbox("Choose a chatbot:", chatbot_options)
    st.markdown("""
    <style>
    [data-testid="stSelectbox"] div[role="combobox"] {color: #ffffff !important;}
    </style>
    """, unsafe_allow_html=True)

# Sidebar Style
st.markdown("""
<style>
[data-testid="stSidebar"] {background-color: #000000; color: white;}
</style>
""", unsafe_allow_html=True)

# Chat history session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ----------------- Chat Input -----------------
user_input = st.chat_input("Ask anything...")

if user_input:
    # Generate bot reply
    if selected_bot == "GROQ":
        bot_reply = groq_chat(user_input)
        user_color = "#ff99ff"
        bot_color = "#00ffff"
    else:
        bot_reply = lm_studio_chat(user_input)
        user_color = "#00ff99"
        bot_color = "#c4ff4d"

    # Save to session state
    st.session_state.chat_history.append({
        "bot": selected_bot,
        "user": user_input,
        "response": bot_reply
    })

# ----------------- Display Chat -----------------
for chat in st.session_state.chat_history:
    if chat["bot"] == selected_bot:
        st.markdown(
            f"""
            <div style='text-align: left; background-color: {user_color};
                        padding: 10px; border-radius: 10px; margin: 5px 0;'>
                👨🏻‍💻: {chat["user"]}
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div style='text-align: left; background-color: {bot_color};
                        padding: 10px; border-radius: 10px; margin: 5px 0;'>
                👾: {chat["response"]}
            </div>
            """,
            unsafe_allow_html=True
        )
