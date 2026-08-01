# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# CPU-only AI runtime. These pin PyTorch / Sentence Transformers to CPU and cap
# the thread pools; UV_HTTP_* harden the (large) torch CPU wheel download.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_HTTP_TIMEOUT=120 \
    UV_HTTP_RETRIES=5 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HOME=/tmp/xninetzy-home \
    CUDA_VISIBLE_DEVICES="" \
    NVIDIA_VISIBLE_DEVICES=void \
    XNINETZY_DEVICE=cpu \
    EMBEDDING_DEVICE=cpu \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4 \
    TORCH_NUM_THREADS=4

WORKDIR /app

# System deps: Chromium for Playwright + PDF/OCR libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright Chromium dependencies
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 libwayland-client0 \
    # Build tools + OCR runtime (English and Indonesian)
    build-essential tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind \
    && rm -rf /var/lib/apt/lists/*

# Dependency layer first (before COPY app) so source edits don't bust the cache.
# --frozen: install exactly the CPU-only lock, never re-resolve to a CUDA build.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev

# Install Playwright browser binaries (Chromium only)
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv run --no-dev playwright install chromium \
    && mkdir -p /app/data/hebat/downloads /app/data/hebat/browser-profiles \
        /app/data/wa-media /app/data/backups \
        /app/data/opencode-config/opencode/skills \
        /app/data/codex-config /app/data/claude-config \
        /tmp/xninetzy-home /tmp/uv-cache \
    && chmod -R a+rX /ms-playwright \
    && chmod -R a+rwX /app/data /tmp/xninetzy-home /tmp/uv-cache
COPY app ./app
COPY scripts ./scripts
COPY .agents ./.agents

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
