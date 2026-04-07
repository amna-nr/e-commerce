from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.redis import redis_client
from app.auth.router import router as auth_router
from app.core.logging import setup_logging, logger

# configure logging
setup_logging()

# start redis on startup and close on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.ping()
    yield 
    await redis_client.aclose()

app = FastAPI(lifespan=lifespan)

# include auth routes
app.include_router(auth_router)

# enable frontend to access backend on the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "welcome"}


# log that app started 
@app.on_event("startup")
async def startup():
    logger.info("app started")


