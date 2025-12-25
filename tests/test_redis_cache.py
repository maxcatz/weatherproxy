import pytest
import json
from unittest.mock import AsyncMock
from app.cache.redis_cache import RedisCache

@pytest.mark.asyncio
async def test_cache_and_get_city_geo():
    cache = RedisCache()
    cache.redis = AsyncMock()

    city_name = "London"
    lat, lon = 51.5074, -0.1278

    # Test caching
    await cache.cache_city_geo(city_name, lat, lon)
    cache.redis.set.assert_awaited_once_with(
        cache.city_key(city_name),
        json.dumps({"lat": lat, "lon": lon}),
        ex=24 * 3600
    )

    # Mock get to return cached value
    cache.redis.get.return_value = json.dumps({"lat": lat, "lon": lon})
    result = await cache.get_city_geo(city_name)
    assert result == {"lat": lat, "lon": lon}


@pytest.mark.asyncio
async def test_cache_and_get_weather():
    cache = RedisCache()
    cache.redis = AsyncMock()

    city_name = "Paris"
    weather_data = {"temp": 20, "humidity": 50}

    # Test caching
    await cache.cache_weather(city_name, weather_data)
    cache.redis.set.assert_awaited_once_with(
        cache.weather_key(city_name),
        json.dumps(weather_data),
        ex=15 * 60
    )

    # Mock get to return cached value
    cache.redis.get.return_value = json.dumps(weather_data)
    result = await cache.get_weather(city_name)
    assert result == weather_data


@pytest.mark.asyncio
async def test_raises_if_redis_not_connected():
    cache = RedisCache()
    cache.redis = None


    result = await cache.cache_city_geo("London", 51.5, -0.1)
    assert result is None

    result = await cache.get_city_geo("London")
    assert result is None

    result = await cache.cache_weather("Paris", {"temp": 20})
    assert result is None

    result = await cache.get_weather("Paris")
    assert result is None
