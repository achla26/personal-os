from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Automatically locate the backend/ folder where .env lives
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    DEBUG: bool = True
    APP_NAME: str = "Personal-OS"
    DEV_USER_ID: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE: int
    LLM_API_KEY: str
    LLM_MODEL: str

settings = Settings()