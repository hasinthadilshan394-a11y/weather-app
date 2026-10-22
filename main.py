__version__ = "1.0.0"

import json
import threading
import urllib.parse
import urllib.request
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle

BG = (0.025, 0.065, 0.12, 1)
PANEL = (0.055, 0.12, 0.21, 1)
PANEL_ALT = (0.075, 0.16, 0.27, 1)
BLUE = (0.12, 0.48, 0.95, 1)
WHITE = (0.95, 0.97, 1, 1)
MUTED = (0.67, 0.76, 0.88, 1)
GREEN = (0.20, 0.85, 0.54, 1)

WEATHER = {
    0: ("☀", "Clear sky"), 1: ("🌤", "Mainly clear"),
    2: ("⛅", "Partly cloudy"), 3: ("☁", "Overcast"),
    45: ("🌫", "Fog"), 48: ("🌫", "Rime fog"),
    51: ("🌦", "Light drizzle"), 53: ("🌦", "Drizzle"),
    55: ("🌧", "Dense drizzle"), 56: ("🌧", "Freezing drizzle"),
    57: ("🌧", "Heavy freezing drizzle"), 61: ("🌧", "Light rain"),
    63: ("🌧", "Moderate rain"), 65: ("🌧", "Heavy rain"),
    66: ("🌧", "Freezing rain"), 67: ("🌧", "Heavy freezing rain"),
    71: ("🌨", "Light snow"), 73: ("🌨", "Snow"),
    75: ("❄", "Heavy snow"), 77: ("🌨", "Snow grains"),
    80: ("🌦", "Rain showers"), 81: ("🌧", "Rain showers"),
    82: ("⛈", "Heavy showers"), 85: ("🌨", "Snow showers"),
    86: ("❄", "Heavy snow"), 95: ("⛈", "Thunderstorm"),
    96: ("⛈", "Thunderstorm with hail"), 99: ("⛈", "Severe thunderstorm"),
}

def api_json(base_url, params):
    url = base_url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "WeatherApp/1.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def fetch_weather(city):
    geo = api_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "en", "format": "json"},
    )
    results = geo.get("results", [])
    if not results:
        raise ValueError("City not found. Check the spelling and try again.")
    place = results[0]
    data = api_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "timezone": "auto",
            "forecast_days": 5,
        },
    )
    return place, data

