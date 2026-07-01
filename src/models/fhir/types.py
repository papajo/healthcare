"""FHIR R4 helper / supporting types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ─── Primitive types ──────────────────────────────────────────────────────────


class FHIRMeta(BaseModel):
    """Resource metadata."""

    lastUpdated: datetime = Field(default_factory=datetime.utcnow)


class FHIRCoding(BaseModel):
    """Reference to a code defined by a terminology system."""

    system: str | None = None
    code: str | None = None
    display: str | None = None


class FHIRIdentifier(BaseModel):
    """Business identifier for a resource."""

    system: str | None = None
    value: str | None = None
    type: FHIRCoding | None = None


class FHIRReference(BaseModel):
    """A reference from one resource to another."""

    reference: str = ""
    display: str | None = None


class FHIRHumanName(BaseModel):
    """A human name for the person."""

    family: str | None = None
    given: list[str] = Field(default_factory=list)
    use: str | None = None


class FHIRAddress(BaseModel):
    """A physical address."""

    line: list[str] = Field(default_factory=list)
    city: str | None = None
    state: str | None = None
    postalCode: str | None = None
    country: str | None = None


class FHIRContactPoint(BaseModel):
    """An amount of money with a unit."""

    system: str | None = None
    value: str | None = None
    use: str | None = None


class FHIRPeriod(BaseModel):
    """A time period defined by a start and end date/time."""

    start: datetime | None = None
    end: datetime | None = None


class FHIRQuantity(BaseModel):
    """A measured amount (or an amount that can potentially be measured)."""

    value: float | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None


class FHIRMoney(BaseModel):
    """An amount of money with a unit."""

    value: float | None = None
    currency: str = "USD"


# ─── Complex supporting types ────────────────────────────────────────────────


class FHIRPatientContact(BaseModel):
    """Contact person for the patient."""

    relationship: list[FHIRCoding] = Field(default_factory=list)
    name: FHIRHumanName | None = None
    telecom: list[FHIRContactPoint] = Field(default_factory=list)


class FHIRTiming(BaseModel):
    """Timing of administration."""

    code: FHIRCoding | None = None


class FHIRDosageRate(BaseModel):
    """Single dose rate."""

    doseQuantity: FHIRQuantity | None = None


class FHIRDosageInstruction(BaseModel):
    """How the medication is taken."""

    text: str | None = None
    timing: FHIRTiming | None = None
    doseAndRate: list[FHIRDosageRate] = Field(default_factory=list)


class FHIRAllergyReaction(BaseModel):
    """Details about a reaction."""

    substance: FHIRCoding | None = None
    manifestation: FHIRCoding | None = None
    severity: FHIRCoding | None = None


class FHIRReferenceRange(BaseModel):
    """Reference range for a quantity observation."""

    low: FHIRQuantity | None = None
    high: FHIRQuantity | None = None
    text: str | None = None


class FHIRClaimItem(BaseModel):
    """Item on a claim."""

    sequence: int = 1
    service: FHIRCoding | None = None
    unitPrice: FHIRMoney | None = None
    net: FHIRMoney | None = None


class FHIRClaimDiagnosis(BaseModel):
    """Diagnosis on a claim."""

    sequence: int = 1
    diagnosisCodeableConcept: FHIRCoding | None = None


class FHIRBundleEntry(BaseModel):
    """Entry in a Bundle."""

    fullUrl: str = ""
    resource: dict[str, Any] | None = None
    search: dict[str, str] | None = None


class FHIRSearchParams:
    """Search parameters for FHIR queries."""

    def __init__(
        self,
        resource_type: str,
        filters: dict[str, str] | None = None,
        sort: list[str] | None = None,
        count: int = 20,
        offset: int = 0,
    ):
        self.resource_type = resource_type
        self.filters = filters or {}
        self.sort = sort or []
        self.count = count
        self.offset = offset
