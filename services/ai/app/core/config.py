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
    AI_API_KEY: str = ""

    DATA_DIR: str = "/app/data"
    SQLITE_PATH: str = "/app/data/xninetzy.sqlite3"

    SKILLS_ENABLED: bool = True
    SKILL_DEBUG_ENDPOINTS: bool = True

    OBSIDIAN_ENABLED: bool = True
    OBSIDIAN_VAULT_HOST_PATH: str = "~/Documents/xninetzy"
    OBSIDIAN_VAULT_PATH: str = "/app/obsidian-vault"
    OBSIDIAN_ALLOW_WRITE: bool = True
    OBSIDIAN_ALLOW_DELETE: bool = False
    OBSIDIAN_BACKUP_BEFORE_WRITE: bool = True
    OBSIDIAN_MAX_FILE_SIZE_MB: int = 5

    REMINDER_ENABLED: bool = True
    APP_TIMEZONE: str = "Asia/Jakarta"
    REMINDER_POLL_INTERVAL_SECONDS: int = 30
    WA_MCP_BASE_URL: str = "http://wa-enggine:8081"
    WA_MCP_API_KEY: str = ""

    WORKFLOW_ENABLED: bool = True
    WORKFLOW_REQUIRE_CONFIRMATION: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
