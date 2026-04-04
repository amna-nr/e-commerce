from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings
from typing import Annotated
from fastapi import Depends

DATABASE_URL = settings.DATABASE_URL 

engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

def create_tables():
    Base.metadata.create_all(bind=engine)