# auth file routes and functions 
from fastapi import APIRouter, HTTPException, Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from starlette import status 

from app.auth.service import get_user, generate_access_token
from app.core.redis import redis_client
from app.core.database import db_dependency
from app.auth.schemas import UserRegister
from app.models.models import User
from app.core.config import settings
from app.core.logging import logger


import bcrypt
import secrets

REFRESH_TOKEN_EXPIRES_DAYS = settings.REFRESH_TOKEN_EXPIRES_DAYS

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


# register endpoint
@router.post("/register")
async def register(db: db_dependency, credentials: UserRegister):

    # check if passwords match 
    if credentials.password != credentials.confirm_password:
        logger.warning("password_failed_password_mismatch")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords don't match."
        )

    # check if username already exists 
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if user: 
        logger.warning("register_failed_duplicate", username=credentials.username)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists."
        )
    
    # hash password 
    password_hash = bcrypt.hashpw(credentials.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # store username and password in db
    new_user = User(username= credentials.username,
                    password_hash=password_hash)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info("register_success", user_id=str(new_user.id))


    return {"message": "User has been created."}


# login endpoint
@router.post("/login")
async def login(db: db_dependency, credentials: OAuth2PasswordRequestForm = Depends()):

    # check if user exists in db 
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if user is None: 
        logger.warning("login_failed_not_found", username=credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # check password in db vs users both hashed
    if not bcrypt.checkpw(credentials.password.encode("utf-8"), user.password_hash.encode("utf-8")):
        logger.warning("login_failed_wrong_password", user_id=str(user.id))
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
    
    logger.info("login_success", user_id=str(user.id))
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


    logger.info("refresh_success", user_id=str(user.id))
    # return both tokens 
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }
