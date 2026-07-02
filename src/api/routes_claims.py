"""Claims API routes — CRUD + lifecycle management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import CurrentUser, require_role
from src.models.auth import UserRole
from src.models.domain import (
    ActorType,
    AuditEventType,
    ClaimCreateRequest,
    ClaimStatusUpdate,
    EntityType,
)
from src.services.audit_ledger import audit_ledger
from src.services.claims_service import claim_store

router = APIRouter()


@router.post(
    "/claims",
    summary="Create a new claim",
    description="Submit a new healthcare claim with line items and diagnosis codes.",
    dependencies=[Depends(require_role(UserRole.CLINICIAN, UserRole.NURSE, UserRole.ADMIN))],
)
async def create_claim(request: ClaimCreateRequest, user: CurrentUser):
    """Create a new claim."""
    claim = claim_store.create_claim(request)

    audit_ledger.write_event(
        event_type=AuditEventType.SUBSIDY_CREATED,  # reuse for claim events
        actor_type=ActorType.PROVIDER_EHR,
        actor_id=str(request.provider_org_id),
        entity_type=EntityType.SUBSIDY,  # reuse entity type
        entity_id=str(claim.claim_id),
        payload={
            "action": "CLAIM_CREATED",
            "encounter_id": request.encounter_id,
            "total_charged_cents": claim.total_charged_cents,
            "payer_id": request.payer_id,
        },
    )

    return claim


@router.get(
    "/claims",
    summary="List claims",
    description="List claims with optional filters for patient, provider, or status.",
    dependencies=[Depends(require_role(UserRole.CLINICIAN, UserRole.NURSE, UserRole.ADMIN))],
)
async def list_claims(
    patient_pseudo_id: str | None = Query(default=None),
    provider_org_id: str | None = Query(default=None),
    claim_status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List claims with filters."""
    claims, total = claim_store.list_claims(
        patient_pseudo_id=patient_pseudo_id,
        provider_org_id=provider_org_id,
        claim_status=claim_status,
        limit=limit,
        offset=offset,
    )
    return {"total": total, "claims": claims}


@router.get(
    "/claims/summary",
    summary="Claim statistics",
    description="Get aggregate claim statistics (totals by status, amounts).",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def get_claim_summary():
    """Get claim summary statistics."""
    return claim_store.get_summary()


@router.get(
    "/claims/{claim_id}",
    summary="Get claim details",
    description="Retrieve a single claim by ID.",
    dependencies=[Depends(require_role(UserRole.CLINICIAN, UserRole.NURSE, UserRole.ADMIN))],
)
async def get_claim(claim_id: str):
    """Get a claim by ID."""
    claim = claim_store.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    return claim


@router.post(
    "/claims/{claim_id}/submit",
    summary="Submit claim for review",
    description="Move a draft claim to SUBMITTED status.",
    dependencies=[Depends(require_role(UserRole.CLINICIAN, UserRole.NURSE, UserRole.ADMIN))],
)
async def submit_claim(claim_id: str):
    """Submit a claim."""
    claim = claim_store.submit_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    return claim


@router.patch(
    "/claims/{claim_id}/status",
    summary="Update claim status",
    description="Update claim status with optional financial adjustments.",
    dependencies=[Depends(require_role(UserRole.CLINICIAN, UserRole.NURSE, UserRole.ADMIN))],
)
async def update_claim_status(claim_id: str, update: ClaimStatusUpdate):
    """Update claim status."""
    claim = claim_store.update_status(claim_id, update)
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

    audit_ledger.write_event(
        event_type=AuditEventType.SUBSIDY_SETTLED,  # reuse for claim events
        actor_type=ActorType.SYSTEM,
        actor_id="claims-service",
        entity_type=EntityType.SUBSIDY,
        entity_id=claim_id,
        payload={
            "action": "CLAIM_STATUS_UPDATED",
            "new_status": update.claim_status.value,
            "insurance_cents": claim.insurance_responsibility_cents,
            "patient_cents": claim.patient_responsibility_cents,
        },
    )

    return claim


@router.post(
    "/claims/{claim_id}/settle",
    summary="Settle claim",
    description="Mark a claim as settled (payment received).",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def settle_claim(claim_id: str):
    """Settle a claim."""
    claim = claim_store.settle_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    return claim


@router.post(
    "/claims/{claim_id}/void",
    summary="Void claim",
    description="Void a claim (cancel before settlement).",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def void_claim(claim_id: str):
    """Void a claim."""
    claim = claim_store.void_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    return claim
