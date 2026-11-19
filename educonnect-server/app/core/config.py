from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "EDUCONNECT School Server"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./educonnect.db"
    CONTENT_STORAGE_DIR: Path = Path("./storage/content")
    SECRET_KEY: str = "offline-school-insecure-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DEFAULT_SCHOOL_ID: str = "0194c7b0-0000-7000-8000-000000000001"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
settings.CONTENT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
