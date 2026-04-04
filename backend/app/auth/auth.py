from fastapi import APIRouter, Depends, HTTPException
from database import db_dependency
from schemas import UserRegister
from models import User
import bcrypt
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from starlette import status
from jose import jwt, JWTError
from datetime import datetime, timedelta
from config import settings


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
TOKEN_ACCESS_EXPIRES_MINUTES = settings.TOKEN_ACCESS_EXPIRES_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register")
def register(user: UserRegister, db: db_dependency):

    if user.password != user.confirm_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Passwords don't match")
    
    password_hash = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    new_user = User(username = user.username, password_hash = password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "user has been created"}

@router.post("/login")
def login(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    
    user = db.query(User).filter(User.username == form_data.username).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    if not bcrypt.checkpw(form_data.password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect password")
    
    return generate_access_token({"sub": user.username})
    

def get_current_user(db: db_dependency, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token not verified")
    username: str = payload.get("sub")
    if username is None: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 
                            detail="User not found")
    
    return user


def generate_access_token(data: dict):
    to_encode = data.copy()
    expires = datetime.utcnow() + timedelta(minutes=TOKEN_ACCESS_EXPIRES_MINUTES)
    to_encode.update({"exp": expires})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}