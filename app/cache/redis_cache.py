import os
import json
from typing import Dict, Optional
import aioredis
from structlog import getLogger

GEOCODE_TTL = 24 * 3600  # 24h
WEATHER_TTL = 15 * 60    # 15min
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class RedisCache:
    def __init__(self):
        self.redis_url = REDIS_URL
        self.redis: Optional[aioredis.Redis] = None

    # --- Connect / Close ---
    async def connect(self):
        self.redis = await aioredis.from_url(
            self.redis_url, encoding="utf-8", decode_responses=True
        )
        getLogger().info("Redis connected")

    async def close(self):
        if self.redis:
            await self.redis.close()
            self.redis = None
            print("Redis closed")

    # --- Keys ---
    @staticmethod
    def city_key(city_name: str) -> str:
        return f"city:{city_name.lower()}"

    @staticmethod
    def weather_key(city_name: str) -> str:
        return f"weather:{city_name.lower()}"

    # --- City cache ---
    async def cache_city_geo(self, city_name: str, lat: float, lon: float):
        if not self.redis:
            return
        try:
            value = {"lat": lat, "lon": lon}
            await self.redis.set(self.city_key(city_name), json.dumps(value), ex=GEOCODE_TTL)
        except Exception as e:
            getLogger().warning("Failed to cache city geo", city=city_name, exc_info=e)

    async def get_city_geo(self, city_name: str) -> Optional[Dict]:
        if not self.redis:
            return None
        try:
            cached = await self.redis.get(self.city_key(city_name))
            return json.loads(cached) if cached else None
        except Exception as e:
            getLogger().warning("Failed to get city geo", city=city_name, exc_info=e)
            return None

    # --- Weather cache ---
    async def cache_weather(self, city_name: str, weather_data: Dict):
        if not self.redis:
            return
        try:
            await self.redis.set(self.weather_key(city_name), json.dumps(weather_data), ex=WEATHER_TTL)
        except Exception as e:
            getLogger().warning("Failed to cache weather", city=city_name, exc_info=e)

    async def get_weather(self, city_name: str) -> Optional[Dict]:
        if not self.redis:
            return None
        try:
            cached = await self.redis.get(self.weather_key(city_name))
            return json.loads(cached) if cached else None
        except Exception as e:
            getLogger().warning("Failed to get weather", city=city_name, exc_info=e)
            return None