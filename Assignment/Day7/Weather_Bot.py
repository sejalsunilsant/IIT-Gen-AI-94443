import streamlit as st
import os
import requests
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

st.set_page_config(page_title="Weather Bot", page_icon="🤖", layout="centered")
st.title("🌤️ Weather Bot")

# ----------- LLM INIT -----------
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
        {"role": "system", "content": "You explain weather in very simple English."}
    ]

# ----------- DISPLAY CHAT HISTORY -----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------- WEATHER FUNCTION -----------
def get_weather(city):
    api_key = os.getenv("API_weather_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()
    return {
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "wind": data["wind"]["speed"]
    }

# ----------- USER INPUT -----------
user_city = st.chat_input("Enter city name to get weather information...")

if user_city:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_city})
    with st.chat_message("user"):
        st.markdown(user_city)

    weather = get_weather(user_city)

    if weather is None:
        with st.chat_message("assistant"):
            st.error("City not found or API error")
    else:
        # Build LLM prompt using real data
        prompt = f"""
        City: {user_city}
        Temperature: {weather['temp']} °C
        Humidity: {weather['humidity']} %
        Wind Speed: {weather['wind']} m/s
        Condition: {weather['description']}

        Explain this weather in very simple English.
        """

        st.session_state.conversation.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("assistant"):
            full_response = ""
            stream = llm.stream(st.session_state.conversation)
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
