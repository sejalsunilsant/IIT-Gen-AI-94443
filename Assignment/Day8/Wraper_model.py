from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call
import streamlit as st
import logging

# ---------------- Logging Setup ----------------
logging.basicConfig(level=logging.INFO)

# ---------------- Middleware -------------------

@wrap_model_call
def limit_context(requests, handler):
    """
    Keeps only the last 5 messages to control context size
    """
    if hasattr(requests, "messages") and len(requests.messages) > 5:
        requests.messages = requests.messages[-5:]

    return handler(requests)


@wrap_model_call
def model_logger(requests, handler):
    """
    Logs request and response safely
    """
    logging.info(f"LLM called with {len(requests.messages)} messages")

    response = handler(requests)

    if response and response.result:
        logging.info("LLM response received")

    return response


@wrap_model_call
def output_formatter(requests, handler):
    """
    Formats model output
    """
    response = handler(requests)

    if response and response.result:
        response.result[0].content = response.result[0].content.strip()

    return response


# ---------------- Streamlit UI -----------------

st.set_page_config(page_title="Agentic LLM", page_icon="🤖")
st.title("Agentic LLM 🤖")

# ---------------- Session State ----------------



if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": "You are an experienced assistant."}
    ]

# ---------------- Display Chat -----------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- Model ------------------------

llm = init_chat_model(
    model="phi-3.1-mini-4k-instruct",
    model_provider="openai",
    base_url="http://127.0.0.1:1234/v1",
    api_key="my_openai_api_key"
)

agent = create_agent(
    model=llm,
    tools=[],
    middleware=[
        limit_context,
        model_logger,
        output_formatter
    ],
    system_prompt=(
        "You are a helpful assistant. "
        "Answer in short. "
        "Output: short answer with main steps only."
    )
)

# ---------------- Input ------------------------

user_input = st.chat_input("Ask anything...")

if user_input:
    # Store user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    st.session_state.conversation.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # Invoke agent
    response = agent.invoke(
        {"messages": st.session_state.conversation}
    )

    assistant_reply = response["messages"][-1].content

    # Store assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_reply}
    )
    st.session_state.conversation.append(
        {"role": "assistant", "content": assistant_reply}
    )

    with st.chat_message("assistant"):
        st.markdown(assistant_reply)
