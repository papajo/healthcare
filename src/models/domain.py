"""Core domain models for the Crisis-Cost Orchestrator."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# ─── Enums ────────────────────────────────────────────────────────────────────


class UrgencyLabel(str, Enum):
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"


class EncounterClass(str, Enum):
    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    OBSERVATION = "OBSERVATION"
    OUTPATIENT = "OUTPATIENT"
    INPATIENT = "INPATIENT"


class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    CONDITIONALLY_ELIGIBLE = "CONDITIONALLY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    NOT_VERIFIED = "NOT_VERIFIED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class RevocationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"


class VerificationAssuranceLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class AffordabilityTier(str, Enum):
    TIER_CRITICAL = "TIER-CRITICAL"
    TIER_LOW = "TIER-LOW"
    TIER_STANDARD = "TIER-STANDARD"
    TIER_MODERATE = "TIER-MODERATE"
    TIER_UNVERIFIED = "TIER-UNVERIFIED"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class SubsidyStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, Enum):
    ACH = "ACH"
    WIRE = "WIRE"
    STABLECOIN = "STABLECOIN"


class AuditEventType(str, Enum):
    ENCOUNTER_INGESTED = "ENCOUNTER_INGESTED"
    URGENCY_CLASSIFIED = "URGENCY_CLASSIFIED"
    ELIGIBILITY_PROOF_INGESTED = "ELIGIBILITY_PROOF_INGESTED"
    ELIGIBILITY_PROOF_VERIFIED = "ELIGIBILITY_PROOF_VERIFIED"
    ELIGIBILITY_PROOF_EXPIRED = "ELIGIBILITY_PROOF_EXPIRED"
    ELIGIBILITY_PROOF_REVOKED = "ELIGIBILITY_PROOF_REVOKED"
    AFFORDABILITY_DECISION_COMPUTED = "AFFORDABILITY_DECISION_COMPUTED"
    SUBSIDY_CREATED = "SUBSIDY_CREATED"
    SUBSIDY_PAYMENT_INITIATED = "SUBSIDY_PAYMENT_INITIATED"
    SUBSIDY_SETTLED = "SUBSIDY_SETTLED"
    SUBSIDY_FAILED = "SUBSIDY_FAILED"
    SUBSIDY_CANCELLED = "SUBSIDY_CANCELLED"
    BREAK_GLASS_ACCESS_GRANTED = "BREAK_GLASS_ACCESS_GRANTED"
    KEY_ROTATED = "KEY_ROTATED"
    RETENTION_PURGE_EXECUTED = "RETENTION_PURGE_EXECUTED"
    LEDGER_DIGEST_VERIFIED = "LEDGER_DIGEST_VERIFIED"


class ActorType(str, Enum):
    SYSTEM = "SYSTEM"
    PROVIDER_EHR = "PROVIDER_EHR"
    PATIENT_APP = "PATIENT_APP"
    VERIFICATION_PROVIDER = "VERIFICATION_PROVIDER"
    OPERATOR = "OPERATOR"
    AUDIT_SYSTEM = "AUDIT_SYSTEM"


class EntityType(str, Enum):
    ENCOUNTER = "ENCOUNTER"
    ELIGIBILITY_PROOF = "ELIGIBILITY_PROOF"
    AFFORDABILITY_DECISION = "AFFORDABILITY_DECISION"
    SUBSIDY = "SUBSIDY"
    SYSTEM = "SYSTEM"


# ─── Eligibility Proof (reduced, from verification provider) ─────────────────


class EligibilityProof(BaseModel):
    """Reduced eligibility proof for affordability calculation.
    
    The core platform never handles raw financial evidence.
    This contains only the minimum attributes needed for decisioning.
    """

    proof_id: UUID
    income_bracket_code: str = Field(pattern=r"^IB-[A-Z0-9][A-Z0-9-]{0,15}$")
    affordability_tier: str = Field(pattern=r"^TIER-[A-Z0-9][A-Z0-9-]{0,23}$")
    eligibility_status_normalized: EligibilityStatus
    verification_assurance_level: VerificationAssuranceLevel
    proof_valid_from: datetime
    proof_valid_to: datetime
    revocation_status: RevocationStatus
    patient_pseudo_id: UUID


# ─── Affordability Engine ────────────────────────────────────────────────────


class AffordabilityCalculationRequest(BaseModel):
    """Request to calculate patient affordability cap."""

    request_id: UUID = Field(default_factory=uuid4)
    encounter_id: str = Field(max_length=64)
    patient_pseudo_id: UUID
    urgency_label: UrgencyLabel
    estimated_total_cents: int = Field(ge=0)
    encounter_class: EncounterClass
    eligibility_proof: EligibilityProof | None = None
    household_size_band: str | None = Field(default=None, pattern=r"^HS-[A-Z0-9][A-Z0-9-]{0,15}$")


class AffordabilityCalculationResponse(BaseModel):
    """Result of affordability cap calculation."""

    request_id: UUID
    affordability_cap_cents: int = Field(ge=0)
    patient_responsibility_cents: int = Field(ge=0)
    subsidy_amount_cents: int = Field(ge=0)
    cap_rule_applied: str
    tier_applied: AffordabilityTier
    urgency_override_applied: bool
    confidence_level: ConfidenceLevel
    computed_at: datetime


# ─── Subsidy ─────────────────────────────────────────────────────────────────


class SubsidyCreationRequest(BaseModel):
    """Request to create a subsidy record."""

    encounter_id: str
    patient_pseudo_id: UUID
    provider_org_id: UUID
    proof_id: UUID | None = None
    urgency_label: UrgencyLabel | None = None
    estimated_total_cents: int | None = None
    affordability_cap_cents: int | None = None
    patient_responsibility_cents: int | None = None
    subsidy_amount_cents: int
    tier_applied: str | None = None


class SubsidyResponse(BaseModel):
    """Subsidy record response."""

    subsidy_id: UUID = Field(default_factory=uuid4)
    encounter_id: str
    patient_pseudo_id: UUID
    provider_org_id: UUID
    subsidy_amount_cents: int
    subsidy_status: SubsidyStatus
    payment_method: PaymentMethod | None = None
    payment_reference: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    settled_at: datetime | None = None


# ─── Audit Event ─────────────────────────────────────────────────────────────


class AuditActor(BaseModel):
    actor_type: ActorType
    actor_id: str = Field(max_length=128)


class AuditEntity(BaseModel):
    entity_type: EntityType
    entity_id: str = Field(max_length=128)


class AuditEvent(BaseModel):
    """Immutable audit event for the compliance ledger."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: AuditEventType
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: AuditActor
    entity: AuditEntity
    payload: dict = Field(default_factory=dict)
    correlation_id: UUID | None = None
    schema_version: str = "1.0.0"
    integrity_hash: str = ""
