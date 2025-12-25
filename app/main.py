import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.weather.router import router as weather_router
from app.observability.router import router as observability_router
import structlog
from app.cache.redis_cache import RedisCache

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.cache = RedisCache()
    await app.state.cache.connect()
    yield
    # Shutdown
    await app.state.cache.close()

app = FastAPI(lifespan=lifespan)

app.include_router(weather_router)
app.include_router(observability_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)