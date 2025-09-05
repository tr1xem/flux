import json
import threading
import time
import urllib.request
import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
from ignis import utils, widgets


CACHE_DURATION, STALE_CACHE_MAX, UPDATE_INTERVAL = 600, 1800, 300
TEMP_DIR = Path.home() / ".cache" / "ignis"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


IP_LOCATION_API = "http://ip-api.com/json/"
WEATHER_API_BASE = "https://api.open-meteo.com/v1/forecast"


WEATHER_DATA: Dict[int, Tuple[str, str, str]] = {
    0: ("☀️", "weather-clear-symbolic", "Clear sky"),
    1: ("🌤️", "weather-few-clouds-symbolic", "Mainly clear"),
    2: ("⛅", "weather-few-clouds-symbolic", "Partly cloudy"),
    3: ("☁️", "weather-overcast-symbolic", "Overcast"),
    45: ("🌫️", "weather-fog-symbolic", "Fog"),
    48: ("🌫️", "weather-fog-symbolic", "Depositing rime fog"),
    51: ("🌦️", "weather-showers-symbolic", "Light drizzle"),
    53: ("🌦️", "weather-showers-symbolic", "Moderate drizzle"),
    55: ("🌧️", "weather-showers-symbolic", "Dense drizzle"),
    56: ("🌨️", "weather-showers-symbolic", "Light freezing drizzle"),
    57: ("🌨️", "weather-showers-symbolic", "Dense freezing drizzle"),
    61: ("🌦️", "weather-showers-symbolic", "Slight rain"),
    63: ("🌧️", "weather-showers-symbolic", "Moderate rain"),
    65: ("🌧️", "weather-showers-symbolic", "Heavy rain"),
    66: ("🌨️", "weather-showers-symbolic", "Light freezing rain"),
    67: ("🌨️", "weather-showers-symbolic", "Heavy freezing rain"),
    71: ("❄️", "weather-snow-symbolic", "Slight snow"),
    73: ("🌨️", "weather-snow-symbolic", "Moderate snow"),
    75: ("❄️", "weather-snow-symbolic", "Heavy snow"),
    77: ("❄️", "weather-snow-symbolic", "Snow grains"),
    80: ("🌦️", "weather-showers-symbolic", "Slight rain showers"),
    81: ("🌧️", "weather-showers-symbolic", "Moderate rain showers"),
    82: ("⛈️", "weather-storm-symbolic", "Violent rain showers"),
    85: ("🌨️", "weather-snow-symbolic", "Slight snow showers"),
    86: ("❄️", "weather-snow-symbolic", "Heavy snow showers"),
    95: ("⛈️", "weather-storm-symbolic", "Thunderstorm"),
    96: ("⛈️", "weather-storm-symbolic", "Thunderstorm with hail"),
    99: ("⛈️", "weather-storm-symbolic", "Thunderstorm with heavy hail"),
}


def get_weather_info(code: int) -> Tuple[str, str, str]:
    """Get emoji, icon, description for weather code"""
    return WEATHER_DATA.get(code, ("🌡️", "weather-clear-symbolic", "Unknown"))


class Cache:
    """Generic cache with file persistence and thread safety"""

    def __init__(self, cache_file: Path, max_age: int):
        self._cache_file, self._max_age = cache_file, max_age
        self._data, self._time, self._lock = None, 0, threading.Lock()
        self._load_cache()

    def _load_cache(self):
        try:
            if self._cache_file.exists():
                with self._lock:
                    self._time = self._cache_file.stat().st_mtime
                    self._data = json.loads(self._cache_file.read_text())
        except Exception:
            pass

    def is_fresh(self) -> bool:
        with self._lock:
            return bool(self._data and time.time() - self._time < CACHE_DURATION)

    def is_usable(self) -> bool:
        with self._lock:
            return bool(self._data and time.time() - self._time < self._max_age)

    def get(self, allow_stale=False) -> Optional[dict]:
        if self.is_fresh() or (allow_stale and self.is_usable()):
            with self._lock:
                return self._data.copy() if self._data else None
        return None

    def set(self, data: dict):
        try:
            tmp = self._cache_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, separators=(",", ":")))
            tmp.rename(self._cache_file)
            with self._lock:
                self._data, self._time = data, time.time()
        except Exception:
            pass


