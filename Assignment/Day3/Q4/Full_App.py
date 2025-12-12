import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv() 
API_KEY = os.getenv("API_weather_KEY")
st.title("🌤 Weather App")
city = st.text_input("Enter City Name:")

if st.button("Get Weather"):
    if city:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        
        response = requests.get(url)
        data = response.json()
        
        if data.get("cod") != 200:
            st.error("City not found! Please enter a valid city.")
        else:
            st.success(f"Weather in {city.title()}")

            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]

            st.write(f"**Condition:** {weather}")
            st.write(f"**Temperature:** {temp} °C")
            st.write(f"**Feels Like:** {feels_like} °C")
            st.write(f"**Humidity:** {humidity}%")
            st.write(f"**Wind Speed:** {wind} m/s")
    else:
        st.warning("Enter a city name to continue")
