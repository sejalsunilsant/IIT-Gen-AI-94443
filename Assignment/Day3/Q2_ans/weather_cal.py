import requests
import os
def get_weather():
    api_key = os.getenv("API_weather_KEY")
    city = input("Enter city name: ")
    url=f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)
    data = response.json()

    if data["cod"] == 200:
        print(f"Weather in {city}:")
        print(f"Temperature: {data['main']['temp']}°C")
        print(f"Humidity: {data['main']['humidity']}%")
        print(f"Description: {data['weather'][0]['description']}")
    else:
        print("City not found or API error.")
get_weather()        