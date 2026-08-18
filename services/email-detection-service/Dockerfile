FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /src

COPY --from=ai_platform pyproject.toml pyproject.toml
COPY --from=ai_platform uv.lock uv.lock
RUN uv sync --package email-detection-service --frozen --no-cache

RUN uv pip install --upgrade huggingface_hub
RUN --mount=type=cache,target=/model/.cache/huggingface \
    /src/.venv/bin/hf download onnx-community/phishing-email-detection-distilbert_v2.4.1-ONNX --local-dir ./model

FROM python:3.13-slim AS runner

WORKDIR /src

COPY --from=builder /src/.venv .venv
COPY --from=builder /src/model model

COPY ./app app

EXPOSE 6000

CMD ["/src/.venv/bin/fastapi", "run", "/src/app/main.py", "--host", "0.0.0.0", "--port", "6000"]