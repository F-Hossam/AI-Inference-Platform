from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from app.dependencies import CurrentUser, DatabaseSession
from app.models import UserRecord
from app.schemas import LoginRequest, SignupRequest, UserResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    payload: SignupRequest,
    response: Response,
    session: DatabaseSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserRecord:
    email = str(payload.email).lower()
    existing_user = await session.scalar(
        select(UserRecord).where(func.lower(UserRecord.email) == email)
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = UserRecord(
        email=email,
        name=payload.name,
        password_hash=await run_in_threadpool(hash_password, payload.password),
        role="user",
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from error

    await session.refresh(user)
    set_session_cookie(response, create_access_token(user.id, settings), settings)
    return user


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    session: DatabaseSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserRecord:
    email = str(payload.email).lower()
    user = await session.scalar(
        select(UserRecord).where(func.lower(UserRecord.email) == email)
    )
    password_is_valid = user is not None and await run_in_threadpool(
        verify_password,
        payload.password,
        user.password_hash,
    )
    if not password_is_valid or user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    set_session_cookie(response, create_access_token(user.id, settings), settings)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path="/",
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser) -> UserRecord:
    return user
