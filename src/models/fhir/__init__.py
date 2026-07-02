"""FHIR R4 compliant Pydantic resource models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.models.fhir.types import (
    FHIRAddress,
    FHIRAllergyReaction,
    FHIRBundleEntry,
    FHIRClaimDiagnosis,
    FHIRClaimItem,
    FHIRCoding,
    FHIRContactPoint,
    FHIRDosageInstruction,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRMeta,
    FHIRMoney,
    FHIRPatientContact,
    FHIRPeriod,
    FHIRQuantity,
    FHIRReference,
    FHIRReferenceRange,
)

FHIR_VERSION = "4.0.1"

_MODEL_CONFIG = {"populate_by_name": True}


# ─── FHIR Patient ────────────────────────────────────────────────────────────


class FHIRPatient(BaseModel):
    """FHIR R4 Patient resource."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["Patient"] = Field(
        default="Patient",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    active: bool = True
    name: list[FHIRHumanName] = Field(default_factory=list)
    gender: str = "unknown"
    birthDate: date | None = None
    address: list[FHIRAddress] = Field(default_factory=list)
    telecom: list[FHIRContactPoint] = Field(default_factory=list)
    contact: list[FHIRPatientContact] = Field(default_factory=list)


# ─── FHIR Encounter ──────────────────────────────────────────────────────────


class FHIREncounterParticipant(BaseModel):
    """A participant in the encounter."""

    individual: FHIRReference | None = None
    type: list[FHIRCoding] = Field(default_factory=list)


class FHIREncounter(BaseModel):
    """FHIR R4 Encounter resource."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["Encounter"] = Field(
        default="Encounter",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    status: str = "planned"
    class_: FHIRCoding = Field(
        default_factory=lambda: FHIRCoding(
            system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
            code="IMP",
            display="inpatient encounter",
        ),
        serialization_alias="class",
    )
    type: list[FHIRCoding] = Field(default_factory=list)
    priority: FHIRCoding | None = None
    subject: FHIRReference = Field(default_factory=FHIRReference)
    participant: list[FHIREncounterParticipant] = Field(default_factory=list)
    period: FHIRPeriod = Field(default_factory=FHIRPeriod)
    reasonCode: list[FHIRCoding] = Field(default_factory=list)


# ─── FHIR Condition ──────────────────────────────────────────────────────────


class FHIRCondition(BaseModel):
    """FHIR R4 Condition resource."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["Condition"] = Field(
        default="Condition",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    clinicalStatus: FHIRCoding | None = None
    verificationStatus: FHIRCoding | None = None
    category: list[FHIRCoding] = Field(default_factory=list)
    code: FHIRCoding | None = None
    subject: FHIRReference = Field(default_factory=FHIRReference)
    onsetDateTime: datetime | None = None
    recordedDate: datetime | None = None


# ─── FHIR MedicationRequest ──────────────────────────────────────────────────


class FHIRMedicationRequest(BaseModel):
    """FHIR R4 MedicationRequest resource."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["MedicationRequest"] = Field(
        default="MedicationRequest",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    status: str = "active"
    intent: str = "order"
    medicationCodeableConcept: FHIRCoding | None = None
    subject: FHIRReference = Field(default_factory=FHIRReference)
    authoredOn: datetime | None = None
    requester: FHIRReference | None = None
    dosageInstruction: list[FHIRDosageInstruction] = Field(default_factory=list)


# ─── FHIR AllergyIntolerance ─────────────────────────────────────────────────


class FHIRAllergyIntolerance(BaseModel):
    """FHIR R4 AllergyIntolerance resource."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["AllergyIntolerance"] = Field(
        default="AllergyIntolerance",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    clinicalStatus: FHIRCoding | None = None
    verificationStatus: FHIRCoding | None = None
    type: str | None = None
    category: list[str] = Field(default_factory=list)
    criticality: str | None = None
    code: FHIRCoding | None = None
    patient: FHIRReference = Field(default_factory=FHIRReference)
    recordedDate: datetime | None = None
    reaction: list[FHIRAllergyReaction] = Field(default_factory=list)


# ─── FHIR Observation ────────────────────────────────────────────────────────


