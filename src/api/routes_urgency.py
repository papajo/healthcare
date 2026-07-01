"""F-01 Urgency Classifier API routes."""

from fastapi import APIRouter, HTTPException

from src.models.domain import ActorType, AuditEventType, EntityType
from src.models.f04_request import F04EncounterRequest
from src.services.audit_ledger import audit_ledger
from src.services.urgency_classifier import (
    ClassificationResult,
    UrgencyClassifier,
)

router = APIRouter()

# Singleton classifier
_classifier = UrgencyClassifier()


@router.post(
    "/urgency/classify",
    response_model=ClassificationResult,
    summary="Classify encounter urgency",
    description=(
        "Classifies an encounter into CRITICAL, URGENT, or ROUTINE urgency. "
        "Uses hybrid rule-based + LLM approach with <150ms p99 latency."
    ),
)
async def classify_urgency(request: F04EncounterRequest):
    """Classify encounter urgency level."""
    try:
        result = _classifier.classify(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}",
        )

    # Emit audit event
    audit_ledger.write_event(
        event_type=AuditEventType.URGENCY_CLASSIFIED,
        actor_type=ActorType.SYSTEM,
        actor_id=f"urgency-classifier-{result.classification_path}",
        entity_type=EntityType.ENCOUNTER,
        entity_id=request.encounter.encounter_id,
        payload={
            "patient_pseudo_id": str(request.patient.patient_pseudo_id),
            "urgency_label": result.urgency_label.value,
            "confidence": result.confidence,
            "triggered_evidence": result.triggered_evidence,
            "rationale_summary": result.rationale_summary,
            "classification_path": result.classification_path,
        },
    )

    return result
