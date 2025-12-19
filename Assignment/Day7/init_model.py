from langchain.chat_models import init_chat_model
import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Standerd Chatbot", page_icon="🤖", layout="centered")

llm = init_chat_model(
    model = "llama-3.3-70b-versatile",
    model_provider = "openai",
    base_url = "https://api.groq.com/openai/v1",
    api_key = os.getenv("groq_Api")
)

# -------- Session State --------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------- Display History --------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------- User Input --------
user_chat = st.chat_input("Type your message...")

if user_chat:
    if user_chat.lower() == "clear":
        st.session_state.messages = []
        st.experimental_rerun()

    # Save user message
    st.session_state.messages.append(
        {"role": "user", "content": user_chat}
    )

    with st.chat_message("user"):
        st.markdown(user_chat)

    # Assistant response
    with st.chat_message("assistant"):
        full_response = ""
        stream = llm.stream(user_chat)

        for chunk in stream:
            if chunk.content:
                full_response += chunk.content
        st.markdown(full_response)

    # Save assistant message AFTER streaming
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )
