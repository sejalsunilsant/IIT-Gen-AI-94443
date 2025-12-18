from dotenv import load_dotenv
import os
import streamlit as st
from langchain_groq import ChatGroq

# ----------------- Setup -----------------
load_dotenv()

st.set_page_config(page_title="Grok Chatbot", page_icon="🤖", layout="centered")

api_key = os.getenv("groq_Api")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=api_key
)

st.title("🤖 Chatbot")
# ----------------- Session State -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------- Display Chat History -----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------------- User Input -----------------
user_prompt = st.chat_input("Type your message...")

if user_prompt:
    # Show user message
    st.session_state.messages.append(
        {"role": "user", "content": user_prompt}
    )

    with st.chat_message("user"):
        st.markdown(user_prompt)

    # AI response (streaming)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        for chunk in llm.stream(user_prompt):
            full_response += chunk.content
            placeholder.markdown(full_response + "▌")

        placeholder.markdown(full_response)

    # Save AI message
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )
