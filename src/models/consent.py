"""Consent management models — granular patient consent for data categories."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ConsentStatus(StrEnum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class DataCategory(StrEnum):
    """Granular data categories patients can consent to."""

    CLINICAL = "CLINICAL"
    FINANCIAL = "FINANCIAL"
    PHARMACY = "PHARMACY"
    LAB_RESULTS = "LAB_RESULTS"
    IMAGING = "IMAGING"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    SUBSTANCE_USE = "SUBSTANCE_USE"


class ConsentRecord(BaseModel):
    """A single consent grant or revocation."""

    consent_id: UUID = Field(default_factory=uuid4)
    patient_id: str = Field(max_length=128, description="FHIR Patient ID")
    category: DataCategory
    status: ConsentStatus = ConsentStatus.VALID
    granted_to: list[str] = Field(
        default_factory=list,
        description="Actor IDs this consent grants access to. Empty = system-wide.",
    )
    granted_by: str = Field(max_length=128, description="User ID who granted consent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    scope_note: str | None = Field(default=None, max_length=512)


class ConsentCreateRequest(BaseModel):
    """Request to grant consent for a data category."""

    patient_id: str = Field(max_length=128)
    category: DataCategory
    granted_to: list[str] = Field(
        default_factory=list,
        description="Actor IDs this consent grants access to. Empty = system-wide.",
    )
    expires_at: datetime | None = None
    scope_note: str | None = Field(default=None, max_length=512)


class ConsentRevokeRequest(BaseModel):
    """Request to revoke consent."""

    reason: str | None = Field(default=None, max_length=512)
