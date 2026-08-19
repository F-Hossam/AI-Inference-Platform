from collections.abc import AsyncIterator
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from starlette.background import BackgroundTask

from app.config import Settings, get_settings
from app.dependencies import CurrentUser, DatabaseSession
from app.models import InferenceRequestRecord, ModelRecord
from app.schemas import InferenceRequest, PositiveId

router = APIRouter(prefix="/api/v1/models", tags=["inference"])


async def close_upstream(response: httpx.Response, client: httpx.AsyncClient) -> None:
    await response.aclose()
    await client.aclose()


async def stop_on_disconnect(
    request: Request,
    upstream: httpx.Response,
) -> AsyncIterator[bytes]:
    async for chunk in upstream.aiter_raw():
        if await request.is_disconnected():
            break
        yield chunk


#invoke the selected model
@router.post("/{model_id}/invoke")
async def invoke_model(
    model_id: PositiveId,
    payload: InferenceRequest,
    request: Request,
    user: CurrentUser,
    session: DatabaseSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> StreamingResponse:
    statement = (
        select(ModelRecord)
        .options(joinedload(ModelRecord.use_case))
        .where(ModelRecord.id == model_id)
    )
    model = await session.scalar(statement)

    is_visible = model is not None and (
        user.role == "tester" or (model.is_active and model.use_case.is_ready)
    )
    if not is_visible:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )

    session.add(InferenceRequestRecord(user_id=user.id, model_id=model.id))
    await session.commit()

    timeout = httpx.Timeout(
        timeout=settings.inference_timeout_seconds,
        connect=settings.connect_timeout_seconds,
    )
    client = httpx.AsyncClient(timeout=timeout)
    upstream_request = client.build_request(
        "POST",
        model.service_url,
        json=payload.input,
    )

    try:
        upstream = await client.send(upstream_request, stream=True)
    except httpx.HTTPError as error:
        await client.aclose()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Model service is unavailable",
        ) from error

    response_headers: dict[str, str] = {}
    content_type = upstream.headers.get("content-type")
    if content_type is not None:
        response_headers["content-type"] = content_type

    return StreamingResponse(
        stop_on_disconnect(request, upstream),
        status_code=upstream.status_code,
        headers=response_headers,
        background=BackgroundTask(close_upstream, upstream, client),
    )
