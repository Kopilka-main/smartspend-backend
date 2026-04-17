from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = ["http://localhost:5173", "https://smartspend.i20h.ru"]

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return stripped

    @field_validator("database_url")
    @classmethod
    def database_url_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_URL must not be empty")
        return v.strip()


settings = Settings()
