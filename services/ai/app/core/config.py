from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DEEPSEEK_API_KEY: str = Field(..., min_length=1)
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    DEEPSEEK_PRO_MODEL: str = "deepseek-v4-pro"
    BOT_NAME: str = "Xninetzy AI"
    BOT_OWNER: str = "Misbahul Muttaqin"
    AI_API_KEY: str = ""

    DATA_DIR: str = "/app/data"
    SQLITE_PATH: str = "/app/data/xninetzy.sqlite3"

    AGENT_MAX_ITERATIONS: int = 10
    CHAT_HISTORY_LIMIT: int = 20
    AGENT_DEBUG_ENDPOINTS: bool = True

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

    # HEBAT / Moodle integration
    HEBAT_BASE_URL: str = "https://hebat.elearning.unair.ac.id"
    HEBAT_LOGIN_URL: str = "https://hebat.elearning.unair.ac.id/login/index.php"
    HEBAT_DATA_DIR: str = "/app/data/hebat"
    HEBAT_DOWNLOAD_DIR: str = "/app/data/hebat/downloads"
    HEBAT_BROWSER_HEADLESS: bool = True
    HEBAT_ALLOW_AUTO_SUBMIT: bool = False
    HEBAT_REQUIRE_CONFIRMATION: bool = True
    HEBAT_MAX_UPLOAD_BYTES: int = 5_242_880
    HEBAT_SYNC_INTERVAL_MINUTES: int = 60
    HEBAT_REMINDER_BEFORE_HOURS: str = "24,6,1"
    HEBAT_ALLOWED_FILE_TYPES: str = ".pdf"
    HEBAT_RATE_LIMIT_SECONDS: float = 2.0
    HEBAT_USERNAME: str = ""
    HEBAT_PASSWORD: str = ""
    HEBAT_NOTIFY_CHAT_ID: str = ""
    HEBAT_AUTO_LOGIN: bool = True

    # Admin / owner policy
    ADMIN_JID: str = ""
    ADMIN_NAMES: str = "misbahul,misbahul muttaqin"
    DEEP_RESEARCH_ADMIN_ONLY: bool = True
    DEEP_RESEARCH_ALLOW_GROUP_ADMINS: bool = True
    DEEP_RESEARCH_ALLOW_ADMIN_NAMES: bool = True

    # Human-in-the-loop approvals
    HITL_ENABLED: bool = True
    HITL_REQUIRE_FOR_RESEARCH_SAVE: bool = True
    HITL_REQUIRE_FOR_ROADMAP_ACTIVATION: bool = True
    HITL_REQUIRE_FOR_HEBAT_UPLOAD: bool = True
    HITL_REQUIRE_FOR_BULK_TASK_CREATE: bool = True
    HITL_REQUIRE_FOR_OBSIDIAN_WRITE: bool = False
    HITL_REQUIRE_FOR_GRAPH_RAG_WRITE: bool = True

    def hebat_reminder_hours(self) -> list[int]:
        return [int(h.strip()) for h in self.HEBAT_REMINDER_BEFORE_HOURS.split(",") if h.strip().isdigit()]

    # Knowledge / Vector memory
    KNOWLEDGE_ENABLED: bool = True
    VECTOR_STORE: str = "faiss"
    VECTOR_DATA_DIR: str = "/app/data/vector"
    EMBEDDING_PROVIDER: str = "sentence_transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RAG_TOP_K: int = 5

    # Graph memory
    NEO4J_ENABLED: bool = False
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # External research
    WEB_SEARCH_PROVIDER: str = "tavily"
    TAVILY_API_KEY: str = ""
    SERPER_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""

    # Life OS
    LIFE_OS_ENABLED: bool = True
    DAILY_REVIEW_ENABLED: bool = True
    AUTO_APPEND_DAILY_NOTE: bool = True

    # Safety
    REQUIRE_CONFIRMATION_FOR_IMPORTANT_ACTIONS: bool = True
    ALLOW_AUTONOMOUS_UPLOAD: bool = False
    ALLOW_AUTONOMOUS_DELETE: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
