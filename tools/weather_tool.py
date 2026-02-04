"""
Weather Tool - Get current weather data using Open-Meteo API with caching
"""
import os
import httpx
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_tool import BaseTool

# Import cache utilities
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cache import cached


class WeatherTool(BaseTool):
    """Tool for fetching weather data using Open-Meteo API with caching"""
    
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    CACHE_TTL = int(os.getenv("CACHE_TTL_WEATHER", 300))  # 5 minutes default
    
    # Weather code descriptions
    WEATHER_CODES = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
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
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @property
    def name(self) -> str:
        return "weather"
    
    @property
    def description(self) -> str:
        return "Get current weather information for any city. Returns temperature, humidity, wind speed, and weather conditions."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "city": {
                "type": "string",
                "description": "City name to get weather for (e.g., 'London', 'New York', 'Tokyo')",
                "required": True
            },
            "units": {
                "type": "string",
                "description": "Temperature units: 'celsius' or 'fahrenheit'",
                "required": False,
                "default": "celsius"
            }
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    @cached(prefix="weather", ttl_seconds=300)
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get weather for specified city with caching"""
        city = kwargs.get("city")
        if not city:
            return {"error": "City parameter is required"}
        
        units = kwargs.get("units", "celsius")
        
        try:
            # First, geocode the city
            location = await self._geocode_city(city)
            if "error" in location:
                return location
            
            # Then get weather data
            weather = await self._get_weather(
                location["latitude"],
                location["longitude"],
                units
            )
            
            weather["location"] = {
                "city": location["name"],
                "country": location["country"],
                "latitude": location["latitude"],
                "longitude": location["longitude"]
            }
            
            weather["cached"] = False  # Will be True when retrieved from cache
            
            return weather
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _geocode_city(self, city: str) -> Dict[str, Any]:
        """Convert city name to coordinates"""
        response = await self.client.get(
            self.GEOCODING_URL,
            params={"name": city, "count": 1}
        )
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return {"error": f"City '{city}' not found"}
        
        location = results[0]
        return {
            "name": location["name"],
            "country": location.get("country", "Unknown"),
            "latitude": location["latitude"],
            "longitude": location["longitude"]
        }
    
    async def _get_weather(self, lat: float, lon: float, units: str) -> Dict[str, Any]:
        """Get current weather for coordinates"""
        temp_unit = "fahrenheit" if units == "fahrenheit" else "celsius"
        
        response = await self.client.get(
            self.WEATHER_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature",
                "temperature_unit": temp_unit,
                "wind_speed_unit": "kmh"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        weather_code = current.get("weather_code", 0)
        
        return {
            "success": True,
            "weather": {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "condition": self.WEATHER_CODES.get(weather_code, "Unknown"),
                "units": {
                    "temperature": "°F" if units == "fahrenheit" else "°C",
                    "wind_speed": "km/h"
                }
            }
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
