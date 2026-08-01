from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def find_root_env() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / "docker-compose.yml").exists():
            return parent / ".env"
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_root_env(), env_file_encoding="utf-8", extra="ignore"
    )

    # Chat LLM provider registry. Credentials stay deployment-scoped; users
    # only select an enabled provider/model pair.
    LLM_DEFAULT_PROVIDER: str = "flaz"
    LLM_ENABLED_PROVIDERS: str = "flaz"
    LLM_TIMEOUT_SECONDS: float = 120.0
    LLM_MAX_RETRIES: int = 2

    FLAZ_API_KEY: str = ""
    FLAZ_BASE_URL: str = "https://ai.flaz.id/v1"
    FLAZ_MODEL: str = "deepseek-v4-pro"
    FLAZ_MODELS: str = "deepseek-v4-pro"
    FLAZ_TIMEOUT_SECONDS: float = 120.0
    FLAZ_MAX_RETRIES: int = 2
    FLAZ_THINKING_ENABLED: bool = False
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = ""
    OPENAI_MODELS: str = ""
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = ""
    ANTHROPIC_MODELS: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = ""
    OPENROUTER_MODELS: str = ""
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434/v1"
    OLLAMA_MODEL: str = ""
    OLLAMA_MODELS: str = ""
    GENERIC_OPENAI_API_KEY: str = ""
    GENERIC_OPENAI_BASE_URL: str = ""
    GENERIC_OPENAI_MODEL: str = ""
    GENERIC_OPENAI_MODELS: str = ""

    # Optional coding-agent runtimes. These execute local CLIs and are kept
    # separate from the chat LLM provider selected above.
    CODING_AGENT_ENABLED: bool = False
    CODING_AGENT_DEFAULT: str = "internal"
    CODING_AGENT_ALLOWED: str = "internal,codex,claude-code,opencode"
    CODING_AGENT_ADMIN_ONLY: bool = True
    CODING_AGENT_WORKSPACE: str = "."
    CODING_AGENT_ALLOWED_ROOT: str = "."
    CODING_AGENT_TIMEOUT_SECONDS: float = 600.0
    CODING_AGENT_MAX_OUTPUT_CHARS: int = 12_000
    CODING_AGENT_SANDBOX: str = "workspace-write"
    CODING_AGENT_ENV_ALLOWLIST: str = "PATH,HOME,USER,LOGNAME,LANG,LC_ALL,TERM,TMPDIR,XDG_CONFIG_HOME,XDG_DATA_HOME,XDG_CACHE_HOME,SSL_CERT_FILE,SSL_CERT_DIR,CODEX_HOME"
    CODING_AGENT_REQUIRE_XNINETZY_MCP: bool = True
    CODING_AGENT_MCP_SERVER_NAME: str = "xninetzy"
    CODING_AGENT_MCP_PREFLIGHT_TIMEOUT_SECONDS: float = 15.0
    CODING_AGENT_EXECUTION_MODE: str = "host_bridge"
    CODING_AGENT_HOST_BRIDGE_URL: str = "http://host.docker.internal:8765"
    CODING_AGENT_HOST_BRIDGE_TOKEN: str = ""
    CODING_AGENT_HOST_BRIDGE_TIMEOUT_SECONDS: float = 660.0
    CODING_AGENT_HOST_WORKSPACE: str = "."
    CODING_AGENT_HOST_ALLOWED_ROOT: str = "."
    CODEX_BIN: str = "codex"
    CODEX_MODEL: str = ""
    CLAUDE_CODE_BIN: str = "claude"
    CLAUDE_CODE_MODEL: str = ""
    OPENCODE_BIN: str = "opencode"
    OPENCODE_MODEL: str = ""

    CHAT_FAILOVER_ENABLED: bool = False
    CHAT_FAILOVER_RUNTIME: str = "opencode"
    CHAT_FAILOVER_MODEL: str = ""
    CHAT_FAILOVER_TIMEOUT_SECONDS: float = 120.0
    CHAT_FAILOVER_MAX_OUTPUT_CHARS: int = 8_000
    CHAT_FAILOVER_SHOW_NOTICE: bool = True
    CHAT_FAILOVER_WHATSAPP_ONLY: bool = True
    CHAT_FAILOVER_MCP_PREFLIGHT_TIMEOUT_SECONDS: float = 20.0

    XNINETZY_SKILLS_DIR: str = ""
    XNINETZY_SKILL_MAX_BYTES: int = 65_536
    XNINETZY_SKILL_MATCH_THRESHOLD: int = 4
    XNINETZY_SKILL_AUTO_INJECT_LIMIT: int = 2
    XNINETZY_SKILL_AUTO_INJECT_MAX_CHARS: int = 8_000
    XNINETZY_SKILL_ALLOW_BUILTIN_OVERRIDE: bool = False

    BOT_NAME: str = "Xninetzy AI"
    BOT_OWNER: str = "Misbahul Muttaqin"
    AI_API_KEY: str = ""
    AI_API_AUTH_REQUIRED: bool = True
    SINGLE_OWNER_MODE: bool = True
    OWNER_ALLOWED_JIDS: str = ""

    DATA_DIR: str = "/app/data"
    SQLITE_PATH: str = "/app/data/xninetzy.sqlite3"
    BACKUP_DIR: str = "/app/data/backups"
    BACKUP_RETENTION: int = 14

    AGENT_MAX_ITERATIONS: int = 10
    CHAT_HISTORY_LIMIT: int = 20
    AGENT_DEBUG_ENDPOINTS: bool = False

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
    REMINDER_SCHEDULER_INTERVAL_SECONDS: int = 30
    REMINDER_EXPIRE_AFTER_HOURS: int = 24
    REMINDER_AUTO_CREATE_ENABLED: bool = True
    REMINDER_DEFAULT_TIMEZONE: str = "Asia/Jakarta"
    WA_MCP_BASE_URL: str = "http://127.0.0.1:8081"
    WA_MCP_API_KEY: str = ""
    WA_MEDIA_MAX_BYTES: int = 25 * 1024 * 1024
    AUDIO_TRANSCRIPTION_ENABLED: bool = True
    AUDIO_TRANSCRIPTION_MODEL: str = "whisper-1"

    # Durable single-owner OS schedules. Delivery jobs are at-most-once; an
    # ambiguous WA send is surfaced for manual inspection instead of blind retry.
    OS_SCHEDULER_ENABLED: bool = True
    OS_SCHEDULER_STARTUP_DELAY_SECONDS: int = 30
    OS_SCHEDULER_POLL_SECONDS: int = 60
    OS_JOB_LEASE_SECONDS: int = 900
    OS_JOB_RETRY_DELAY_SECONDS: int = 300
    OS_NOTIFY_CHAT_ID: str = ""
    MORNING_BRIEFING_ENABLED: bool = True
    MORNING_BRIEFING_HOUR: int = 7
    EVENING_CHECKIN_ENABLED: bool = True
    EVENING_CHECKIN_HOUR: int = 20
    WEEKLY_REVIEW_ENABLED: bool = True
    WEEKLY_REVIEW_WEEKDAY: int = 6
    WEEKLY_REVIEW_HOUR: int = 20
    PRAYER_REMINDER_ENABLED: bool = True
    PRAYER_REMINDER_SCHEDULE: str = "subuh:04:30,dzuhur:11:45,ashar:15:00,maghrib:17:30,isya:18:40"
    HEBAT_PERIODIC_SYNC_ENABLED: bool = False

    # Standard stdio MCP can run either inside the AI container or directly on
    # the host through Codex, Claude Code, and OpenCode.
    MCP_RUNTIME_MODE: str = "auto"  # auto | host | container
    MCP_HOST_DATA_DIR: str = ""
    MCP_HOST_SQLITE_PATH: str = ""
    # Local stdio clients are treated as the installation owner. Context
    # arguments are injected server-side and are not trusted from MCP callers.
    MCP_PRINCIPAL_ID: str = ""
    MCP_PRINCIPAL_NAME: str = ""
    MCP_DEFAULT_CHAT_ID: str = ""

    # OCR for WhatsApp images and scanned PDFs
    OCR_ENABLED: bool = True
    OCR_LANGUAGES: str = "eng+ind"
    OCR_MAX_PDF_PAGES: int = 20
    OCR_MAX_IMAGE_PIXELS: int = 25_000_000

    # Local-only web analysis engine (one owner profile per installation)
    WEB_ANALYSIS_ENABLED: bool = True
    WEB_ANALYSIS_DATA_DIR: str = "/app/data/web-analysis"
    WEB_ANALYSIS_PROFILE_ID: str = "local-owner"
    WEB_ANALYSIS_ENCRYPTION_KEY: str = ""
    WEB_ANALYSIS_HEADLESS: bool = True
    WEB_ANALYSIS_AUTHENTICATED_CRAWL_ENABLED: bool = False
    WEB_ANALYSIS_DEFAULT_TTL_DAYS: int = 14
    WEB_ANALYSIS_MAX_PAGES: int = 10
    WEB_ANALYSIS_PORTAL_MAX_PAGES: int = 48
    WEB_ANALYSIS_DISCOVERY_MAX_DEPTH: int = 2
    WEB_ANALYSIS_MAX_VISUAL_CAPTURES: int = 3
    WEB_ANALYSIS_TIMEOUT_MS: int = 30_000
    WEB_ANALYSIS_REQUEST_DELAY_SECONDS: float = 2.0
    WEB_ANALYSIS_LOCK_STALE_SECONDS: int = 1_800
    WEB_ANALYSIS_MAX_ENCRYPTED_JSON_BYTES: int = 5_242_880
    WEB_ANALYSIS_BACKGROUND_ENABLED: bool = True
    WEB_ANALYSIS_BACKGROUND_INTERVAL_MINUTES: int = 360
    WEB_ANALYSIS_BACKGROUND_SITES: str = "hebat,mahasiswa,qa"
    WEB_ANALYSIS_BACKGROUND_AUTHENTICATED: bool = False
    ACADEMIC_CREDENTIAL_SOURCE: str = "hebat"
    CYBER_CAMPUS_ENABLED: bool = False
    CYBER_CAMPUS_BASE_URL: str = "https://mahasiswa.unair.ac.id"
    CYBER_CAMPUS_CREDENTIAL_SOURCE: str = "hebat"
    CYBER_CAMPUS_BROWSER_HEADLESS: bool = True
    CYBER_CAMPUS_LOGIN_CHALLENGE_TTL_SECONDS: int = 600
    CYBER_CAMPUS_LOGIN_MAX_ATTEMPTS: int = 3
    CYBER_CAMPUS_LOGIN_TIMEOUT_MS: int = 30_000
    CYBER_CAMPUS_GRADE_TOKEN_TTL_SECONDS: int = 180
    CYBER_CAMPUS_GRADE_TOKEN_MAX_ATTEMPTS: int = 3
    CYBER_CAMPUS_ENTRY_YEAR: int = 0
    KRS_WATCHER_DEFAULT_INTERVAL_SECONDS: int = 600
    KRS_WATCHER_ANNOUNCEMENT_INTERVAL_SECONDS: int = 30
    KRS_WATCHER_WINDOW_INTERVAL_SECONDS: int = 10

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
    QA_CREDENTIAL_SOURCE: str = "hebat"
    QA_BROWSER_HEADLESS: bool = False
    QA_RECAPTCHA_SETTLE_MS: int = 3000
    HEBAT_NOTIFY_CHAT_ID: str = ""
    HEBAT_AUTO_LOGIN: bool = False
    # Max automatic re-logins per request when a stale cookie redirects to /login.
    # Bounds the relogin+retry loop so a permanently-broken session can't spin forever.
    HEBAT_SESSION_MAX_RELOGIN: int = 2
    # Persist raw/cleaned HTML to disk on failure for offline debugging.
    HEBAT_DEBUG_SAVE_HTML: bool = False
    HEBAT_DEBUG_HTML_DIR: str = "/app/data/hebat/debug-html"

    # Multi-action workflow engine
    WORKFLOW_ENABLED: bool = True
    WORKFLOW_RUNNER_MODE: str = "inline"  # inline | queued (queued not implemented yet)
    WORKFLOW_NOTIFY_ENABLED: bool = True
    WORKFLOW_NOTIFY_ON_START: bool = False
    WORKFLOW_NOTIFY_ON_DONE: bool = True
    WORKFLOW_NOTIFY_MIN_INTERVAL_SECONDS: float = 3.0
    WORKFLOW_NOTIFY_MAX_MESSAGE_LENGTH: int = 500
    WORKFLOW_MAX_ACTIONS: int = 12

    # Admin / owner policy
    ADMIN_JID: str = ""
    ADMIN_NAMES: str = "misbahul,misbahul muttaqin"
    DEEP_RESEARCH_ADMIN_ONLY: bool = True
    DEEP_RESEARCH_ALLOW_GROUP_ADMINS: bool = True
    DEEP_RESEARCH_ALLOW_ADMIN_NAMES: bool = True

    # Deep research resource guards (enforced regardless of admin gate)
    DEEP_RESEARCH_MAX_CONCURRENT_PER_CHAT: int = 2
    DEEP_RESEARCH_MAX_SOURCES: int = 40
    DEEP_RESEARCH_MAX_QUERIES: int = 24
    DEEP_RESEARCH_TIMEOUT_SECONDS: int = 180

    # Human-in-the-loop approvals
    HITL_ENABLED: bool = True
    HITL_REQUIRE_FOR_RESEARCH_SAVE: bool = True
    HITL_REQUIRE_FOR_ROADMAP_ACTIVATION: bool = True
    HITL_REQUIRE_FOR_HEBAT_UPLOAD: bool = True
    HITL_REQUIRE_FOR_BULK_TASK_CREATE: bool = True
    HITL_REQUIRE_FOR_OBSIDIAN_WRITE: bool = False
    HITL_REQUIRE_FOR_GRAPH_RAG_WRITE: bool = True
    ACTION_POLICY_DEFAULT_MODE: str = "approval"
    ACTION_POLICY_OVERRIDES: str = ""
    ACTION_POLICY_TTL_SECONDS: int = 300
    ACTION_POLICY_MAX_WRITES_PER_RUN: int = 30
    ACTION_POLICY_KILL_SWITCH: bool = False

    def hebat_reminder_hours(self) -> list[int]:
        return [
            int(h.strip())
            for h in self.HEBAT_REMINDER_BEFORE_HOURS.split(",")
            if h.strip().isdigit()
        ]

    # Knowledge / Vector memory
    KNOWLEDGE_ENABLED: bool = True
    VECTOR_STORE: str = "faiss"
    VECTOR_DATA_DIR: str = "/app/data/vector"
    EMBEDDING_PROVIDER: str = "sentence_transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # CPU-only AI runtime. Xninetzy runs all inference on CPU exclusively.
    # These knobs pin Sentence Transformers / PyTorch to CPU and cap the thread
    # pools for a personal single-owner workload. A GPU-enabled build is
    # rejected at startup by app.xninetzy.runtime.cpu_guard.
    XNINETZY_DEVICE: str = "cpu"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BACKEND: str = "torch"  # torch | onnx (onnx reserved, not yet wired)
    EMBEDDING_NORMALIZE: bool = True
    EMBEDDING_BATCH_SIZE: int = 16
    AI_CPU_THREADS: int = 4

    def cpu_threads(self) -> int:
        """Thread cap for torch/OMP/MKL — at least 1."""
        return max(1, int(self.AI_CPU_THREADS))

    RAG_TOP_K: int = 5
    RAG_AUTO_GROUND_ENABLED: bool = True
    RAG_MIN_EVIDENCE: int = 1
    RAG_MAX_CONTEXT_CHARS: int = 6_000
    # Retrieval quality gates. Rank-only RRF happily returns off-topic lexical
    # hits (common words, keyword-dense bibliographies) with a real fused score,
    # so a bundle could be labelled sufficient/high for a query the vault does
    # not actually cover. These knobs re-introduce a true relevance signal:
    #   * cosine floor — a chunk must clear RAG_MIN_RELEVANCE semantic similarity
    #     (0..1) to count as evidence at all.
    #   * reference penalty — bibliography / DOI / "daftar pustaka" chunks are
    #     keyword-dense but low-information; discount their score.
    #   * topic consistency — sufficient requires the surviving evidence to agree
    #     on a source, not just exist.
    RAG_MIN_RELEVANCE: float = 0.28  # cosine floor for a chunk to be evidence
    RAG_HIGH_RELEVANCE: float = 0.45  # cosine at/above this reads as strong
    RAG_REFERENCE_PENALTY: float = 0.5  # multiplier applied to reference chunks
    RAG_TOPIC_CONSISTENCY_MIN: float = 0.5  # min share of top source among evidence

    # Router-based document extraction ecosystem. Classifies each document as
    # simple vs complex and selects open-source extractors accordingly. No
    # Docling, no vision LLM — images fall back to deterministic tesseract OCR.
    DOC_EXTRACTION_ENABLED: bool = True
    DOC_ROUTER_COMPLEX_PAGE_THRESHOLD: int = 8
    DOC_ROUTER_MIN_TEXT_RATIO: int = 120  # chars/page below this ⇒ treat as scanned
    DOC_ROUTER_SAMPLE_PAGES: int = 4  # pages probed for text-ratio / table sniff
    DOC_TABLE_EXTRACTION_ENABLED: bool = True
    DOC_IMAGE_OCR_ENABLED: bool = True
    DOC_OVERVIEW_ENABLED: bool = True
    DOC_OVERVIEW_BATCH_SIZE: int = 6
    DOC_OVERVIEW_MAX_BATCHES: int = 8
    DOC_MAX_PAGES: int = 200

    # Graph memory
    NEO4J_ENABLED: bool = False
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"
    # Optional path to a Docker/mounted secret file containing the Neo4j
    # password (one line). When set and readable it overrides NEO4J_PASSWORD so
    # the credential never has to live in .env. Empty ⇒ use NEO4J_PASSWORD.
    NEO4J_AUTH_FILE: str = ""
    # Host MCP runs outside the compose network, so the docker-DNS NEO4J_URI
    # (bolt://neo4j:7687) is unreachable. In host runtime we swap to the
    # published loopback port instead. Auto-start boots the `graph` compose
    # profile on first graph access and stops the container after it goes idle,
    # so Neo4j only runs while graph tools are actually in use.
    NEO4J_HOST_URI: str = "bolt://127.0.0.1:7687"
    NEO4J_AUTOSTART_ENABLED: bool = True
    NEO4J_AUTOSTART_COMPOSE_SERVICE: str = "neo4j"
    NEO4J_AUTOSTART_PROFILE: str = "graph"
    NEO4J_AUTOSTART_BOOT_TIMEOUT_SECONDS: int = 60  # cold-start bolt-ready wait
    NEO4J_AUTOSTART_IDLE_STOP_SECONDS: int = 300  # stop container after idle
    NEO4J_AUTOSTART_STOP_ON_EXIT: bool = True  # stop when the MCP process exits

    # GraphRAG V3 — tri-store (SQLite source-of-truth + Neo4j projection +
    # FAISS semantic index) via outbox/projection-worker + hybrid RRF retriever.
    # Fully gated: when disabled the V3 stores, worker, and tools stay dormant
    # and the legacy V1 graph_store keeps working untouched.
    GRAPHRAG_V3_ENABLED: bool = False
    GRAPH_VECTOR_DATA_DIR: str = "/app/data/graph_vector"
    GRAPH_SYNC_POLL_SECONDS: int = 15
    GRAPH_SYNC_BATCH_SIZE: int = 32
    GRAPH_SYNC_LEASE_SECONDS: int = 120
    GRAPH_SYNC_MAX_ATTEMPTS: int = 6
    GRAPH_SYNC_RETRY_BASE_SECONDS: int = 20
    GRAPH_SYNC_STARTUP_DELAY_SECONDS: int = 8
    GRAPH_RRF_K: int = 60
    GRAPH_RETRIEVAL_TOP_K: int = 8
    GRAPH_COMMUNITY_ENABLED: bool = False
    GRAPH_COMMUNITY_INTERVAL_MINUTES: int = 360

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
