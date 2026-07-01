"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.models.auth import Scope, UserRole
from src.models.auth import UserResponse as AuthUserResponse
from src.services.auth_service import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)

TokenDep = Annotated[str | None, Depends(oauth2_scheme)]


async def get_current_user(token: TokenDep) -> AuthUserResponse:
    """Decode JWT and return user. Raises 401 if invalid or missing."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return auth_service.get_current_user(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


CurrentUser = Annotated[AuthUserResponse, Depends(get_current_user)]


async def optional_user(token: TokenDep) -> AuthUserResponse | None:
    """Decode JWT if present, return None if not."""
    if token is None:
        return None
    try:
        return auth_service.get_current_user(token)
    except ValueError:
        return None


OptionalUser = Annotated[AuthUserResponse | None, Depends(optional_user)]


def require_role(*roles: UserRole):
    """Dependency factory: raises 403 if user role not in *roles*."""

    async def _check(user: CurrentUser) -> AuthUserResponse:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(r.value for r in roles)}",
            )
        return user

    return _check


def require_scope(required_scope: Scope):
    """Dependency factory: raises 403 if token lacks *required_scope*."""

    async def _check(
        token: Annotated[str | None, Depends(oauth2_scheme)],
        user: CurrentUser,
    ) -> AuthUserResponse:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        if not auth_service.verify_scope(token, required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing scope: {required_scope.value}",
            )
        return user

    return _check
