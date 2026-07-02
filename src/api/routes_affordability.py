"""Affordability Engine API routes — F-02."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import PatientScopeDep, require_role
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


@router.get(
    "/affordability/{patient_id}",
    summary="Get patient affordability assessment",
    description="Retrieve the latest affordability assessment for a patient.",
)
async def get_patient_affordability(
    patient_id: str,
    scope: PatientScopeDep,
):
    """Get affordability for a specific patient."""
    if not scope.can_access(patient_id):
        raise HTTPException(status_code=403, detail="Access denied to this patient")

    # Search for the most recent affordability calculation in audit events
    from src.models.domain import AuditEventType

    events, total = audit_ledger.query_events(
        event_type=AuditEventType.AFFORDABILITY_DECISION_COMPUTED,
        entity_id=None,
        limit=100,
    )

    # Find events for this patient
    patient_events = [
        e for e in events
        if e.payload.get("patient_pseudo_id") == patient_id
    ]

    if not patient_events:
        raise HTTPException(
            status_code=404,
            detail=f"No affordability assessment found for patient {patient_id}",
        )

    # Return the most recent
    latest = patient_events[-1]
    return {
        "patient_id": patient_id,
        "assessment": latest.payload,
        "computed_at": latest.event_timestamp.isoformat(),
    }
