"""FastAPI dependencies for authentication, authorization, and consent validation."""

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


# ─── Data-scoping dependency ─────────────────────────────────────────────────


def _visible_patient_ids(user: AuthUserResponse) -> list[str] | None:
    """Return the list of FHIR Patient IDs the user may access.

    * ``None``  → unbounded access (admin / system / nurse)
    * ``[...]`` → exactly these patient IDs (doctor or patient)
    """
    if user.role in (UserRole.ADMIN, UserRole.SYSTEM, UserRole.NURSE):
        return None  # full access

    if user.role == UserRole.PATIENT:
        if user.fhir_patient_id:
            return [user.fhir_patient_id]
        return []  # no linked patient → no access

    if user.role == UserRole.CLINICIAN:
        return user.assigned_patient_ids or []

    return []  # unknown role → no access


class PatientScope:
    """Injected dependency carrying the current user and their visible patient IDs.

    ``patient_ids is None`` means unbounded (admin/system/nurse).
    ``patient_ids is [...]`` means scoped to those IDs.
    """

    def __init__(
        self,
        user: AuthUserResponse,
        patient_ids: list[str] | None,
    ) -> None:
        self.user = user
        self.patient_ids = patient_ids

    def can_access(self, fhir_patient_id: str) -> bool:
        """Check if the user may access a specific patient."""
        if self.patient_ids is None:
            return True
        return fhir_patient_id in self.patient_ids


async def get_patient_scope(user: CurrentUser) -> PatientScope:
    """Build a PatientScope for the current user."""
    return PatientScope(
        user=user,
        patient_ids=_visible_patient_ids(user),
    )


PatientScopeDep = Annotated[PatientScope, Depends(get_patient_scope)]


# ─── Consent validation dependency ─────────────────────────────────────────


def require_consent(*categories: str):
    """Dependency factory: raises 403 if the patient lacks consent for the given data categories.

    Usage in routes::

        @router.post(
            "/some-endpoint",
            dependencies=[Depends(require_consent("CLINICAL", "FINANCIAL"))],
        )
        async def endpoint(patient_id: str, scope: PatientScopeDep):
            ...
    """

    async def _check(
        patient_id: str,
        scope: PatientScopeDep,
    ) -> PatientScope:
        from src.models.consent import DataCategory
        from src.services.consent_service import consent_service

        actor_id = scope.user.user_id
        for cat_str in categories:
            try:
                cat = DataCategory(cat_str)
            except ValueError:
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid consent category: {cat_str}",
                )
            if not consent_service.has_valid_consent(patient_id, cat, actor_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing consent for category: {cat.value}",
                )
        return scope

    return _check
