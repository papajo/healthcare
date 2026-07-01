"""Map between domain models and FHIR R4 resources."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.models.domain import ClaimResponse
from src.models.fhir import (
    FHIRBundle,
    FHIRClaim,
    FHIRClaimDiagnosis,
    FHIRClaimItem,
    FHIRCoding,
    FHIREncounter,
    FHIRMoney,
    FHIRPatient,
    FHIRPeriod,
    FHIRReference,
)


def domain_to_fhir_patient(
    patient_pseudo_id: str,
    *,
    family: str = "Unknown",
    given: list[str] | None = None,
    gender: str = "unknown",
    birth_date: str | None = None,
) -> FHIRPatient:
    """Create a FHIR Patient from domain pseudo-id and optional demographic info."""
    return FHIRPatient(
        id=patient_pseudo_id,
        identifier=[
            {
                "system": "http://crisiscost.example.org/pseudo-id",
                "value": patient_pseudo_id,
            }
        ],
        name=[
            {
                "family": family,
                "given": given or ["Patient"],
                "use": "official",
            }
        ],
        gender=gender,
        birthDate=birth_date,
    )


def domain_to_fhir_encounter(
    encounter_id: str,
    patient_id: str,
    *,
    status: str = "planned",
    encounter_class_code: str = "IMP",
    encounter_class_display: str = "inpatient encounter",
    priority_code: str | None = None,
    priority_display: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    reason_codes: list[dict[str, str]] | None = None,
) -> FHIREncounter:
    """Create a FHIR Encounter from domain fields."""
    priority = None
    if priority_code:
        priority = FHIRCoding(
            system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
            code=priority_code,
            display=priority_display,
        )

    reason_coding = []
    if reason_codes:
        reason_coding = [
            FHIRCoding(system=r.get("system", ""), code=r.get("code", ""), display=r.get("display"))
            for r in reason_codes
        ]

    return FHIREncounter(
        id=encounter_id,
        identifier=[
            {
                "system": "http://crisiscost.example.org/encounter",
                "value": encounter_id,
            }
        ],
        status=status,
        class_=FHIRCoding(
            system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
            code=encounter_class_code,
            display=encounter_class_display,
        ),
        subject=FHIRReference(reference=f"Patient/{patient_id}"),
        period=FHIRPeriod(start=start, end=end),
        priority=priority,
        reasonCode=reason_coding,
    )


def domain_to_fhir_claim(claim: ClaimResponse) -> FHIRClaim:
    """Map a domain ClaimResponse to a FHIR Claim resource."""
    status_map = {
        "DRAFT": "draft",
        "SUBMITTED": "active",
        "UNDER_REVIEW": "active",
        "APPROVED": "active",
        "PARTIAL": "active",
        "DENIED": "active",
        "APPEALED": "active",
        "SETTLED": "complete",
        "VOIDED": "cancelled",
    }

    claim_type_map = {
        "PROFESSIONAL": ("professional", "Professional"),
        "INSTITUTIONAL": ("institutional", "Institutional"),
        "PHARMACY": ("pharmacy", "Pharmacy"),
    }
    ct = claim_type_map.get(claim.claim_type, ("professional", "Professional"))

    items = []
    for li in claim.line_items:
        items.append(
            FHIRClaimItem(
                sequence=1,
                service=FHIRCoding(
                    system="http://www.ama-assn.org/go/cpt",
                    code=li.service_code,
                    display=li.description,
                ),
                unitPrice=FHIRMoney(value=li.unit_price_cents / 100.0, currency="USD"),
                net=FHIRMoney(value=li.total_cents / 100.0, currency="USD"),
            )
        )

    diagnoses = [
        FHIRClaimDiagnosis(
            sequence=i + 1,
            diagnosisCodeableConcept=FHIRCoding(
                system="http://hl7.org/fhir/sid/icd-10-cm", code=code
            ),
        )
        for i, code in enumerate(claim.diagnosis_codes)
    ]

    return FHIRClaim(
        id=str(claim.claim_id),
        identifier=[
            {
                "system": "http://crisiscost.example.org/claim",
                "value": str(claim.claim_id),
            }
        ],
        status=status_map.get(claim.claim_status.value, "active"),
        type=FHIRCoding(
            system="http://terminology.hl7.org/CodeSystem/claim-type",
            code=ct[0],
            display=ct[1],
        ),
        patient=FHIRReference(
            reference=f"Patient/{claim.patient_pseudo_id}",
            display="Patient",
        ),
        provider=FHIRReference(
            reference=f"Organization/{claim.provider_org_id}",
            display="Provider Organization",
        ),
        billablePeriod=FHIRPeriod(
            start=claim.service_date.isoformat() if claim.service_date else None,
        ),
        item=items,
        total=FHIRMoney(
            value=claim.total_charged_cents / 100.0, currency="USD"
        ),
        diagnosis=diagnoses,
    )


def fhir_to_domain_claim(fhir_claim: FHIRClaim) -> dict[str, Any]:
    """Extract domain-compatible fields from a FHIR Claim."""
    status_reverse = {
        "draft": "DRAFT",
        "active": "SUBMITTED",
        "complete": "SETTLED",
        "cancelled": "VOIDED",
    }
    type_reverse = {
        "professional": "PROFESSIONAL",
        "institutional": "INSTITUTIONAL",
        "pharmacy": "PHARMACY",
    }

    line_items = []
    for item in fhir_claim.item:
        svc = item.service or FHIRCoding()
        line_items.append(
            {
                "service_code": svc.code or "",
                "description": svc.display or "",
                "unit_price_cents": int((item.unitPrice.value or 0) * 100),
                "total_cents": int((item.net.value or 0) * 100),
            }
        )

    diag_codes = [
        d.diagnosisCodeableConcept.code
        for d in fhir_claim.diagnosis
        if d.diagnosisCodeableConcept
    ]

    return {
        "claim_id": fhir_claim.id,
        "patient_ref": fhir_claim.patient.reference,
        "provider_ref": fhir_claim.provider.reference,
        "status": status_reverse.get(fhir_claim.status, "DRAFT"),
        "claim_type": type_reverse.get(
            fhir_claim.type.code if fhir_claim.type else "", "PROFESSIONAL"
        ),
        "line_items": line_items,
        "diagnosis_codes": diag_codes,
        "total_cents": int((fhir_claim.total.value or 0) * 100),
    }


def fhir_bundle_to_list(bundle: FHIRBundle) -> list[dict[str, Any]]:
    """Extract all resources from a FHIR Bundle as a list of dicts."""
    return [e.resource for e in bundle.entry if e.resource is not None]
