import json
import random
import sys

import requests
from bs4 import BeautifulSoup


def get_random_file(path):
    return random.choice(tuple(path.iterdir()))


def get_weather():
    url = f"https://yandex.ru/pogoda/langepas?lat=61.253701&lon=75.180725"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        temp = soup.find("div", class_="weather__article_main_temp").text.strip()
        sunrise = soup.find("div", class_="ss_wrap ru").findAll("span")[0].text
        sunset = soup.find("div", class_="ss_wrap ru").findAll("span")[1].text
        pressure = soup.find("div", class_="table__col current").find("div", class_="table__pressure").text
        humidity = soup.find("div", class_="table__col current").find("div", class_="table__humidity").text
        wind = soup.find("div", class_="table__col current").findAll("label", class_="show-tooltip")[1].text
        weather_data = {
            "temp": temp,
            "sunrise": sunrise,
            "sunset": sunset,
            "pressure": pressure,
            "humidity": humidity,
            "wind": wind
        }
        return weather_data


def get_wind_direction(deg):
    l = ['С ','СВ',' В','ЮВ','Ю ','ЮЗ',' З','СЗ']
    for i in range(0,8):
        step = 45.
        min = i*step - 45/2.
        max = i*step + 45/2.
        if i == 0 and deg > 360-45/2.:
            deg = deg - 360
        if deg >= min and deg <= max:
            res = l[i]
            break
    return res


def get_city_id(s_city_name):
    appid = "fee2f032237baea4ed7328ea3c188911"
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/find",
                     params={'q': s_city_name, 'type': 'like', 'units': 'metric', 'lang': 'ru', 'APPID': appid})
        data = res.json()
        cities = ["{} ({})".format(d['name'], d['sys']['country'])
                  for d in data['list']]
        print("city:", cities)
        city_id = data['list'][0]['id']
        print('city_id=', city_id)
    except Exception as e:
        print("Exception (find):", e)
        pass
    assert isinstance(city_id, int)
    return city_id


def request_current_weather(city_id):
    appid = "fee2f032237baea4ed7328ea3c188911"
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/weather",
                     params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': appid})
        data = res.json()
        pog = "Погода: " + str(data['weather'][0]['description'])
        temp = "Температура: " + str(data['main']['temp'])
        speed = "Скорость ветра: " + str(data['wind']['speed'])
        return pog, temp, speed

    except Exception as e:
        return "Exception (weather):", e
        pass


def request_forecast(city_id):
    appid = "fee2f032237baea4ed7328ea3c188911"
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                           params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': appid})
        data = res.json()
        print('city:', data['city']['name'], data['city']['country'])
        for i in data['list']:
            print( (i['dt_txt'])[:16], '{0:+3.0f}'.format(i['main']['temp']),
                   '{0:2.0f}'.format(i['wind']['speed']) + " м/с",
                   get_wind_direction(i['wind']['deg']),
                   i['weather'][0]['description'] )
    except Exception as e:
        print("Exception (forecast):", e)
        pass
