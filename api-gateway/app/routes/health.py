from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import DatabaseSession

router = APIRouter(tags=["health"])


#server is healthy
@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


#connection to DB is ready
@router.get("/health/ready")
async def readiness(session: DatabaseSession) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from error

    return {"status": "ready"}