class FHIRObservation(BaseModel):
    """FHIR R4 Observation resource."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["Observation"] = Field(
        default="Observation",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    status: str = "final"
    category: list[FHIRCoding] = Field(default_factory=list)
    code: FHIRCoding = Field(default_factory=FHIRCoding)
    subject: FHIRReference = Field(default_factory=FHIRReference)
    effectiveDateTime: datetime | None = None
    valueQuantity: FHIRQuantity | None = None
    valueString: str | None = None
    interpretation: list[FHIRCoding] | None = None
    referenceRange: list[FHIRReferenceRange] | None = None


# ─── FHIR Claim ──────────────────────────────────────────────────────────────


class FHIRClaim(BaseModel):
    """FHIR R4 Claim resource."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["Claim"] = Field(
        default="Claim",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    status: str = "active"
    type: FHIRCoding | None = None
    patient: FHIRReference = Field(default_factory=FHIRReference)
    provider: FHIRReference = Field(default_factory=FHIRReference)
    billablePeriod: FHIRPeriod = Field(default_factory=FHIRPeriod)
    item: list[FHIRClaimItem] = Field(default_factory=list)
    total: FHIRMoney = Field(default_factory=FHIRMoney)
    diagnosis: list[FHIRClaimDiagnosis] = Field(default_factory=list)


# ─── FHIR Bundle ─────────────────────────────────────────────────────────────


class FHIRBundle(BaseModel):
    """FHIR R4 Bundle resource."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["Bundle"] = Field(
        default="Bundle",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    type: str = "searchset"
    total: int | None = None
    entry: list[FHIRBundleEntry] = Field(default_factory=list)


# ─── FHIR OperationOutcome ───────────────────────────────────────────────────


class FHIROperationOutcomeIssue(BaseModel):
    """Single issue in an OperationOutcome."""

    severity: str = "error"
    code: str = "invalid"
    details: FHIRCoding | None = None
    diagnostics: str | None = None


class FHIROperationOutcome(BaseModel):
    """FHIR R4 OperationOutcome resource."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["OperationOutcome"] = Field(
        default="OperationOutcome",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    issue: list[FHIROperationOutcomeIssue] = Field(default_factory=list)


# ─── FHIR Organization ───────────────────────────────────────────────────────


class FHIROrganizationContact(BaseModel):
    """Contact information for an organization."""

    purpose: FHIRCoding | None = None
    name: FHIRHumanName | None = None
    telecom: list[FHIRContactPoint] = Field(default_factory=list)
    address: FHIRAddress | None = None


class FHIROrganization(BaseModel):
    """FHIR R4 Organization resource — provider, hospital, or payer entity."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["Organization"] = Field(
        default="Organization",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    active: bool = True
    type: list[FHIRCoding] = Field(default_factory=list)
    name: str | None = None
    alias: list[str] = Field(default_factory=list)
    telecom: list[FHIRContactPoint] = Field(default_factory=list)
    address: list[FHIRAddress] = Field(default_factory=list)
    contact: list[FHIROrganizationContact] = Field(default_factory=list)


# ─── FHIR Coverage ───────────────────────────────────────────────────────────


class FHIRCoverageClass(BaseModel):
    """Type of cost sharing for the coverage."""

    type: FHIRCoding | None = None
    value: str | None = None


class FHIRCoveragePayor(FHIRReference):
    """Reference to the organization providing coverage."""

    pass


class FHIRCoverage(BaseModel):
    """FHIR R4 Coverage resource — insurance plan details."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["Coverage"] = Field(
        default="Coverage",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    status: str = "active"
    type: FHIRCoding | None = None
    beneficiary: FHIRReference = Field(default_factory=FHIRReference)
    period: FHIRPeriod = Field(default_factory=FHIRPeriod)
    payor: list[FHIRCoveragePayor] = Field(default_factory=list)
    class_: FHIRCoverageClass | None = Field(
        default=None,
        serialization_alias="class",
    )
    network: str | None = None
    order: int | None = None
    typeOfBenefit: list[FHIRCoding] = Field(default_factory=list)


# ─── FHIR DiagnosticReport ──────────────────────────────────────────────────


class FHIRDiagnosticReport(BaseModel):
    """FHIR R4 DiagnosticReport resource — lab reports, imaging results."""

    model_config = _MODEL_CONFIG

    resource_type: Literal["DiagnosticReport"] = Field(
        default="DiagnosticReport",
        serialization_alias="resourceType",
    )
    id: str | None = None
    meta: FHIRMeta = Field(default_factory=FHIRMeta)
    identifier: list[FHIRIdentifier] = Field(default_factory=list)
    status: str = "final"
    category: list[FHIRCoding] = Field(default_factory=list)
    code: FHIRCoding = Field(default_factory=FHIRCoding)
    subject: FHIRReference = Field(default_factory=FHIRReference)
    encounter: FHIRReference | None = None
    effectiveDateTime: datetime | None = None
    issued: datetime | None = None
    performer: list[FHIRReference] = Field(default_factory=list)
    result: list[FHIRReference] = Field(default_factory=list)
    conclusion: str | None = None
    conclusionCode: list[FHIRCoding] = Field(default_factory=list)
