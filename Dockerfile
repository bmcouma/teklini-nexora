FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir ".[postgres]"

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "nexora.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
