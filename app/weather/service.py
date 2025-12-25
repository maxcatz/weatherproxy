import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
from app.observability.log_metrics import log_metrics

from app.cache.redis_cache import RedisCache

GEOCODE_TTL = 86400  # 24 hours

CACHE_TTL = 600

class CityNotFound(Exception):
    pass

@log_metrics
async def get_weather(city: str, cache: RedisCache):
    cached = await cache.get_weather(city)
    if cached:
        return cached

    lat, lon = await resolve_city(city, cache)
    data = await fetch_weather(lat, lon)

    await cache.cache_weather(city, data)
    return data

@log_metrics
@retry(stop=stop_after_attempt(3), wait=wait_exponential(), retry=retry_if_not_exception_type(CityNotFound))
async def resolve_city(city: str, cache: RedisCache) -> tuple[float, float]:

    data = await cache.get_city_geo(city)
    if data:
        return data["lat"], data["lon"]

    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
        )
        resp.raise_for_status()

    data = resp.json()
    if not data.get("results"):
        raise CityNotFound(f"City '{city}' not found")

    result = data["results"][0]
    lat, lon = result["latitude"], result["longitude"]

    await cache.cache_city_geo(city, lat, lon)

    return lat, lon

@log_metrics
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def fetch_weather(lat: float, lon: float):
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True}
        )
        resp.raise_for_status()
        return resp.json()
