from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DatabaseSession
from app.models import ModelRecord, UseCaseRecord
from app.schemas import ModelResponse, PositiveId, UseCaseResponse

router = APIRouter(prefix="/api/v1", tags=["catalog"])


#list all use-cases
@router.get("/use-cases", response_model=list[UseCaseResponse])
async def list_use_cases(
    user: CurrentUser,
    session: DatabaseSession,
) -> list[UseCaseRecord]:
    statement = select(UseCaseRecord).order_by(UseCaseRecord.name)
    if user.role != "tester":
        statement = statement.where(UseCaseRecord.is_ready.is_(True))

    result = await session.scalars(statement)
    return list(result)


#list the models for a specific use-case
@router.get(
    "/use-cases/{use_case_id}/models",
    response_model=list[ModelResponse],
)
async def list_models(
    use_case_id: PositiveId,
    user: CurrentUser,
    session: DatabaseSession,
) -> list[ModelRecord]:
    use_case = await session.get(UseCaseRecord, use_case_id)
    if use_case is None or (user.role != "tester" and not use_case.is_ready):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found",
        )

    statement = (
        select(ModelRecord)
        .where(ModelRecord.use_case_id == use_case_id)
        .order_by(ModelRecord.name)
    )
    if user.role != "tester":
        statement = statement.where(ModelRecord.is_active.is_(True))

    result = await session.scalars(statement)
    return list(result)
