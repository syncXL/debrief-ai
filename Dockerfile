FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libxml2-dev \
    libxslt-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --python /usr/local/bin/python3.13

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uv run --python /usr/local/bin/python3.13 uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]