def fetch_api(url: str, timeout: int = 10) -> Optional[dict]:
    """Generic API fetcher with error handling"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return (
                json.loads(response.read().decode()) if response.status == 200 else None
            )
    except Exception:
        return None


def format_time(time_str: str) -> str:
    """Convert ISO time to 12-hour format"""
    if "T" not in time_str:
        return time_str
    hour_24 = int(time_str.split("T")[1][:2])
    if hour_24 == 0:
        return "12:00AM"
    elif hour_24 < 12:
        return f"{hour_24:02d}:00AM"
    elif hour_24 == 12:
        return "12:00PM"
    else:
        return f"{hour_24 - 12:02d}:00PM"


def get_wind_direction(degrees: float) -> str:
    """Convert wind degrees to direction"""
    dirs = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    return dirs[round(degrees / 22.5) % 16]


def style_temp(temp: float) -> str:
    """Get markup style for temperature"""
    if temp > 30 or temp < 0:
        return "weight='bold'"
    elif temp > 25 or temp < 5:
        return "style='italic'"
    return ""


def create_tooltip(weather_data: dict, location_data: dict) -> str:
    """Create rich tooltip from weather data"""
    try:
        current = weather_data["current"]
        hourly = weather_data.get("hourly", {})
        daily = weather_data.get("daily", {})

        temp, feels = (
            current["temperature_2m"],
            current.get("apparent_temperature", current["temperature_2m"]),
        )
        humidity = round(current["relative_humidity_2m"])
        pressure = round(current.get("surface_pressure", 1013))
        wind_speed = current.get("wind_speed_10m", 0)
        wind_dir = get_wind_direction(current.get("wind_direction_10m", 0))
        precipitation = current.get("precipitation", 0)

        emoji, _, description = get_weather_info(current["weather_code"])
        city = location_data.get("city", "Unknown")
        country = location_data.get("country", "")
        location = f"{city}, {country}" if country else city

        tooltip = f"<span size='large' weight='bold'>📍 {location}</span>\n"
        tooltip += f"<span size='large' weight='bold'>{emoji} {description}</span>\n"
        tooltip += (
            "\n<span weight='bold' underline='single'>Current Conditions</span>\n\n"
        )

        temp_style, feels_style = style_temp(temp), style_temp(feels)
        tooltip += f"<span {temp_style}>🌡️ {temp:.1f}°C</span>  <span {feels_style}>feels {feels:.1f}°C</span>\n"

        humidity_style = (
            "style='italic'"
            if 40 <= humidity <= 60
            else "weight='bold'"
            if humidity > 80 or humidity < 20
            else ""
        )
        tooltip += f"<span {humidity_style}>💧 {humidity}%</span>  <span weight='bold'>📊 {pressure}hPa</span>\n"

        wind_style = (
            "weight='bold'"
            if wind_speed > 20
            else "style='italic'"
            if wind_speed > 10
            else ""
        )
        tooltip += f"<span {wind_style}>💨 {wind_speed:.1f}km/h {wind_dir}</span>\n"

        if precipitation > 0:
            tooltip += f"<span weight='bold'>🌧️ {precipitation:.1f}mm</span>\n"

        if hourly and len(hourly.get("time", [])) > 1:
            tooltip += (
                "\n<span weight='bold' underline='single'>Next 6 Hours</span>\n\n"
            )
            current_hour = datetime.datetime.now().hour
            for i in range(current_hour, min(current_hour + 6, len(hourly["time"]))):
                try:
                    hour_temp = hourly["temperature_2m"][i]
                    hour_time = format_time(hourly["time"][i])
                    tooltip += f"<span font_family='monospace' font_weight='bold'>{hour_time}</span>   {hour_temp:.1f}°C\n"
                except (IndexError, KeyError):
                    continue

        if daily and len(daily.get("time", [])) > 1:
            tooltip += (
                "\n<span weight='bold' underline='single'>3-Day Forecast</span>\n\n"
            )
            days = ["Today", "Tomorrow", "Day 3"]
            for i in range(min(3, len(daily["time"]))):
                try:
                    max_temp, min_temp = (
                        daily["temperature_2m_max"][i],
                        daily["temperature_2m_min"][i],
                    )
                    emoji, _, _ = get_weather_info(daily["weather_code"][i])
                    max_style, min_style = style_temp(max_temp), style_temp(min_temp)
                    tooltip += f"<span font_family='monospace' font_weight='bold'>{days[i]:<8}</span>  <span {max_style}>{emoji} {max_temp:.1f}°C</span>/<span {min_style}>{min_temp:.1f}°C</span>\n"
                except (IndexError, KeyError):
                    continue

        tooltip += "\n<span size='small' style='italic'>📡 Open-Meteo API</span>"
        return tooltip.strip()

    except Exception as e:
        return f"<span weight='bold'>Tooltip error: {str(e)}</span>"


class Weather(widgets.Box):
    def __init__(self):
        super().__init__(css_classes=["weather"])

        self._icon = widgets.Icon(
            image="weather-clear-symbolic", pixel_size=16, css_classes=["weather-icon"]
        )
        self._label = widgets.Label(css_classes=["weather-label"], label="Loading...")
        self._event_box = widgets.EventBox(
            child=[self._icon, self._label],
            spacing=8,
            tooltip_text="Loading weather data...",
            css_classes=["weather-container"],
        )
        self.append(self._event_box)

        self._weather_cache = Cache(TEMP_DIR / "weather_cache.json", STALE_CACHE_MAX)
        self._location_cache = Cache(TEMP_DIR / "location_cache.json", 24 * 3600)

        utils.ThreadTask(self._fetch_weather_data, self._update_display).run()
        self._poll = utils.Poll(
            UPDATE_INTERVAL * 1000, lambda _: self._periodic_update()
        )

    def _fetch_weather_data(self) -> Tuple[str, str, str]:
        """Fetch weather data - returns (text, icon_name, tooltip_text)"""

        def error_result(msg: str) -> Tuple[str, str, str]:
            return (
                "Error",
                "weather-clear-symbolic",
                f"<span weight='bold'>{msg}</span>",
            )

        location_data = self._location_cache.get()
        if not location_data:
            location_data = fetch_api(IP_LOCATION_API, 10)
            if not location_data or location_data.get("status") != "success":
                return error_result("Location unavailable")
            location_data = {
                "lat": location_data["lat"],
                "lon": location_data["lon"],
                "city": location_data.get("city", "Unknown"),
                "country": location_data.get("country", ""),
            }
            self._location_cache.set(location_data)

        weather_data = self._weather_cache.get()
        if not weather_data:
            lat, lon = location_data["lat"], location_data["lon"]
            params = [
                f"latitude={lat}",
                f"longitude={lon}",
                "current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m",
                "hourly=temperature_2m,weather_code",
                "daily=weather_code,temperature_2m_max,temperature_2m_min",
                "timezone=auto",
                "forecast_days=3",
            ]
            weather_data = fetch_api(f"{WEATHER_API_BASE}?{'&'.join(params)}", 15)
            if not weather_data:
                weather_data = self._weather_cache.get(allow_stale=True)
                if not weather_data:
                    return error_result("Weather unavailable")
            else:
                self._weather_cache.set(weather_data)

        try:
            current = weather_data["current"]
            temp = current["temperature_2m"]
            _, icon_name, _ = get_weather_info(current["weather_code"])
            tooltip = create_tooltip(weather_data, location_data)
            return f"{temp:.1f}°C", icon_name, tooltip
        except Exception as e:
            return error_result(f"Data error: {str(e)}")

    def _periodic_update(self) -> str:
        utils.ThreadTask(self._fetch_weather_data, self._update_display).run()
        return "Updated"

    def _update_display(self, result: Tuple[str, str, str]) -> None:
        text, icon_name, tooltip_text = result
        self._label.label = text
        self._icon.set_image(icon_name)
        self._event_box.tooltip_markup = tooltip_text

