"""Affordability Engine API routes — F-02."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import require_role
from src.models.auth import UserRole
from src.models.domain import (
    ActorType,
    AffordabilityCalculationRequest,
    AffordabilityCalculationResponse,
    AuditEventType,
    EntityType,
)
from src.services.affordability_engine import calculate_affordability
from src.services.audit_ledger import audit_ledger

router = APIRouter()


@router.post(
    "/affordability/calculate",
    response_model=AffordabilityCalculationResponse,
    summary="Calculate patient affordability cap",
    description="Deterministic calculation of the maximum out-of-pocket cost.",
    dependencies=[Depends(require_role(UserRole.CLINICIAN, UserRole.NURSE, UserRole.ADMIN))],
)
async def calculate(request: AffordabilityCalculationRequest):
    """Calculate the patient's affordability cap."""
    try:
        result = calculate_affordability(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Emit audit event
    audit_ledger.write_event(
        event_type=AuditEventType.AFFORDABILITY_DECISION_COMPUTED,
        actor_type=ActorType.SYSTEM,
        actor_id="affordability-engine",
        entity_type=EntityType.AFFORDABILITY_DECISION,
        entity_id=str(request.request_id),
        payload={
            "patient_pseudo_id": str(request.patient_pseudo_id),
            "encounter_id": request.encounter_id,
            "estimated_total_cents": request.estimated_total_cents,
            "patient_responsibility_cents": result.patient_responsibility_cents,
            "subsidy_amount_cents": result.subsidy_amount_cents,
            "tier_applied": result.tier_applied.value,
        },
    )

    return result
