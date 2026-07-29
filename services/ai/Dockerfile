FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    UV_CACHE_DIR=/tmp/uv-cache \
    HOME=/tmp/xninetzy-home

WORKDIR /app

# System deps: Chromium for Playwright + PDF libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright Chromium dependencies
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 libwayland-client0 \
    # Build tools + OCR runtime (English and Indonesian)
    build-essential tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

# Install Playwright browser binaries (Chromium only)
RUN uv run --no-dev playwright install chromium \
    && mkdir -p /app/data/hebat/downloads /app/data/hebat/browser-profiles \
        /app/data/wa-media /app/data/backups /tmp/xninetzy-home /tmp/uv-cache \
    && chmod -R a+rX /ms-playwright \
    && chmod -R a+rwX /app/data /tmp/xninetzy-home /tmp/uv-cache
COPY app ./app
COPY scripts ./scripts

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
