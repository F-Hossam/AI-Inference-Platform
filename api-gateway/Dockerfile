FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /src

COPY --from=ai_platform pyproject.toml pyproject.toml
COPY --from=ai_platform uv.lock uv.lock
RUN uv sync --package api-gateway --frozen --no-cache

FROM python:3.13-slim AS runner

WORKDIR /src

COPY --from=builder /src/.venv .venv
COPY /app app

CMD ["/src/.venv/bin/fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]