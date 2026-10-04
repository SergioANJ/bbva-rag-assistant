FROM python:3.12-slim

# uv, copiado de su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# 1. Dependencias primero: esta capa se reutiliza mientras que uv.lock no cambia.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2. Código del proyecto y el corpus limpio versionado
COPY README.md ./
COPY src ./src
COPY data/clean ./data/clean
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"