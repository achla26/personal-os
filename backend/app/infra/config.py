from pydantic_settings import BaseSettings 

class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = True
    APP_NAME: str ="Personal-OS"
    DEV_USER_ID: str
    JWT_SECRET: str
    JWT_ALGORITHM : str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE: int

    class Config:
        env_file = ".env"

settings =Settings()        