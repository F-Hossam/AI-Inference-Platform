from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from transformers import AutoTokenizer

TOKENIZER_PATH = Path("./model/tokenizer.json")
MODEL_PATH = Path("./model/onnx/model_fp16.onnx")
LABELS = {
    0: "legitimate_email",
    1: "phishing_email",
    2: "legitimate_url",
    3: "phishing_url",
}


class PhishingRequest(BaseModel):
    content: str = Field(min_length=1, max_length=512)


class PhishingResponse(BaseModel):
    prediction: str
    confidence: float = Field(ge=0, le=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.tokenizer = AutoTokenizer.from_pretrained(
        TOKENIZER_PATH,
        local_files_only=True,
    )

    app.state.session = ort.InferenceSession(
        path_or_bytes=MODEL_PATH,
        providers=['CPUExecutionProvider'],
    )

    yield

    app.state.session = None
    app.state.tokenizer = None


app = FastAPI(
    title="Email Detection Service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health(request: Request) -> dict[str, str]:
    if getattr(request.app.state, "session", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready",
        )

    return {"status": "ok"}


@app.post("/predict")
def predict(payload: PhishingRequest, request: Request) -> PhishingResponse:
    session: ort.InferenceSession = request.app.state.session
    tokenizer = request.app.state.tokenizer

    tokenized = tokenizer(
        payload.content,
        return_tensors="np",
        truncation=True,
        max_length=512,
    )
    inputs = {
        "input_ids": tokenized["input_ids"],
        "attention_mask": tokenized["attention_mask"],
    }

    logits = session.run(None, inputs)[0][0]
    shifted_logits = logits - np.max(logits)
    probabilities = np.exp(shifted_logits)
    probabilities /= np.sum(probabilities)

    label_id = int(np.argmax(probabilities))
    return PhishingResponse(
        prediction=LABELS[label_id],
        confidence=float(probabilities[label_id]),
    )
