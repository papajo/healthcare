"""Auth models for SMART on FHIR OAuth2 authorization."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

# ─── Enums ────────────────────────────────────────────────────────────────────


class UserRole(str, Enum):
    CLINICIAN = "CLINICIAN"
    NURSE = "NURSE"
    ADMIN = "ADMIN"
    PATIENT = "PATIENT"
    SYSTEM = "SYSTEM"


class Scope(str, Enum):
    """SMART on FHIR scopes."""

    PATIENT_READ = "patient/Patient.read"
    PATIENT_WRITE = "patient/Patient.write"
    ENCOUNTER_READ = "patient/Encounter.read"
    ENCOUNTER_WRITE = "patient/Encounter.write"
    OBSERVATION_READ = "patient/Observation.read"
    OBSERVATION_WRITE = "patient/Observation.write"
    MEDICATION_READ = "patient/MedicationRequest.read"
    MEDICATION_WRITE = "patient/MedicationRequest.write"
    USER_READ = "user/*.read"
    USER_ADMIN = "user/*.admin"
    SYSTEM_ACCESS = "system/*.access"
    LAUNCH = "launch"


# ─── Role → default scopes mapping ───────────────────────────────────────────

ROLE_SCOPES: dict[UserRole, list[Scope]] = {
    UserRole.CLINICIAN: [
        Scope.PATIENT_READ,
        Scope.PATIENT_WRITE,
        Scope.ENCOUNTER_READ,
        Scope.ENCOUNTER_WRITE,
        Scope.OBSERVATION_READ,
        Scope.OBSERVATION_WRITE,
        Scope.MEDICATION_READ,
        Scope.MEDICATION_WRITE,
        Scope.LAUNCH,
    ],
    UserRole.NURSE: [
        Scope.PATIENT_READ,
        Scope.ENCOUNTER_READ,
        Scope.OBSERVATION_READ,
        Scope.MEDICATION_READ,
        Scope.LAUNCH,
    ],
    UserRole.ADMIN: [
        Scope.USER_READ,
        Scope.USER_ADMIN,
        Scope.PATIENT_READ,
        Scope.ENCOUNTER_READ,
        Scope.OBSERVATION_READ,
        Scope.MEDICATION_READ,
        Scope.SYSTEM_ACCESS,
    ],
    UserRole.PATIENT: [
        Scope.PATIENT_READ,
        Scope.ENCOUNTER_READ,
        Scope.OBSERVATION_READ,
        Scope.MEDICATION_READ,
        Scope.LAUNCH,
    ],
    UserRole.SYSTEM: [
        Scope.SYSTEM_ACCESS,
        Scope.PATIENT_READ,
        Scope.PATIENT_WRITE,
        Scope.ENCOUNTER_READ,
        Scope.ENCOUNTER_WRITE,
        Scope.OBSERVATION_READ,
        Scope.OBSERVATION_WRITE,
        Scope.MEDICATION_READ,
        Scope.MEDICATION_WRITE,
    ],
}


# ─── Request/Response models ─────────────────────────────────────────────────


class UserCreate(BaseModel):
    """Request to create a new user."""

    username: str = Field(min_length=3, max_length=64)
    email: str = Field(max_length=256)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=128)
    role: UserRole = UserRole.CLINICIAN


class UserResponse(BaseModel):
    """User profile response."""

    user_id: UUID
    username: str
    email: str
    full_name: str
    role: UserRole
    created_at: datetime
    is_active: bool


class TokenResponse(BaseModel):
    """OAuth2 token pair response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    scope: str


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str
    role: UserRole
    scope: str
    exp: int
    iat: int
    iss: str = "crisiscost-orchestrator"


class LoginRequest(BaseModel):
    """Login credentials."""

    username: str
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


# ─── Internal record (not exposed via API) ───────────────────────────────────


class UserRecord(BaseModel):
    """Internal user record stored in memory."""

    user_id: UUID
    username: str
    email: str
    hashed_password: str
    full_name: str
    role: UserRole
    created_at: datetime
    is_active: bool = True
    refresh_token_jti: str | None = None
