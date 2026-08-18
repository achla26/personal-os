from pydantic_settings import BaseSettings 

class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = True
    APP_NAME: str ="Personal-OS"
    DEV_USER_ID: str

    class Config:
        env_file = ".env"

settings =Settings()        