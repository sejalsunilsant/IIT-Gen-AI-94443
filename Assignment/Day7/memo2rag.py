import streamlit as st
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv
load_dotenv()

llm = init_chat_model(
    model = "llama-3.3-70b-versatile",
    model_provider = "openai",
    base_url = "https://api.groq.com/openai/v1",
    api_key = os.getenv("groq_Api")
)

if "conversation" not in st.session_state:
    st.session_state.conversation = []
    
k = st.slider("Decide the number of messages to remeber",min_value=1,max_value=20,value=1)

user_input = st.chat_input("Say something")

if user_input:
    st.session_state.conversation.append(
        {"role": "user", "content": user_input}
    )

    context = st.session_state.conversation[-k:]

    response = llm.invoke(context)

    st.session_state.conversation.append(
        {"role": "assistant", "content": response.content}
    )
    
for msg in st.session_state.conversation:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])