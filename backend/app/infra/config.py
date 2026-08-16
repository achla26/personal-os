from pydantic_settings import BaseSettings 

class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = True
    APP_NAME: str ="Personal-OS"

    class Config:
        env_file = ".env"

settings =Settings()        