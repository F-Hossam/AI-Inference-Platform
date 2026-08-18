up:
	docker compose up --build

down:
	docker compose down

database: 
	docker compose --env-file ./ai-inference-platform/database/.env.local up -d

vllm-runtime:
	docker run --runtime=nvidia --gpus all --name=nvidia -v ./ai-inference-platform/services/vllm-service/vllm/model:/runtime/model vllm-runtime

# gateway:
# 	uv run --project api-gateway uvicorn app.main:app --reload

# registry:
# 	uv run --project model-registry uvicorn app.main:app --reload

# controller:
# 	uv run --project inference-controller uvicorn app.main:app --reload