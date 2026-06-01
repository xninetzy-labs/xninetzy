FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# System deps: Chromium for Playwright + PDF libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright Chromium dependencies
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 libwayland-client0 \
    # Build tools
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

# Install Playwright browser binaries (Chromium only)
RUN uv run playwright install chromium

COPY app ./app

# Create data directories
RUN mkdir -p /app/data/hebat/downloads /app/data/hebat/browser-profiles /app/data/wa-media

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
