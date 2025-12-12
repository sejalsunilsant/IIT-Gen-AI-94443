import requests
import os

def get_weather():
    api_key = "86307b059853ce0c374e803250a32f67" 
    city = input("Enter city name: ")
    url=f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)
    data = response.json()

    if data["cod"] == 200:
        weather=f"Weather in {city}:\nTemperature: {data['main']['temp']} C\nHumidity: {data['main']['humidity']}%\nDescription: {data['weather'][0]['description']}"
        print(f"Weather in {city}:")
        print(f"Temperature: {data['main']['temp']}°C")
        print(f"Humidity: {data['main']['humidity']}%")
        print(f"Description: {data['weather'][0]['description']}")
    else:
        print("City not found or API error.")

    return weather
def save_weather_to_File():
    data = get_weather()
    path="D:\Sunbeam\Assignments\Day3\Q3\weather_data.txt"
    with open(path, 'w') as file:
        file.write(str(data))
    print(f"Weather data saved to {path}")
save_weather_to_File()