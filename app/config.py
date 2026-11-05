from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    port: int = Field(default=8000, gt=0, le=65535)
    database_url: str
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
