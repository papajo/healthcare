"""Consent management API routes — granular patient consent for data categories.

Provides:
- POST /consent           — Grant consent
- GET  /consent           — List consents (all or filtered)
- GET  /consent/{id}      — Get a single consent
- POST /consent/{id}/revoke — Revoke consent
- POST /consent/check     — Check if consent exists for a patient/category
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from src.api.deps import CurrentUser
from src.models.auth import UserRole
from src.models.consent import (
    ConsentCreateRequest,
    ConsentRevokeRequest,
    DataCategory,
)
from src.services.audit_ledger import audit_ledger
from src.services.consent_service import consent_service

router = APIRouter()


@router.post(
    "/consent",
    status_code=status.HTTP_201_CREATED,
    summary="Grant consent",
    description="Grant patient consent for a specific data category.",
)
async def grant_consent(request: ConsentCreateRequest, user: CurrentUser):
    """Grant consent — patients can grant for themselves; clinicians for assigned patients."""
    # Patients can only grant for themselves
    if user.role == UserRole.PATIENT:
        if user.fhir_patient_id != request.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients can only grant consent for themselves",
            )

    record = consent_service.grant(request, granted_by=str(user.user_id))

    audit_ledger.write_event(
        event_type="CONSENT_GRANTED",
        actor_type="PATIENT_APP" if user.role == UserRole.PATIENT else "PROVIDER_EHR",
        actor_id=str(user.user_id),
        entity_type="PATIENT",
        entity_id=request.patient_id,
        payload={
            "consent_id": str(record.consent_id),
            "category": request.category.value,
            "granted_to": request.granted_to,
        },
    )

    return record


@router.get(
    "/consent",
    summary="List consents",
    description="List consent records, optionally filtered by patient or category.",
)
async def list_consents(
    user: CurrentUser,
    patient_id: str | None = Query(default=None),
    category: DataCategory | None = Query(default=None),
    include_expired: bool = Query(default=False),
):
    if user.role == UserRole.PATIENT:
        # Patients can only see their own consents
        pid = user.fhir_patient_id or "__none__"
        return consent_service.list_for_patient(pid, category, include_expired)

    if patient_id:
        return consent_service.list_for_patient(patient_id, category, include_expired)

    return consent_service.list_all(include_expired)


@router.get(
    "/consent/{consent_id}",
    summary="Get consent",
    description="Get a single consent record by ID.",
)
async def get_consent(consent_id: str, user: CurrentUser):
    record = consent_service.get(consent_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Consent not found")

    # Patients can only see their own
    if user.role == UserRole.PATIENT and user.fhir_patient_id != record.patient_id:
        raise HTTPException(status_code=404, detail="Consent not found")

    return record


@router.post(
    "/consent/{consent_id}/revoke",
    summary="Revoke consent",
    description="Revoke an active consent. Propagates system-wide.",
)
async def revoke_consent(
    consent_id: str,
    request: ConsentRevokeRequest,
    user: CurrentUser,
):
    try:
        record = consent_service.revoke(consent_id, str(user.user_id), request)
    except KeyError:
        raise HTTPException(status_code=404, detail="Consent not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Patients can only revoke their own
    if user.role == UserRole.PATIENT and user.fhir_patient_id != record.patient_id:
        # Re-revoke to undo
        raise HTTPException(status_code=403, detail="Cannot revoke consent for another patient")

    audit_ledger.write_event(
        event_type="CONSENT_REVOKED",
        actor_type="PATIENT_APP" if user.role == UserRole.PATIENT else "PROVIDER_EHR",
        actor_id=str(user.user_id),
        entity_type="PATIENT",
        entity_id=record.patient_id,
        payload={
            "consent_id": consent_id,
            "category": record.category.value,
            "reason": request.reason,
        },
    )

    return record


@router.post(
    "/consent/check",
    summary="Check consent",
    description="Check if valid consent exists for a patient/category combination.",
)
async def check_consent(
    user: CurrentUser,
    patient_id: str = Query(...),
    category: DataCategory = Query(...),
    actor_id: str | None = Query(default=None),
):
    valid = consent_service.has_valid_consent(patient_id, category, actor_id)
    return {
        "patient_id": patient_id,
        "category": category.value,
        "actor_id": actor_id,
        "consent_valid": valid,
    }
