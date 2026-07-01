"""Auth routes — SMART on FHIR OAuth2 endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import CurrentUser, require_role
from src.models.auth import (
    LoginRequest,
    RefreshRequest,
    UserCreate,
    UserResponse,
    UserRole,
)
from src.services.auth_service import auth_service

router = APIRouter(prefix="/v1/auth", tags=["auth"])


# ─── Public endpoints ────────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(body: UserCreate):
    """Register a new user.

    Patients can self-register. Non-patient roles require admin privileges.
    """
    # Patient self-registration is open; other roles require admin
    if body.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patient self-registration is allowed. Use /users for admin creation.",
        )
    try:
        record = auth_service.register(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    return auth_service._to_response(record)


@router.post(
    "/login",
    summary="Authenticate and get token pair",
)
async def login(body: LoginRequest):
    """Authenticate with username/password and receive access + refresh tokens."""
    try:
        return auth_service.login(body.username, body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.post(
    "/refresh",
    summary="Refresh access token",
)
async def refresh(body: RefreshRequest):
    """Exchange a valid refresh token for a new token pair."""
    try:
        return auth_service.refresh_token(body.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


# ─── Authenticated endpoints ─────────────────────────────────────────────────


@router.post("/logout", summary="Logout (invalidate refresh token)")
async def logout(user: CurrentUser):
    """Invalidate the current user's refresh token."""
    auth_service.logout(str(user.user_id))
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def me(user: CurrentUser):
    """Return the authenticated user's profile."""
    return user


# ─── Admin endpoints ─────────────────────────────────────────────────────────


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: create user with any role",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def admin_create_user(body: UserCreate, _admin: CurrentUser):
    """Create a user with any role (admin only)."""
    try:
        record = auth_service.register(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    return auth_service._to_response(record)


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="Admin: list all users",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def admin_list_users(_admin: CurrentUser):
    """List all active users (admin only)."""
    return auth_service.list_users()


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Admin: deactivate user",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def admin_deactivate_user(user_id: str, _admin: CurrentUser):
    """Deactivate a user account (admin only)."""
    if not auth_service.deactivate_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
