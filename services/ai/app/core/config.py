from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DEEPSEEK_API_KEY: str = Field(..., min_length=1)
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    BOT_NAME: str = "Xninetzy AI"
    BOT_OWNER: str = "Misbahul Muttaqin"


@lru_cache
def get_settings() -> Settings:
    return Settings()
