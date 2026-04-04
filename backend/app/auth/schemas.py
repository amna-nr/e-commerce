from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str
    confirm_password: str
