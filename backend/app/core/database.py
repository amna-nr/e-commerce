# database connection 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings 
from typing import Annotated 
from fastapi import Depends


DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)

Base = declarative_base()

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as db:
        try: 
            yield db 
        except Exception:
            await db.rollback()
            raise 

db_dependency = Annotated[AsyncSession, Depends(get_db)]