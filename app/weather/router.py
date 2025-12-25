import structlog
from fastapi import APIRouter, Query, Depends, Request, HTTPException
from app.weather.service import get_weather, CityNotFound
from app.cache.redis_cache import RedisCache

log = structlog.get_logger(__name__)
router = APIRouter()

# Dependency to access RedisCache
def get_cache(request: Request) -> RedisCache:
    return request.app.state.cache

@router.get("/weather")
async def weather(city: str = Query(..., min_length=2),
                  cache: RedisCache = Depends(get_cache)):  # Inject RedisCache
    log.info(f"Ask for weather in {city}")
    try:
        data = await get_weather(city, cache)
        return data
    except CityNotFound as e:
        log.warning(f"City not found: {city}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error(f"Error fetching weather for {city}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")