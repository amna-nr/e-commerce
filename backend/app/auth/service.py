from app.core.database import db_dependency
from app.core.config import settings
from app.models.models import User

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from starlette import status
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from sqlalchemy import select


ACCESS_TOKEN_EXPIRES_MINUTES = settings.ACCESS_TOKEN_EXPIRES_MINUTES
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# user verification function for sensitive routes
async def get_current_user_protected(db: db_dependency, token: str = Depends(oauth2_scheme)):

    # decode jwt using secret key
    payload = decode_jwt(token, SECRET_KEY, ALGORITHM)

    # get user id
    user_id = payload.get("id")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # check if user exists 
    user = await get_user(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# user verification function for every request
async def get_current_user(token: str = Depends(oauth2_scheme)):

    # decode jwt using secret key
    payload = decode_jwt(token, SECRET_KEY, ALGORITHM)

    return payload


# generate access token function 
def generate_access_token(data: dict):
    to_encode = data.copy()
    expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    to_encode.update({"exp": expires})
    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return access_token


# decode jwt token using secret key
def decode_jwt(token: str, SECRET_KEY: str, ALGORITHM: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return payload 

# function to get user from db
async def get_user (db: db_dependency, id: int):
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    return user 
