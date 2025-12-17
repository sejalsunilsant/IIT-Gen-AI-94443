import streamlit as st
import requests
import json
import time
import os   
from dotenv import load_dotenv
load_dotenv()
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
    time2= time.perf_counter()
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        return "GROQ Error"
    reply = response.json()["choices"][0]["message"]["content"]
    time3= time.perf_counter()
    reply += f"\n\n⏱ Time: {time3 - time2:.2f}s"
    return reply


def lm_studio_chat(message):
    url = "http://127.0.0.1:1234/v1/chat/completions"

    headers = {
        "Authorization": "Bearer dummy-key",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "phi-3.1-mini-4k-instruct",
        "messages": [{"role": "user", "content": message}]
    }

    start = time.perf_counter()
    response = requests.post(url, headers=headers, json=payload)
    end = time.perf_counter()

    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
        return f"{reply}\n\n⏱ Time: {end - start:.2f}s"
    else:
        return "LM Studio Error"


st.set_page_config(page_title="Multi Chatbot", page_icon="🤖")
st.title("🤖 Multi-Chatbot Interface")
st.markdown("""
<style>
/* Main app background */
.stApp {
    background-color: #0f172a;
}

/* Title */
h1 {
    color: #38bdf8;
    text-align: center;
}

/* Chat bubbles */
[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 10px;
    margin-bottom: 10px;
}

/* User message */
[data-testid="stChatMessage"][data-role="user"] {
    background-color: #1e293b;
}

/* Assistant message */
[data-testid="stChatMessage"][data-role="assistant"] {
    background-color: #020617;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #020617;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Select Chatbot")
    chatbot_options = ["GROQ", "LM Studio"]
    selected_bot = st.selectbox("Choose a chatbot:", chatbot_options)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Ask anything...")

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("assistant"):
        if selected_bot == "GROQ":
            bot_reply = groq_chat(user_input)
        elif selected_bot == "LM Studio":
            bot_reply = lm_studio_chat(user_input)
        else:
            bot_reply = "Bot not available"

        st.markdown(bot_reply)

    st.session_state.messages.append(
        {"role": "assistant", "content": bot_reply}
    )
