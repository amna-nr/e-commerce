# auth file routes and functions 
from fastapi import APIRouter, HTTPException, Depends
from core.database import db_dependency
from schemas import UserRegister
from starlette import status
import bcrypt
import secrets
from models.models import User
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from core.config import settings
from jose import jwt, JWTError


TOKEN_ACCESS_EXPIRE_MINUTES = settings.TOKEN_ACCESS_EXPIRE_MINUTES
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# register
@router.post("/register")
def register(db: db_dependency, credentials: UserRegister):

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


# login 
@router.post("/login")
def login(db: db_dependency, credentials: OAuth2PasswordRequestForm = Depends()):

    # check if user exists in db 
    user = db.query(User).filter(User.username == credentials.username).first()

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
    # return both tokens 

# refresh 
# check if refresh token exists in redis 
# check if user exists in db
# generate new access token 
# invalidate old refresh token 
# generate new refresh token 
# return both tokens 

# generate access token function 
def generate_access_token(data: dict):
    to_encode = data.copy()
    expires = datetime.utcnow() + timedelta(minutes=TOKEN_ACCESS_EXPIRE_MINUTES)
    to_encode.update({"exp": expires})
    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token,
            "token_type": "bearer"}




