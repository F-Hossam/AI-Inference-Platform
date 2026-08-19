from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_session
from app.models import UserRecord
from app.security import decode_access_token

DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    session: DatabaseSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(http_bearer),
    ] = None,
) -> UserRecord:
    token = (
        credentials.credentials
        if credentials is not None
        else request.cookies.get(settings.auth_cookie_name)
    )
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token, settings)
        user_id = int(str(payload["sub"]))
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    user = await session.get(UserRecord, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


CurrentUser = Annotated[UserRecord, Depends(get_current_user)]
