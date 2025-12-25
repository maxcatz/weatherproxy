import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock, MagicMock
from app.weather.service import resolve_city, get_weather, CityNotFound
from app.cache.redis_cache import RedisCache

@pytest.mark.asyncio
@respx.mock
async def test_resolve_city_success():
    mock_cache = MagicMock(spec=RedisCache)
    mock_cache.get_city_geo = AsyncMock(return_value=None)
    mock_cache.cache_city_geo = AsyncMock()
    
    city = "Berlin"
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(200, json={
            "results": [{"latitude": 52.52, "longitude": 13.405}]
        })
    )

    lat, lon = await resolve_city(city, mock_cache)

    assert lat == 52.52
    assert lon == 13.405
    mock_cache.cache_city_geo.assert_awaited_once_with(city, 52.52, 13.405)

@pytest.mark.asyncio
async def test_resolve_city_from_cache():
    mock_cache = MagicMock(spec=RedisCache)
    mock_cache.get_city_geo = AsyncMock(return_value={"lat": 40.71, "lon": -74.00})
    
    lat, lon = await resolve_city("New York", mock_cache)

    assert lat == 40.71
    assert lon == -74.00
    # Ensure no network call would have been made if we didn't mock it with respx
    mock_cache.get_city_geo.assert_awaited_once()

@pytest.mark.asyncio
@respx.mock
async def test_resolve_city_not_found():
    mock_cache = MagicMock(spec=RedisCache)
    mock_cache.get_city_geo = AsyncMock(return_value=None)
    
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(200, json={"results": []})
    )

    with pytest.raises(CityNotFound, match="City 'Unknown' not found"):
        await resolve_city("Unknown", mock_cache)

@pytest.mark.asyncio
@respx.mock
async def test_get_weather_full_flow():
    mock_cache = MagicMock(spec=RedisCache)
    mock_cache.get_weather = AsyncMock(return_value=None)
    mock_cache.get_city_geo = AsyncMock(return_value={"lat": 10.0, "lon": 20.0})
    mock_cache.cache_weather = AsyncMock()

    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=Response(200, json={"current_weather": {"temperature": 15.0}})
    )

    data = await get_weather("TestCity", mock_cache)

    assert data["current_weather"]["temperature"] == 15.0
    mock_cache.cache_weather.assert_awaited_once()
