FROM nvidia/cuda:13.3.1-cudnn-runtime-ubuntu26.04

WORKDIR /runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get install -y build-essential gcc g++ && \
    apt-get install -y nvidia-cuda-toolkit && \
    rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++
RUN uv python install 3.12

RUN uv venv
RUN uv pip install vllm --torch-backend=auto

COPY entrypoint.sh /runtime/entrypoint.sh
RUN chmod +x /runtime/entrypoint.sh

ENTRYPOINT ["/runtime/entrypoint.sh"]
