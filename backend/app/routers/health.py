from fastapi import APIRouter
from app.core.database import db_dependency
from app.core.redis import redis_client


router = APIRouter(
    prefix="/health",
    tags=["health"]
)

@router.get("")
async def health(db: db_dependency):
    try: 
        await db.execute("SELECT(1)")
        await redis_client.ping()
        return {"status": "healthy", "db": "up", "redis": "up"}
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
