import langchain
from langchain.chat_models import init_chat_model
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="MemoRAG Bot", page_icon="🤖", layout="centered")

llm = init_chat_model(
    model="llama-3.3-70b-versatile",
    model_provider="openai",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("groq_Api")
)

# ----------- SESSION MEMORY -----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

# ----------- DISPLAY CHAT HISTORY -----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------- SIDEBAR -----------
with st.sidebar:
    context_size = int(
        st.selectbox("Context Size", ["256", "512", "1024"], index=1)
    )

# ----------- USER INPUT -----------
user_msg = st.chat_input("Type your message...")

if user_msg:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_msg})
    st.session_state.conversation.append(
        {"role": "user", "content": user_msg}
    )

    with st.chat_message("user"):
        st.markdown(user_msg)

    # Assistant response
    with st.chat_message("assistant"):
        full_response = ""

        stream = llm.stream(
            st.session_state.conversation,
            max_tokens=context_size
        )

        for chunk in stream:
            if chunk.content:
                full_response += chunk.content
        st.markdown(full_response + "▌")

    # Save assistant response
    st.session_state.conversation.append(
        {"role": "assistant", "content": full_response}
    )
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )
