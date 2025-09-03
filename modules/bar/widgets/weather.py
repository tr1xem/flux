# Define Weather widget inline to avoid import issues
import json
import threading
import time
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple

from ignis import utils, widgets

# Configuration constants for weather
CACHE_DURATION = 10 * 60  # 10 minutes
STALE_CACHE_MAX = 30 * 60  # 30 minutes
UPDATE_INTERVAL = 5 * 60  # 5 minutes in seconds

# Directory setup
TEMP_DIR = Path.home() / ".cache" / "ignis"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = TEMP_DIR / "weather_cache.json"
LOCATION_CACHE_FILE = TEMP_DIR / "location_cache.json"

# APIs - all free, no key required
IP_LOCATION_API = "http://ip-api.com/json/"
WEATHER_API_BASE = "https://api.open-meteo.com/v1/forecast"

# Weather icons mapping (WMO weather codes to emoji icons)
WEATHER_ICONS: Dict[int, str] = {
    0: "☀️",  # Clear sky
    1: "🌤️",  # Mainly clear
    2: "⛅",  # Partly cloudy
    3: "☁️",  # Overcast
    45: "🌫️",  # Fog
    48: "🌫️",  # Depositing rime fog
    51: "🌦️",  # Drizzle: Light
    53: "🌦️",  # Drizzle: Moderate
    55: "🌧️",  # Drizzle: Dense
    56: "🌨️",  # Freezing Drizzle: Light
    57: "🌨️",  # Freezing Drizzle: Dense
    61: "🌧️",  # Rain: Slight
    63: "🌧️",  # Rain: Moderate
    65: "🌧️",  # Rain: Heavy
    66: "🌨️",  # Freezing Rain: Light
    67: "🌨️",  # Freezing Rain: Heavy
    71: "❄️",  # Snow fall: Slight
    73: "❄️",  # Snow fall: Moderate
    75: "❄️",  # Snow fall: Heavy
    77: "❄️",  # Snow grains
    80: "🌦️",  # Rain showers: Slight
    81: "🌧️",  # Rain showers: Moderate
    82: "⛈️",  # Rain showers: Violent
    85: "🌨️",  # Snow showers: Slight
    86: "🌨️",  # Snow showers: Heavy
    95: "⛈️",  # Thunderstorm: Slight or moderate
    96: "⛈️",  # Thunderstorm with slight hail
    99: "⛈️",  # Thunderstorm with heavy hail
}


def get_weather_description(code: int) -> str:
    """Get weather description from WMO code"""
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, "Unknown")


def format_weather(data: dict) -> Optional[str]:
    """Format Open-Meteo data into display text"""
    try:
        current = data["current"]
        temp = current["temperature_2m"]
        weather_code = current["weather_code"]
        icon = WEATHER_ICONS.get(weather_code, "🌡")
        return f"{icon} {temp:.1f}°C"
    except Exception:
        return None


def create_tooltip(weather_data: dict, location_data: dict) -> str:
    """Create detailed tooltip from weather data"""
    try:
        current = weather_data["current"]
        hourly = weather_data["hourly"]

        # Current weather
        temp = round(current["temperature_2m"])
        feels_like = round(current["apparent_temperature"])
        humidity = round(current["relative_humidity_2m"])
        wind_speed = round(current["wind_speed_10m"])
        weather_code = current["weather_code"]
        description = get_weather_description(weather_code)

        # Location info
        city = location_data.get("city", "Unknown")
        country = location_data.get("country", "")
        location_str = f"{city}, {country}" if country else city

        tooltip = f"<b>{location_str}</b>\n"
        tooltip += f"<b>{description}</b>\n"
        tooltip += f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
        tooltip += f"Humidity: {humidity}%\n"
        tooltip += f"Wind: {wind_speed} km/h\n"

        # Add next few hours forecast
        tooltip += "\n<b>Next 12 hours:</b>\n"
        for i in range(1, 5):  # Next 4 hours
            if i < len(hourly["time"]):
                hour_temp = round(hourly["temperature_2m"][i])
                hour_code = hourly["weather_code"][i]
                hour_icon = WEATHER_ICONS.get(hour_code, "🌡")
                hour_desc = get_weather_description(hour_code)
                # Extract hour from time string
                time_str = hourly["time"][i]
                hour = time_str.split("T")[1][:2]
                tooltip += f"{hour}:00: {hour_icon} {hour_temp}°C - {hour_desc}\n"

        return tooltip.strip()
    except Exception:
        return "Weather information"


class LocationCache:
    """Cache for location data"""

    def __init__(self):
        self._location_data: Optional[dict] = None
        self._location_time: float = 0
        self._cache_file = LOCATION_CACHE_FILE
        self._lock = threading.Lock()
        self._load_cache()

    def _load_cache(self):
        try:
            if self._cache_file.exists():
                stat = self._cache_file.stat()
                with self._lock:
                    self._location_time = stat.st_mtime
                    self._location_data = json.loads(self._cache_file.read_text())
        except Exception:
            pass

    def is_fresh(self) -> bool:
        # Location cache valid for 24 hours
        with self._lock:
            return (
                self._location_data is not None
                and time.time() - self._location_time < 24 * 60 * 60
            )

    def get_location(self) -> Optional[dict]:
        if self.is_fresh():
            with self._lock:
                return self._location_data.copy() if self._location_data else None
        return None

    def set_location(self, data: dict):
        try:
            tmp = self._cache_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, separators=(",", ":")))
            tmp.rename(self._cache_file)
            with self._lock:
                self._location_data = data
                self._location_time = time.time()
        except Exception:
            pass


class WeatherCache:
    """Thread-safe weather data caching system"""

    def __init__(self):
        self._memory_cache: Optional[dict] = None
        self._memory_time: float = 0
        self._cache_file = CACHE_FILE
        self._lock = threading.Lock()
        self._load_file_cache()

    def _load_file_cache(self):
        try:
            if self._cache_file.exists():
                stat = self._cache_file.stat()
                with self._lock:
                    self._memory_time = stat.st_mtime
                    self._memory_cache = json.loads(self._cache_file.read_text())
        except Exception:
            pass

    def is_fresh(self) -> bool:
        with self._lock:
            return (
                self._memory_cache is not None
                and time.time() - self._memory_time < CACHE_DURATION
            )

    def is_usable(self) -> bool:
        with self._lock:
            return (
                self._memory_cache is not None
                and time.time() - self._memory_time < STALE_CACHE_MAX
            )

    def get_cache(self, network=True) -> Optional[dict]:
        if self.is_fresh():
            with self._lock:
                return self._memory_cache.copy() if self._memory_cache else None
        if not network and self.is_usable():
            with self._lock:
                return self._memory_cache.copy() if self._memory_cache else None
        return None

    def set_cache(self, data: dict):
        try:
            tmp = self._cache_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, separators=(",", ":")))
            tmp.rename(self._cache_file)
            with self._lock:
                self._memory_cache = data
                self._memory_time = time.time()
        except Exception:
            pass


def fetch_location() -> Optional[dict]:
    """Fetch location from IP using free API"""
    try:
        req = urllib.request.Request(IP_LOCATION_API)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get("status") == "success":
                    return {
                        "lat": data["lat"],
                        "lon": data["lon"],
                        "city": data.get("city", "Unknown"),
                        "country": data.get("country", ""),
                        "timezone": data.get("timezone", ""),
                    }
        return None
    except Exception:
        return None


def fetch_weather(lat: float, lon: float) -> Optional[dict]:
    """Fetch weather from Open-Meteo API"""
    try:
        # Build URL with parameters
        params = [
            f"latitude={lat}",
            f"longitude={lon}",
            "current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "hourly=temperature_2m,weather_code",
            "timezone=auto",
            "forecast_days=1",
        ]
        url = f"{WEATHER_API_BASE}?{'&'.join(params)}"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
        return None
    except Exception:
        return None


