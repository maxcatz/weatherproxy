import pytest
from unittest.mock import AsyncMock, patch

import respx
from fastapi.testclient import TestClient

from app.cache.redis_cache import RedisCache
from app.main import app
from httpx import Response

client = TestClient(app)


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_endpoint_with_mocked_provider():
    mock_cache = RedisCache()
    mock_cache.get_weather = AsyncMock(return_value={"temp": 25, "condition": "Sunny"})
    app.state.cache = mock_cache
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(
            200,
            json={"results": [{"latitude": 48.8566, "longitude": 2.3522}]}
        )
    )

    with patch("app.cache.redis_cache", mock_cache):
        response = client.get("/weather?city=Paris")
        assert response.status_code == 200
        data = response.json()
        assert data["temp"] == 25
        assert data["condition"] == "Sunny"


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_endpoint_cache_not_available():
    mock_cache = RedisCache()
    mock_cache.get_weather = AsyncMock(return_value=None)
    mock_cache.get_city_geo  = AsyncMock(return_value=None)
    mock_cache.cache_city_geo = AsyncMock()
    app.state.cache = mock_cache

    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(
            200,
            json={"results": [{"latitude": 55.0, "longitude": 83.0}]}
        )
    )

    respx.get("https://api.open-meteo.com/v1/forecast").mock(return_value=Response(
            200,
            json={
                "latitude": 55.0,
                "longitude": 83.0,
                "generationtime_ms": 0.055789947509765625,
                "utc_offset_seconds": 0,
                "timezone": "GMT",
                "timezone_abbreviation": "GMT",
                "elevation": 135.0,
                "current_weather_units": {
                    "time": "iso8601",
                    "interval": "seconds",
                    "temperature": "°C",
                    "windspeed": "km/h",
                    "winddirection": "°",
                    "is_day": "",
                    "weathercode": "wmo code"
                },
                "current_weather": {
                    "time": "2025-12-25T14:30",
                    "interval": 900,
                    "temperature": -4.8,
                    "windspeed": 12.4,
                    "winddirection": 197,
                    "is_day": 0,
                    "weathercode": 71
                }
            }
        ))

    with patch("app.cache.redis_cache", mock_cache):
        response = client.get("/weather?city=Paris")
        assert response.status_code == 200
        data = response.json()
        assert data["current_weather"]["temperature"] == -4.8

@pytest.mark.asyncio
@respx.mock
async def test_weather_endpoint_geocoding_city_not_found():
    mock_cache = RedisCache()
    mock_cache.get_weather = AsyncMock(return_value=None)
    mock_cache.get_city_geo = AsyncMock(return_value=None)
    mock_cache.cache_city_geo = AsyncMock()
    app.state.cache = mock_cache

    city = "ZZ"

    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(
            200,
            json={"generationtime_ms": 0.109910965}
        )
    )

    response = client.get(f"/weather?city={city}")

    assert response.status_code == 404
    data = response.json()
    assert data['detail'] ==  "City 'ZZ' not found"


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_endpoint_retries():
    mock_cache = RedisCache()
    mock_cache.get_weather = AsyncMock(return_value=None)
    mock_cache.get_city_geo  = AsyncMock(return_value=None)
    mock_cache.cache_city_geo = AsyncMock()
    app.state.cache = mock_cache

    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(
            200,
            json={"results": [{"latitude": 55.0, "longitude": 83.0}]}
        )
    )

    route = respx.get("https://api.open-meteo.com/v1/forecast").mock(return_value=Response(
            500
        ))

    with patch("app.cache.redis_cache", mock_cache):
        response = client.get("/weather?city=Paris")
        assert response.status_code == 500
        assert route.call_count == 3