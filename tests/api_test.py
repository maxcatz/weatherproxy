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
async def test_get_weather_endpoint_provider_raises_error():
    mock_cache = RedisCache()
    mock_cache.get_weather = AsyncMock(side_effect=RuntimeError("Provider error"))
    app.state.cache = mock_cache

    with patch("app.cache.redis_cache", mock_cache):
        response = client.get("/weather?city=Paris")
        assert response.status_code == 500