class RoundedPanel(BoxLayout):
    def __init__(self, panel_color=PANEL, **kwargs):
        super().__init__(**kwargs)
        self.panel_color = panel_color
        with self.canvas.before:
            self._color = Color(*panel_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

class WeatherApp(App):
    def build(self):
        self.title = "Weather App"
        Window.clearcolor = BG
        self.favourites = []
        self.root_box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(72), spacing=dp(2))
        header.add_widget(self.make_label("🌤  WEATHER APP", 23, WHITE, "left"))
        header.add_widget(self.make_label("Live weather for any city", 13, MUTED, "left"))
        self.root_box.add_widget(header)

        search_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        self.city_input = TextInput(
            text="Colombo", hint_text="Enter city name", multiline=False,
            font_size=dp(16), foreground_color=WHITE, hint_text_color=MUTED,
            background_normal="", background_active="", background_color=PANEL_ALT,
            padding=[dp(12), dp(12), dp(12), dp(8)], cursor_color=WHITE
        )
        self.city_input.bind(on_text_validate=lambda *_: self.search_weather())
        search_row.add_widget(self.city_input)
        search_btn = Button(
            text="Search", size_hint_x=None, width=dp(95), font_size=dp(15),
            bold=True, color=WHITE, background_normal="", background_down="",
            background_color=BLUE
        )
        search_btn.bind(on_release=lambda *_: self.search_weather())
        search_row.add_widget(search_btn)
        self.root_box.add_widget(search_row)

        self.status = self.make_label("Connecting to weather service…", 12, MUTED, "left")
        self.status.size_hint_y = None
        self.status.height = dp(25)
        self.root_box.add_widget(self.status)

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.content = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        self.root_box.add_widget(scroll)

        self.hero = RoundedPanel(orientation="vertical", padding=dp(18), spacing=dp(5),
                                 size_hint_y=None, height=dp(230))
        self.location = self.make_label("Your city", 23, WHITE, "left")
        self.country = self.make_label("Current conditions", 13, MUTED, "left")
        self.hero.add_widget(self.location)
        self.hero.add_widget(self.country)
        self.temp_row = BoxLayout(size_hint_y=None, height=dp(92), spacing=dp(10))
        self.icon_label = self.make_label("🌤", 54, WHITE, "center")
        self.icon_label.size_hint_x = None
        self.icon_label.width = dp(88)
        self.temp_label = self.make_label("--°C", 42, WHITE, "left")
        self.temp_row.add_widget(self.icon_label)
        self.temp_row.add_widget(self.temp_label)
        self.hero.add_widget(self.temp_row)
        self.condition = self.make_label("Waiting for weather data…", 16, MUTED, "left")
        self.hero.add_widget(self.condition)
        self.hero.add_widget(self.make_label("Live data • Open-Meteo", 11, MUTED, "left"))
        self.content.add_widget(self.hero)

        metrics_title = self.make_label("WEATHER DETAILS", 13, MUTED, "left")
        metrics_title.size_hint_y = None
        metrics_title.height = dp(24)
        self.content.add_widget(metrics_title)

        metrics = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(150))
        self.feels_value = self.metric(metrics, "🌡  FEELS LIKE", "--°C")
        self.humidity_value = self.metric(metrics, "💧  HUMIDITY", "--%")
        self.wind_value = self.metric(metrics, "💨  WIND SPEED", "-- km/h")
        self.rain_value = self.metric(metrics, "🌦  CONDITION", "—")
        self.content.add_widget(metrics)

        forecast_title = self.make_label("5-DAY FORECAST", 13, MUTED, "left")
        forecast_title.size_hint_y = None
        forecast_title.height = dp(24)
        self.content.add_widget(forecast_title)
        self.forecast = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_y=None)
        self.forecast.bind(minimum_height=self.forecast.setter("height"))
        self.content.add_widget(self.forecast)

        fav_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        fav_btn = Button(
            text="★  Add to favourites", font_size=dp(14), color=WHITE,
            background_normal="", background_down="", background_color=PANEL_ALT
        )
        fav_btn.bind(on_release=lambda *_: self.toggle_favourite())
        fav_row.add_widget(fav_btn)
        self.fav_status = self.make_label("No saved cities", 11, MUTED, "center")
        fav_row.add_widget(self.fav_status)
        self.content.add_widget(fav_row)

        self.last_place = None
        self.last_data = None
        Clock.schedule_once(lambda _dt: self.search_weather(), 0.5)
        return self.root_box

    def make_label(self, text, size, color, halign="left"):
        label = Label(
            text=text, font_size=dp(size), color=color, halign=halign,
            valign="middle", size_hint_y=None, height=dp(max(size * 1.7, 24))
        )
        label.bind(size=lambda inst, _size: setattr(inst, "text_size", (inst.width, None)))
        return label

    def metric(self, parent, heading, value):
        panel = RoundedPanel(orientation="vertical", padding=dp(10), spacing=dp(2),
                             size_hint_y=None, height=dp(70))
        panel.add_widget(self.make_label(heading, 10, MUTED, "left"))
        value_label = self.make_label(value, 18, WHITE, "left")
        panel.add_widget(value_label)
        parent.add_widget(panel)
        return value_label

    def search_weather(self):
        city = self.city_input.text.strip()
        if not city:
            self.status.text = "Type a city name first."
            return
        self.status.color = MUTED
        self.status.text = "Fetching live weather…"
        threading.Thread(target=self._worker, args=(city,), daemon=True).start()

    def _worker(self, city):
        try:
            result = fetch_weather(city)
            Clock.schedule_once(lambda _dt: self.show_weather(*result), 0)
        except Exception as exc:
            message = str(exc)
            Clock.schedule_once(lambda _dt, m=message: self.show_error(m), 0)

    def show_error(self, message):
        self.status.text = message[:180]
        self.status.color = (1, 0.55, 0.55, 1)

    def show_weather(self, place, data):
        self.last_place, self.last_data = place, data
        current = data["current"]
        code = int(current["weather_code"])
        icon, description = WEATHER.get(code, ("🌍", "Other conditions"))
        city = place.get("name", "Unknown city")
        subline = " • ".join(x for x in [place.get("admin1", ""), place.get("country", "")] if x)
        self.location.text = "⌖  " + city
        self.country.text = subline or "Current conditions"
        self.icon_label.text = icon
        self.temp_label.text = f"{current['temperature_2m']:.1f}°C"
        self.condition.text = description
        self.feels_value.text = f"{current['apparent_temperature']:.1f}°C"
        self.humidity_value.text = f"{current['relative_humidity_2m']}%"
        self.wind_value.text = f"{current['wind_speed_10m']} km/h"
        self.rain_value.text = description

        self.forecast.clear_widgets()
        daily = data.get("daily", {})
        for i, date_text in enumerate(daily.get("time", [])):
            try:
                date = datetime.strptime(date_text, "%Y-%m-%d")
                day = "Today" if i == 0 else date.strftime("%a, %d %b")
            except ValueError:
                day = date_text
            f_icon, f_desc = WEATHER.get(int(daily["weather_code"][i]), ("🌍", "Conditions"))
            row = RoundedPanel(panel_color=PANEL_ALT, orientation="horizontal",
                               padding=[dp(12), dp(5)], spacing=dp(8),
                               size_hint_y=None, height=dp(62))
            day_label = self.make_label(day, 12, WHITE, "left")
            day_label.size_hint_x = 0.95
            row.add_widget(day_label)
            ico = self.make_label(f_icon, 23, WHITE, "center")
            ico.size_hint_x = 0.55
            row.add_widget(ico)
            desc = self.make_label(f_desc, 11, MUTED, "left")
            desc.size_hint_x = 1.25
            row.add_widget(desc)
            temp = self.make_label(
                f"{round(daily['temperature_2m_max'][i])}° / {round(daily['temperature_2m_min'][i])}°",
                12, WHITE, "right"
            )
            temp.size_hint_x = 0.9
            row.add_widget(temp)
            self.forecast.add_widget(row)

        stamp = current.get("time", "")
        self.status.color = GREEN
        self.status.text = f"●  Updated {stamp}  •  Open-Meteo"

    def toggle_favourite(self):
        if not self.last_place:
            self.status.text = "Search for a city before saving it."
            return
        city = self.last_place.get("name", "")
        if city in self.favourites:
            self.favourites.remove(city)
        else:
            self.favourites.append(city)
        self.fav_status.text = "Saved: " + ", ".join(self.favourites[-3:]) if self.favourites else "No saved cities"

if __name__ == "__main__":
    WeatherApp().run()
