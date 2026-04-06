# auth file routes and functions 
from fastapi import APIRouter, HTTPException, Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from starlette import status
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from sqlalchemy import select

from app.core.config import settings
from app.core.redis import redis_client
from app.core.database import db_dependency
from app.auth.schemas import UserRegister
from app.models.models import User

import bcrypt
import secrets



ACCESS_TOKEN_EXPIRES_MINUTES = settings.ACCESS_TOKEN_EXPIRES_MINUTES
REFRESH_TOKEN_EXPIRES_DAYS = settings.REFRESH_TOKEN_EXPIRES_DAYS
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenURL="/auth/login")

# register endpoint
@router.post("/register")
async def register(db: db_dependency, credentials: UserRegister):

    # check if username already exists 
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if user: 
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Username already exists."
        )

    # check if passwords match 
    if credentials.password != credentials.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords don't match."
        )
    
    # hash password 
    password_hash = bcrypt.hashpw(credentials.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # store username and password in db
    new_user = User(username= credentials.username,
                    password_hash=password_hash)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

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
                     ex=REFRESH_TOKEN_EXPIRES_DAYS * 86400)
    
    # return both tokens 
    return {"access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token}


# refresh endpoint
@router.post("/refresh")
async def refresh(db: db_dependency, refresh_token: str = Cookie(...)):
   
    # get user id from token
    user_id = await redis_client.get(f"refresh:{refresh_token}")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    # check if user exists in db
    user = await get_user(db, user_id)

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
        ex=REFRESH_TOKEN_EXPIRES_DAYS * 86400
    )

    # return both tokens 
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


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
