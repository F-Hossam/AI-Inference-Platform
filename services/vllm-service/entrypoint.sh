#!/bin/sh
set -e

echo "Serving LLM ...."

export VLLM_USE_FLASHINFER_SAMPLER=0
exec uv run vllm serve /runtime/model \
    --served-model-name llm \
    --port 5000 \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.85 \
    --no-enable-flashinfer-autotune