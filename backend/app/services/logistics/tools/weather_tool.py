"""
Weather and disaster tools — fetch live weather data and flood warnings
from Open-Meteo APIs (free, no API key required).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.logistics.tools.registry import tool_registry

logger = logging.getLogger(__name__)

# Hardcoded city lookup for Indian cities (name -> (latitude, longitude))
_CITY_COORDS: dict[str, tuple[float, float]] = {
    "odisha": (20.27, 85.84),
    "bhubaneswar": (20.27, 85.84),
    "puri": (19.81, 85.83),
    "cuttack": (20.46, 85.88),
    "chennai": (13.08, 80.27),
    "vellore": (12.92, 79.13),
    "gujarat": (23.02, 72.57),
    "ahmedabad": (23.02, 72.57),
    "bhuj": (23.25, 69.67),
    "rajkot": (22.30, 70.80),
    "rajasthan": (26.91, 75.79),
    "jaipur": (26.91, 75.79),
    "barmer": (25.75, 71.38),
    "jaisalmer": (26.92, 70.91),
    "kerala": (10.85, 76.27),
    "kochi": (9.97, 76.27),
    "bihar": (25.61, 85.14),
    "patna": (25.61, 85.14),
    "assam": (26.14, 91.74),
    "guwahati": (26.14, 91.74),
    "mumbai": (19.08, 72.88),
    "uttarakhand": (30.32, 78.03),
    "dehradun": (30.32, 78.03),
    "kedarnath": (30.73, 79.07),
    "rishikesh": (30.09, 78.27),
    "joshimath": (30.56, 79.56),
    "delhi": (28.61, 77.21),
    "kolkata": (22.57, 88.36),
    "hyderabad": (17.39, 78.49),
    "bangalore": (12.97, 77.59),
    "pune": (18.52, 73.86),
    "lucknow": (26.85, 80.95),
    "surat": (21.17, 72.83),
    "visakhapatnam": (17.69, 83.22),
    "vizag": (17.69, 83.22),
    "srinagar": (34.08, 74.80),
    "leh": (34.16, 77.58),
    "andaman": (11.62, 92.73),
    "port blair": (11.64, 92.73),
    "tamil nadu": (11.13, 78.66),
    "andhra pradesh": (15.91, 79.74),
    "karnataka": (15.32, 75.71),
    "maharashtra": (19.75, 75.71),
    "west bengal": (22.99, 87.85),
    # Additional disaster-prone regions
    "nagpur": (21.15, 79.09),
    "indore": (22.72, 75.86),
    "bhopal": (23.26, 77.41),
    "raipur": (21.25, 81.63),
    "ranchi": (23.34, 85.31),
    "thiruvananthapuram": (8.52, 76.94),
    "coimbatore": (11.00, 76.96),
    "madurai": (9.92, 78.12),
    "mangalore": (12.87, 74.84),
    "vadodara": (22.31, 73.19),
    "agra": (27.18, 78.02),
    "varanasi": (25.32, 83.01),
    "kanpur": (26.45, 80.35),
    "chandigarh": (30.73, 76.77),
    "shimla": (31.10, 77.17),
    "imphal": (24.82, 93.95),
    "aizawl": (23.73, 92.72),
    "kohima": (25.67, 94.11),
    "gangtok": (27.33, 88.62),
    "silchar": (24.83, 92.78),
    "dibrugarh": (27.47, 94.91),
    "jorhat": (26.76, 94.20),
    "tezpur": (26.63, 92.80),
    "shillong": (25.57, 91.88),
    "jammu": (32.73, 74.87),
    "rourkela": (22.26, 84.85),
    "sambalpur": (21.47, 83.97),
    "berhampur": (19.31, 84.79),
    "balasore": (21.49, 86.93),
    "paradip": (20.26, 86.61),
    "gopalpur": (19.26, 84.90),
    "konark": (19.88, 86.09),
    "dhenkanal": (20.66, 85.60),
    "koraput": (18.81, 82.71),
    "warangal": (18.00, 79.59),
    "vijayawada": (16.51, 80.65),
    "tirupati": (13.63, 79.42),
    "nellore": (14.44, 79.99),
    "kakinada": (16.94, 82.24),
    "rajahmundry": (17.00, 81.80),
    "ongole": (15.50, 80.04),
    "machilipatnam": (16.19, 81.14),
    "sikkim": (27.53, 88.51),
    "meghalaya": (25.47, 91.37),
    "mizoram": (23.16, 92.94),
    "manipur": (24.66, 93.91),
    "nagaland": (26.16, 94.56),
    "arunachal pradesh": (28.22, 94.73),
    "tripura": (23.94, 91.99),
    "jharkhand": (23.61, 85.28),
    "chhattisgarh": (21.27, 81.87),
    "madhya pradesh": (22.97, 78.66),
    "punjab": (31.15, 75.34),
    "haryana": (29.06, 76.09),
    "himachal pradesh": (31.10, 77.17),
    "goa": (15.30, 74.12),
    "telangana": (18.11, 79.02),
}

# WMO weather code descriptions
_WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
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
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

_HTTP_TIMEOUT = 10.0


def _resolve_coordinates(
    latitude: float | None,
    longitude: float | None,
    location_name: str | None,
) -> tuple[float, float, str]:
    """Resolve coordinates from explicit lat/lon or city name lookup.

    Returns (latitude, longitude, resolved_name).
    Raises ValueError when coordinates cannot be determined.
    """
    if latitude is not None and longitude is not None:
        resolved_name = location_name or f"{latitude},{longitude}"
        return float(latitude), float(longitude), resolved_name

    if location_name:
        key = location_name.strip().lower()
        coords = _CITY_COORDS.get(key)
        if coords is not None:
            return coords[0], coords[1], location_name
        raise ValueError(
            f"Unknown location '{location_name}'. Provide latitude/longitude "
            f"or use a known city: {', '.join(sorted(_CITY_COORDS))}"
        )

    raise ValueError("Provide either latitude/longitude or a location_name.")


# ── live_weather tool ─────────────────────────────────────


async def live_weather(
    latitude: float | None = None,
    longitude: float | None = None,
    location_name: str | None = None,
) -> dict[str, Any]:
    """Fetch current weather data for a location from Open-Meteo."""
    try:
        lat, lon, name = _resolve_coordinates(latitude, longitude, location_name)
    except ValueError as exc:
        return {"error": str(exc)}

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast", params=params
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.warning(f"[live_weather] API request failed: {exc}")
        return _weather_fallback(name, lat, lon)

    current = data.get("current", {})
    temperature = current.get("temperature_2m")
    precipitation = current.get("precipitation", 0.0)
    wind_speed = current.get("wind_speed_10m")
    humidity = current.get("relative_humidity_2m")
    weather_code = current.get("weather_code", 0)
    description = _WMO_DESCRIPTIONS.get(weather_code, "Unknown")

    flood_risk = "high" if (precipitation or 0) > 50 else (
        "moderate" if (precipitation or 0) > 20 else "low"
    )

    return {
        "location": name,
        "latitude": lat,
        "longitude": lon,
        "temperature_celsius": temperature,
        "humidity_percent": humidity,
        "precipitation_mm": precipitation,
        "wind_speed_kmh": wind_speed,
        "weather_code": weather_code,
        "weather_description": description,
        "flood_risk": flood_risk,
        "source": "Open-Meteo",
    }


def _weather_fallback(name: str, lat: float, lon: float) -> dict[str, Any]:
    """Return sensible fallback data when the API is unreachable."""
    return {
        "location": name,
        "latitude": lat,
        "longitude": lon,
        "temperature_celsius": None,
        "humidity_percent": None,
        "precipitation_mm": None,
        "wind_speed_kmh": None,
        "weather_code": None,
        "weather_description": "Data unavailable — API unreachable",
        "flood_risk": "unknown",
        "source": "fallback",
        "warning": "Could not reach Open-Meteo API. Values are unavailable.",
    }


# ── disaster_check tool ──────────────────────────────────


async def disaster_check(
    latitude: float | None = None,
    longitude: float | None = None,
    location_name: str | None = None,
) -> dict[str, Any]:
    """Check for active flood/cyclone warnings using Open-Meteo flood API."""
    try:
        lat, lon, name = _resolve_coordinates(latitude, longitude, location_name)
    except ValueError as exc:
        return {"error": str(exc)}

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "river_discharge",
        "forecast_days": 7,
    }

    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(
                "https://flood-api.open-meteo.com/v1/flood", params=params
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.warning(f"[disaster_check] API request failed: {exc}")
        return _disaster_fallback(name, lat, lon)

    daily = data.get("daily", {})
    discharge_values = daily.get("river_discharge", [])
    dates = daily.get("time", [])

    max_discharge = max(discharge_values, default=0) if discharge_values else 0

    if max_discharge > 5000:
        alert_level = "critical"
    elif max_discharge > 2000:
        alert_level = "elevated"
    else:
        alert_level = "normal"

    forecast_entries = [
        {"date": d, "river_discharge_m3s": v}
        for d, v in zip(dates, discharge_values)
    ]

    return {
        "location": name,
        "latitude": lat,
        "longitude": lon,
        "max_river_discharge_m3s": max_discharge,
        "flood_alert_level": alert_level,
        "forecast_days": len(forecast_entries),
        "daily_forecast": forecast_entries,
        "source": "Open-Meteo Flood API",
    }


def _disaster_fallback(name: str, lat: float, lon: float) -> dict[str, Any]:
    """Return sensible fallback data when the flood API is unreachable."""
    return {
        "location": name,
        "latitude": lat,
        "longitude": lon,
        "max_river_discharge_m3s": None,
        "flood_alert_level": "unknown",
        "forecast_days": 0,
        "daily_forecast": [],
        "source": "fallback",
        "warning": "Could not reach Open-Meteo Flood API. Values are unavailable.",
    }


# ── Register tools ────────────────────────────────────────

tool_registry.register(
    name="live_weather",
    description=(
        "Fetch current weather data (temperature, precipitation, wind, humidity) "
        "for a location. Supports Indian city names or explicit lat/lon coordinates. "
        "Also estimates flood risk based on precipitation levels."
    ),
    parameters={
        "type": "object",
        "properties": {
            "latitude": {
                "type": "number",
                "description": "Latitude of the location (e.g. 20.27 for Bhubaneswar)",
            },
            "longitude": {
                "type": "number",
                "description": "Longitude of the location (e.g. 85.84 for Bhubaneswar)",
            },
            "location_name": {
                "type": "string",
                "description": (
                    "Name of an Indian city/state to look up coordinates automatically. "
                    "Supported: odisha, bhubaneswar, chennai, gujarat, ahmedabad, "
                    "rajasthan, jaipur, kerala, bihar, patna, assam, guwahati, "
                    "mumbai, uttarakhand, dehradun"
                ),
            },
        },
        "required": [],
    },
    handler=live_weather,
)

tool_registry.register(
    name="disaster_check",
    description=(
        "Check for active flood warnings by querying river discharge data from "
        "the Open-Meteo Flood API. Returns 7-day discharge forecast and an alert "
        "level (normal, elevated, critical). Supports Indian city names or lat/lon."
    ),
    parameters={
        "type": "object",
        "properties": {
            "latitude": {
                "type": "number",
                "description": "Latitude of the location",
            },
            "longitude": {
                "type": "number",
                "description": "Longitude of the location",
            },
            "location_name": {
                "type": "string",
                "description": (
                    "Name of an Indian city/state to look up coordinates automatically. "
                    "Supported: odisha, bhubaneswar, chennai, gujarat, ahmedabad, "
                    "rajasthan, jaipur, kerala, bihar, patna, assam, guwahati, "
                    "mumbai, uttarakhand, dehradun"
                ),
            },
        },
        "required": [],
    },
    handler=disaster_check,
)
