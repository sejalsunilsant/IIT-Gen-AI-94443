import streamlit as st
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()
# ------------------ Page Config ------------------
st.set_page_config(page_title="Weather App", layout="centered")

st.subheader("Welcome to Weather App")
st.caption("Application show weather using city name :)")

# ------------------ Session State ------------------
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False

if "user_data" not in st.session_state:
    st.session_state.user_data = pd.DataFrame({
        "Username": ["admin", "user1", "user2"],
        "Password": ["admin123", "user123", "user234"]
    })

if "page" not in st.session_state:
    st.session_state.page = "home"

# ------------------ Pages ------------------

def home_page():
    st.title("Home")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Log in", key="home_login"):
            st.session_state.page = "login"

    with col2:
        if st.button("Sign up", key="home_signup"):
            st.session_state.page = "signup"


def login_page():
    st.title("Login Page")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_btn"):
        if (
            username in st.session_state.user_data["Username"].values
            and password ==
            st.session_state.user_data[
                st.session_state.user_data["Username"] == username
            ]["Password"].iloc[0]
        ):
            st.success("Login Successful..... Redirecting to Weather Page")
            st.session_state.user_authenticated = True
            st.session_state.page = "weather"
            st.rerun()
        else:
            st.error("Invalid Username or Password")

    if st.button("⬅ Back", key="login_back"):
        st.session_state.page = "home"


def signup_page():
    st.title("Sign Up Page")

    new_user = st.text_input("New Username", key="signup_username")
    new_password = st.text_input("New Password", type="password", key="signup_password")

    if st.button("Create Account", key="signup_btn"):
        if not new_user or not new_password:
            st.error("Please fill all fields")
        elif new_user == new_password:
            st.error("Username and Password cannot be same")
        elif new_user in st.session_state.user_data["Username"].values:
            st.error("Username already exists")
        else:
            st.session_state.user_data.loc[len(st.session_state.user_data)] = [
                new_user, new_password
            ]
            st.success("Account Created Successfully..... Redirecting to Login Page")
            st.session_state.page = "login"
            st.rerun()

    if st.button("⬅ Back", key="signup_back"):
        st.session_state.page = "home"

def get_weather_info(city):
    api_key = os.getenv("API_weather_KEY")

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        return "City not found or API error"

    data = response.json()

    weather_info = f"""
     **City:** {city}  
     **Temperature:** {data['main']['temp']} °C  
     **Humidity:** {data['main']['humidity']} %  
     **Condition:** {data['weather'][0]['description'].title()}
    """

    return weather_info

def weather_page():
    if not st.session_state.user_authenticated:
        st.warning("Please login first to access the Weather Page")
        st.session_state.page = "login"
        st.rerun()

    st.title("Weather Page")

    city = st.text_input("Enter city name", key="weather_city")

    if st.button("Get Weather", key="get_weather"):
        if city.strip():
            result = get_weather_info(city)
            st.markdown(result)
        else:
            st.error("Please enter a city name")

    st.divider()

    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.user_authenticated = False
        st.session_state.page = "home"
        st.success("Logged out successfully")
        st.rerun()


# ------------------ Router ------------------
if st.session_state.page == "home":
    home_page()

elif st.session_state.page == "login":
    login_page()

elif st.session_state.page == "signup":
    signup_page()

elif st.session_state.page == "weather":
    weather_page()
