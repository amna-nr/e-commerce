# auth file routes and functions 
from fastapi import APIRouter, HTTPException
from core.database import db_dependency
from schemas import UserRegister
from starlette import status
import bcrypt
from models.models import User

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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Passwords don't match"
            )
    
    # hash password 
    password_hash = bcrypt.hashpw(credentials.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # store username and password in db
    new_user = User(username= credentials.username, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User has been created"}

# login 
# check if user exists in db 
# hash password 
# check password in db vs users both hashed 
# if login successful generate access token 
# generate refresh token 
# store refresh token in redis 
# return both tokens 

# refresh 
# check if refresh token exists in redis 
# check if user exists in db
# generate new access token 
# invalidate old refresh token 
# generate new refresh token 
# return both tokens 

