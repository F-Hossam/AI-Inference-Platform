up:
    docker compose up --build

down:
    docker compose down

# gateway:
#     uv run --project api-gateway uvicorn app.main:app --reload

# registry:
#     uv run --project model-registry uvicorn app.main:app --reload

# controller:
#     uv run --project inference-controller uvicorn app.main:app --reload