class Weather(widgets.Box):
    def __init__(self):
        super().__init__(css_classes=["weather"])

        # Start with a simple working widget first
        self._label = widgets.Label(css_classes=["weather-label"], label="🌡️ Loading...")

        self._event_box = widgets.EventBox(
            child=[self._label],
            tooltip_text="Loading weather data...",
            css_classes=["weather-container"],
        )

        self.append(self._event_box)

        # Initialize caches
        self._weather_cache = WeatherCache()
        self._location_cache = LocationCache()

        # Try to fetch weather data immediately on startup
        utils.ThreadTask(self._fetch_weather_data, self._update_display).run()

        # Set up periodic updates using Poll
        self._poll = utils.Poll(
            UPDATE_INTERVAL * 1000, lambda _: self._periodic_update()
        )

    def _fetch_weather_data(self) -> Tuple[str, str]:
        """Fetch weather data - returns (weather_text, tooltip_text)"""
        try:
            # Check cached location first
            location_data = self._location_cache.get_location()

            if not location_data:
                # Try to fetch location
                try:
                    req = urllib.request.Request(
                        IP_LOCATION_API, headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status == 200:
                            data = json.loads(response.read().decode())
                            if data.get("status") == "success":
                                location_data = {
                                    "lat": data["lat"],
                                    "lon": data["lon"],
                                    "city": data.get("city", "Unknown"),
                                    "country": data.get("country", ""),
                                }
                                self._location_cache.set_location(location_data)
                except Exception as e:
                    return (
                        "🌡️ No Location",
                        f"<span weight='bold'>Location error:</span> {str(e)}",
                    )

            if not location_data:
                return (
                    "🌡️ No Location",
                    "<span weight='bold'>Unable to detect location</span>",
                )

            # Check cached weather
            weather_data = self._weather_cache.get_cache()

            if not weather_data:
                # Fetch comprehensive weather data
                try:
                    lat, lon = location_data["lat"], location_data["lon"]
                    # Request extensive weather parameters
                    params = [
                        f"latitude={lat}",
                        f"longitude={lon}",
                        "current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                        "hourly=temperature_2m,weather_code,precipitation_probability,wind_speed_10m",
                        "daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                        "timezone=auto",
                        "forecast_days=3",
                    ]
                    url = f"{WEATHER_API_BASE}?{'&'.join(params)}"

                    req = urllib.request.Request(
                        url, headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(req, timeout=15) as response:
                        if response.status == 200:
                            weather_data = json.loads(response.read().decode())
                            self._weather_cache.set_cache(weather_data)
                        else:
                            return (
                                f"🌡️ {location_data['city']}",
                                f"<span weight='bold'>Weather API error:</span> {response.status}",
                            )
                except Exception as e:
                    # Try to use stale cache
                    weather_data = self._weather_cache.get_cache(network=False)
                    if not weather_data:
                        return (
                            f"🌡️ {location_data['city']}",
                            f"<span weight='bold'>Weather fetch error:</span> {str(e)}",
                        )

            # Format the weather data
            if weather_data and "current" in weather_data:
                try:
                    current = weather_data["current"]
                    temp = current["temperature_2m"]  # Keep as float for .1f formatting
                    weather_code = current["weather_code"]
                    icon = WEATHER_ICONS.get(weather_code, "🌡")

                    text = f"{icon} {temp:.1f}°C"

                    # Create extensive colorful tooltip
                    tooltip = self._create_rich_tooltip(weather_data, location_data)

                    return text, tooltip
                except Exception as e:
                    return (
                        f"🌡️ {location_data['city']}",
                        f"<span weight='bold'>Data parsing error:</span> {str(e)}",
                    )
            else:
                return (
                    f"🌡️ {location_data['city']}",
                    "<span style='italic'>No weather data available</span>",
                )

        except Exception as e:
            return "🌡️ Error", f"<span weight='bold'>Unexpected error:</span> {str(e)}"

    def _create_rich_tooltip(self, weather_data: dict, location_data: dict) -> str:
        """Create a rich tooltip with bold and italic styling (no colors)"""
        try:
            current = weather_data["current"]
            hourly = weather_data.get("hourly", {})
            daily = weather_data.get("daily", {})

            # Current weather data
            temp = current["temperature_2m"]  # Keep as float
            feels_like = current.get("apparent_temperature", temp)  # Keep as float
            humidity = round(current["relative_humidity_2m"])
            pressure = round(
                current.get("surface_pressure", 1013)
            )  # Default atmospheric pressure
            wind_speed = current.get("wind_speed_10m", 0)  # Keep as float
            wind_direction = current.get("wind_direction_10m", 0)
            wind_gusts = current.get("wind_gusts_10m", 0)  # Keep as float
            precipitation = current.get("precipitation", 0)
            weather_code = current["weather_code"]
            description = get_weather_description(weather_code)
            icon = WEATHER_ICONS.get(weather_code, "🌡")

            # Location info
            city = location_data.get("city", "Unknown")
            country = location_data.get("country", "")
            location_str = f"{city}, {country}" if country else city

            # Wind direction
            wind_dirs = [
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
            wind_dir = wind_dirs[round(wind_direction / 22.5) % 16]

            # Build tooltip with bold and italic styling
            tooltip = f"<span size='large' weight='bold'>📍 {location_str}</span>\n"
            tooltip += f"<span size='large' weight='bold'>{icon} {description}</span>\n"

            # Current conditions section
            tooltip += (
                "\n<span weight='bold' underline='single'>Current Conditions</span>\n\n"
            )

            # Temperature row with emphasis based on temperature
            temp_style = (
                "weight='bold'"
                if temp > 30 or temp < 0
                else "style='italic'"
                if temp > 25 or temp < 5
                else ""
            )
            feels_style = (
                "weight='bold'"
                if feels_like > 30 or feels_like < 0
                else "style='italic'"
                if feels_like > 25 or feels_like < 5
                else ""
            )
            tooltip += f"<span {temp_style}>🌡️ {temp:.1f}°C</span>  <span {feels_style}>feels {feels_like:.1f}°C</span>\n"

            # Environment row
            humidity_style = (
                "style='italic'"
                if 40 <= humidity <= 60
                else "weight='bold'"
                if humidity > 80 or humidity < 20
                else ""
            )
            tooltip += f"<span {humidity_style}>💧 {humidity}%</span>  <span weight='bold'>📊 {pressure}hPa</span>\n"

            # Wind row with emphasis based on speed
            wind_style = (
                "weight='bold'"
                if wind_speed > 20
                else "style='italic'"
                if wind_speed > 10
                else ""
            )
            wind_text = f"<span {wind_style}>💨 {wind_speed:.1f}km/h {wind_dir}</span>"
            if wind_gusts > wind_speed:
                wind_text += f"  <span weight='bold'>gusts {wind_gusts:.1f}km/h</span>"
            tooltip += wind_text + "\n"

            # Precipitation row (only if present)
            if precipitation > 0:
                tooltip += f"<span weight='bold'>🌧️ {precipitation:.1f}mm precipitation</span>\n"

            # Hourly forecast section
            if hourly and "time" in hourly and len(hourly["time"]) > 1:
                tooltip += (
                    "\n<span weight='bold' underline='single'>Next 6 Hours</span>\n\n"
                )

                # Find current hour index by comparing with current time
                import datetime

                current_hour = datetime.datetime.now().hour
                start_index = current_hour  # Start from current hour

                for i in range(start_index, min(start_index + 6, len(hourly["time"]))):
                    try:
                        hour_temp = hourly["temperature_2m"][i]  # Keep as float
                        hour_code = hourly["weather_code"][i]
                        hour_icon = WEATHER_ICONS.get(hour_code, "🌡")
                        hour_precipitation = hourly.get(
                            "precipitation_probability", [0] * len(hourly["time"])
                        )[i]
                        hour_wind = hourly.get(
                            "wind_speed_10m", [0] * len(hourly["time"])
                        )[i]

                        # Extract hour from ISO time and convert to 12-hour format
                        time_str = hourly["time"][i]
                        if "T" in time_str:
                            # Parse the full datetime string like "2025-09-03T18:00"
                            time_part = time_str.split("T")[1]
                            hour_24 = int(time_part[:2])
                            if hour_24 == 0:
                                hour = "12:00AM"
                            elif hour_24 < 12:
                                hour = f"{hour_24:02d}:00AM"
                            elif hour_24 == 12:
                                hour = "12:00PM"
                            else:
                                hour = f"{hour_24 - 12:02d}:00PM"
                        else:
                            hour = f"{i:02d}:00"

                        # Build hourly line (without weather icon and temperature styling)
                        line = f"<span font_family='monospace'font_weight='bold' >{hour}</span>   {hour_temp:.1f}°C"

                        # Add additional info if significant
                        extras = []
                        if hour_precipitation > 20:
                            extras.append(
                                f"<span weight='bold'>💧{hour_precipitation}%</span>"
                            )
                        if hour_wind > 15:
                            extras.append(
                                f"<span weight='bold'>💨{hour_wind:.1f}</span>"
                            )

                        if extras:
                            line += "  " + "  ".join(extras)

                        tooltip += line + "\n"
                    except (IndexError, KeyError):
                        continue

            # Daily forecast section
            if daily and "time" in daily and len(daily["time"]) > 1:
                tooltip += (
                    "\n<span weight='bold' underline='single'>3-Day Forecast</span>\n\n"
                )
                days = ["Today", "Tomorrow", "Day 3"]
                for i in range(min(3, len(daily["time"]))):
                    try:
                        max_temp = daily["temperature_2m_max"][i]  # Keep as float
                        min_temp = daily["temperature_2m_min"][i]  # Keep as float
                        day_code = daily["weather_code"][i]
                        day_icon = WEATHER_ICONS.get(day_code, "🌡")
                        day_precipitation = daily.get(
                            "precipitation_sum", [0] * len(daily["time"])
                        )[i]
                        day_wind = daily.get(
                            "wind_speed_10m_max", [0] * len(daily["time"])
                        )[i]

                        max_style = (
                            "weight='bold'"
                            if max_temp > 25 or max_temp < 5
                            else "style='italic'"
                            if max_temp > 20 or max_temp < 10
                            else ""
                        )
                        min_style = "style='italic'" if min_temp < 10 else ""

                        # Build daily line with equal spacing
                        line = f"<span font_family='monospace' font_weight='bold'>{days[i]:<8}</span>  <span {max_style}>{day_icon} {max_temp:.1f}°C</span>/<span {min_style}>{min_temp:.1f}°C</span>"

                        # Add weather details if significant
                        extras = []
                        if day_precipitation > 1:
                            extras.append(
                                f"<span weight='bold'>🌧️{day_precipitation:.1f}mm</span>"
                            )
                        if day_wind > 20:
                            extras.append(
                                f"<span weight='bold'>💨{day_wind:.1f}km/h</span>"
                            )

                        if extras:
                            line += "  " + "  ".join(extras)

                        tooltip += line + "\n"
                    except (IndexError, KeyError):
                        continue

            # Data source footer
            tooltip += "\n<span size='small' style='italic'>📡 Open-Meteo API</span>"

            return tooltip.strip()

        except Exception as e:
            return f"<span weight='bold'>Tooltip error: {str(e)}</span>"

    def _periodic_update(self) -> str:
        """Periodic update function for Poll"""
        utils.ThreadTask(self._fetch_weather_data, self._update_display).run()
        return "Updated"

    def _update_display(self, result: Tuple[str, str]) -> None:
        """Update weather display on main thread"""
        text, tooltip_text = result

        # Update label text
        self._label.label = text

        # Set tooltip
        if tooltip_text:
            self._event_box.tooltip_markup = tooltip_text
        else:
            self._event_box.tooltip_text = text
