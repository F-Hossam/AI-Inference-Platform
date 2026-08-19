from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env.local",
        env_prefix="API_",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = Field(validation_alias="API_DATABASE_URL")
    inference_base_url: AnyHttpUrl = Field(
        validation_alias="API_INFERENCE_BASE_URL"
    )
    cors_origins: list[str] = Field(validation_alias="API_CORS_ORIGINS")
    jwt_secret_key: SecretStr = Field(validation_alias="API_JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=480, gt=0, le=10080)
    auth_cookie_name: str = "ai_session"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    connect_timeout_seconds: float = Field(default=5, gt=0, le=60)
    inference_timeout_seconds: float = Field(default=300, gt=0, le=1800)


@lru_cache
def get_settings() -> Settings:
    return Settings()
