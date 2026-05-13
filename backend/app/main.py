from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.redis import redis_client
from app.auth.router import router as auth_router
from app.products.router import router as products_router
from app.routers.health import router as health_router
from app.core.logging import setup_logging, logger



# start redis on startup and close on shutdown and add logging
@asynccontextmanager
async def lifespan(app: FastAPI):
    # configure logging
    setup_logging()
    logger.info("app_started")
    await redis_client.ping()
    yield 
    await redis_client.aclose()
    logger.info("app_shutdown")

# identify each caller by their ip address
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan)

# enable frontend to access backend on the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# set up rate limiting 
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# include auth routes
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(health_router)


@app.get("/")
def home():
    return {"message": "welcome"}