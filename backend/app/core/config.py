from pydantic_settings import BaseSettings 


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str

    class Config():
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()