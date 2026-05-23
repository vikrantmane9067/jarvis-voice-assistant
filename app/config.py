from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "JARVIS AI Command Center"
    APP_VERSION: str = "3.0.0"
    SECRET_KEY: str = "change-this-secret"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./jarvis.db"
    ALLOWED_ORIGINS: List[str] = ["*"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
