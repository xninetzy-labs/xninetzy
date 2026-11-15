# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV UV_CACHE_DIR=/tmp/uv-cache \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    MCP_RUNTIME_MODE=container \
    XNINETZY_MCP_TRANSPORT=stdio \
    DATA_DIR=/app/data \
    SQLITE_PATH=/app/data/xninetzy.sqlite3 \
    BACKUP_DIR=/app/data/backups \
    OUTPUT_DIR=/app/data/output \
    GENERATED_DOCUMENTS_DIR=/app/data/generated/documents \
    RESEARCH_OUTPUT_DIR=/app/data/generated/research \
    UNTRACKED_OUTPUT_DIR=/app/data/generated/untracked \
    HEBAT_DATA_DIR=/app/data/hebat \
    HEBAT_DOWNLOAD_DIR=/app/data/hebat/downloads \
    XNINETZY_SKILLS_DIR=/app/data/skills \
    CUDA_VISIBLE_DEVICES="" \
    NVIDIA_VISIBLE_DEVICES=void \
    XNINETZY_DEVICE=cpu \
    EMBEDDING_DEVICE=cpu \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4 \
    TORCH_NUM_THREADS=4

WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY xninetzy ./xninetzy
COPY scripts ./scripts
COPY .agents ./.agents
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev --no-editable --reinstall-package xninetzy-mcp \
    && python -I scripts/check_installed_package.py --source /app/xninetzy \
    && useradd --uid 1000 --create-home xninetzy \
    && mkdir -p /app/data \
    && chown xninetzy:xninetzy /app/data

USER 1000:1000
CMD ["python", "-m", "xninetzy.interfaces.mcp_server"]
