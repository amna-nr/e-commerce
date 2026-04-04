# auth file routes and functions 
from fastapi import APIRouter, HTTPException, Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from starlette import status
from datetime import datetime, timedelta
from jose import jwt, JWTError
from sqlalchemy import select

from app.core.config import settings
from app.core.redis import redis_client
from app.core.database import db_dependency
from app.auth.schemas import UserRegister
from app.models.models import User

import bcrypt
import secrets



ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# register endpoint
@router.post("/register")
async def register(db: db_dependency, credentials: UserRegister):

    # check if passwords match 
    if credentials.password != credentials.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords don't match."
        )
    
    # hash password 
    password_hash = bcrypt.hashpw(credentials.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # store username and password in db
    new_user = User(username= credentials.username, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User has been created."}


# login endpoint
@router.post("/login")
async def login(db: db_dependency, credentials: OAuth2PasswordRequestForm = Depends()):

    # check if user exists in db 
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if user is None: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    # check password in db vs users both hashed
    if not bcrypt.checkpw(credentials.password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password."
        )
    
    # generate access token
    access_token = generate_access_token({"id": user.id,
                                          "sub": user.username}) 
    
    # generate refresh token 
    refresh_token = secrets.token_urlsafe()

    # store refresh token in redis 
    await redis_client.set(f"refresh:{refresh_token}",
                     user.id,
                     ex=REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    
    # return both tokens 
    return {"access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token}


# refresh endpoint
@router.post("/refresh")
async def refresh(db: db_dependency, refresh_token: str = Cookie(...)):
   
    # check if refresh token exists in redis 
    if refresh_token is None: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token does not exist."
        )
    
    # get user id from token
    user_id = await redis_client.get(f"refresh:{refresh_token}")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    # check if user exists in db
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    # generate new access token 
    access_token = generate_access_token({"id": user.id,
                                          "sub": user.username})
    
    # invalidate old refresh token 
    await redis_client.delete(f"refresh:{refresh_token}")

    # generate new refresh token 
    refresh_token = secrets.token_urlsafe()

    # store new refresh token in redis 
    await redis_client.set(
        f"refresh:{refresh_token}",
        user.id,
        ex=REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )

    # return both tokens 
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


# user verification function for every request
# user verification function for sensitive routes 

# generate access token function 
def generate_access_token(data: dict):
    to_encode = data.copy()
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expires})
    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token,
            "token_type": "bearer"}




