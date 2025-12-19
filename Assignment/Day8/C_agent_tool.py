from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
import streamlit as st
import requests
import time
import os
from dotenv import load_dotenv
import json
load_dotenv()

# -------- Tool --------
@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.It accuratly calculate expression without wrong way.
    It follow mathamatical rules correctly.
    This calculator function solves any arithmetic expression containing all constant values.
    Supports +, -, *, /, %, and brackets.
    it has eval() function that easily calculate
    :param expression: str input arithmetic expression
    :returns expression result as str
    
    """
    try:
        return str(eval(expression))
    except Exception:
        return "Error"
# ----------- WEATHER FUNCTION -----------
@tool
def get_weather(city :str)->str:
    """
    This get_weather() function gets the current weather of given city.
    If weather cannot be found, it returns 'Error'.
    This function doesn't return historic or general weather of the city.

    :param city: str input - city name
    :returns current weather in json format or 'Error'   
    :output: based on return value we can exaplin weather in detail
    """
    api_key = os.getenv("API_weather_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    time1=time.time()
    response = requests.get(url)
    time2=time.time()
    print(f"Weather API response time: {time2-time1} seconds")

    if response.status_code != 200:
        return None

    data = response.json()
    result={
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "wind": data["wind"]["speed"]
    }
    return json.dumps(result)

@tool
def read_file(filepath: str) -> str:
    """
    Read the contents of a local text file and return it as a string.

    This tool opens a file from the local filesystem using the provided
    file path and reads its entire content. It is intended for reading
    plain text files such as .txt, .md, .py, or .json files.

    Parameters:
        filepath (str): Absolute or relative path to the local file.

    Returns:
        str: The full text content of the file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If the file cannot be read.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
    
# -------- UI --------
st.title("Agentic LLM 🤖")

# -------- Session State --------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": "You are an experienced assistant."}
    ]

# -------- Display Chat --------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------- Model --------
llm = init_chat_model(
    model="phi-3.1-mini-4k-instruct",
    model_provider="openai",
    base_url="http://127.0.0.1:1234/v1",
    api_key="my_openai_api_key"
)

agent = create_agent(
    model=llm,
    tools=[calculator,get_weather,read_file],
    system_prompt="""
You are a helpful and intelligent assistant.

Use tools only when they are strictly necessary to complete the user’s request.
Do not invoke any tool for general knowledge, descriptive, or informational questions.
Do not fabricate or repeat tool calls.
If no tool is required, answer directly using your own knowledge.
When a tool is used, use it exactly once and rely only on its output.
Keep responses concise and relevant.


"""
)

# -------- Input --------
user_input = st.chat_input("Ask anything...")

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    st.session_state.conversation.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    response = agent.invoke(
        {"messages": st.session_state.conversation}
    )
    print(response)
    assistant_reply = response["messages"][-1].content

    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_reply}
    )
    st.session_state.conversation.append(
        {"role": "assistant", "content": assistant_reply}
    )
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)
#----------tool Call--------------------------------
        st.markdown("### 🛠 Tool Usage")
        tool_found = False
        for msg in response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_found = True
                for tool in msg.tool_calls:
                    st.write("**Tool Name:**", tool["name"])

        if not tool_found:
            st.info("No tools were used by the agent.")
