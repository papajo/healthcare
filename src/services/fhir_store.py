"""In-memory FHIR R4 resource store."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.models.fhir import (
    FHIRBundle,
    FHIRBundleEntry,
)

logger = logging.getLogger(__name__)

SUPPORTED_RESOURCE_TYPES = frozenset({
    "Patient",
    "Encounter",
    "Condition",
    "MedicationRequest",
    "AllergyIntolerance",
    "Observation",
    "Claim",
})


class FHIRStore:
    """In-memory FHIR resource store with CRUD + search."""

    def __init__(self) -> None:
        self._resources: dict[str, dict[str, dict[str, Any]]] = {}

    # ─── CRUD ────────────────────────────────────────────────────────────────

    def create(self, resource_type: str, resource: dict[str, Any]) -> dict[str, Any]:
        """Create a new resource. Assigns id and sets meta.lastUpdated."""
        if resource_type not in SUPPORTED_RESOURCE_TYPES:
            raise ValueError(f"Unsupported resource type: {resource_type}")

        resource_id = resource.get("id") or str(uuid4())
        resource["id"] = resource_id
        resource["resourceType"] = resource_type
        resource["meta"] = resource.get("meta", {})
        resource["meta"]["lastUpdated"] = datetime.now(UTC).isoformat()

        self._resources.setdefault(resource_type, {})[resource_id] = resource
        return resource

    def read(self, resource_type: str, resource_id: str) -> dict[str, Any] | None:
        """Read a resource by id."""
        return self._resources.get(resource_type, {}).get(resource_id)

    def update(
        self, resource_type: str, resource_id: str, resource: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update an existing resource. Returns None if not found."""
        if resource_id not in self._resources.get(resource_type, {}):
            return None

        resource["id"] = resource_id
        resource["resourceType"] = resource_type
        resource["meta"] = resource.get("meta", {})
        resource["meta"]["lastUpdated"] = datetime.now(UTC).isoformat()

        self._resources[resource_type][resource_id] = resource
        return resource

    def delete(self, resource_type: str, resource_id: str) -> bool:
        """Delete a resource. Returns True if deleted, False if not found."""
        if resource_id in self._resources.get(resource_type, {}):
            del self._resources[resource_type][resource_id]
            return True
        return False

    # ─── Search ──────────────────────────────────────────────────────────────

    def search(self, resource_type: str, params: dict[str, str]) -> FHIRBundle:
        """Search resources with filter params."""
        if resource_type not in SUPPORTED_RESOURCE_TYPES:
            return FHIRBundle(type="searchset", total=0, entry=[])

        resources = list(self._resources.get(resource_type, {}).values())
        filtered = self._apply_filters(resources, params)

        entries = [
            FHIRBundleEntry(
                fullUrl=f"{resource_type}/{r['id']}",
                resource=r,
                search={"mode": "match"},
            )
            for r in filtered
        ]

        return FHIRBundle(type="searchset", total=len(entries), entry=entries)

    def search_by_patient(
        self, patient_id: str, resource_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Find all resources referencing a patient."""
        ref_string = f"Patient/{patient_id}"
        results: list[dict[str, Any]] = []

        types_to_search = (
            [resource_type] if resource_type else list(self._resources.keys())
        )

        for rtype in types_to_search:
            for resource in self._resources.get(rtype, {}).values():
                if self._references_patient(resource, ref_string):
                    results.append(resource)

        return results

    def count(self, resource_type: str) -> int:
        """Count resources of a given type."""
        return len(self._resources.get(resource_type, {}))

    def create_bundle(
        self, type_: str, entries: list[dict[str, Any]]
    ) -> FHIRBundle:
        """Wrap a list of resources in a FHIR Bundle."""
        bundle_entries = [
            FHIRBundleEntry(
                fullUrl=f"{r.get('resourceType', 'Unknown')}/{r.get('id', '')}",
                resource=r,
                search={"mode": "match"},
            )
            for r in entries
        ]
        return FHIRBundle(type=type_, total=len(bundle_entries), entry=bundle_entries)

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _apply_filters(
        self, resources: list[dict[str, Any]], params: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Apply simple equality / contains filters."""
        result = resources
        for key, value in params.items():
            if key == "_id":
                result = [r for r in result if r.get("id") == value]
            elif key == "patient":
                # Patient filter: match subject.reference or patient.reference
                result = [
                    r
                    for r in result
                    if self._field_matches_ref(r, "subject", value)
                    or self._field_matches_ref(r, "patient", value)
                ]
            elif key == "subject":
                result = [
                    r
                    for r in result
                    if self._field_matches_ref(r, "subject", value)
                ]
            elif key == "status":
                result = [r for r in result if r.get("status") == value]
            elif key == "identifier":
                result = [
                    r
                    for r in result
                    if any(
                        ident.get("value") == value
                        for ident in r.get("identifier", [])
                    )
                ]
            elif key == "code":
                result = [
                    r
                    for r in result
                    if self._field_matches_coding(r, "code", value)
                ]
            elif key == "date":
                result = [
                    r for r in result if self._field_matches_date(r, value)
                ]
        return result

    @staticmethod
    def _field_matches_ref(
        resource: dict[str, Any], field: str, value: str
    ) -> bool:
        """Check if a reference field matches a value."""
        ref_obj = resource.get(field)
        if isinstance(ref_obj, dict):
            return ref_obj.get("reference", "") == value
        if isinstance(ref_obj, str):
            return ref_obj == value
        return False

    @staticmethod
    def _field_matches_coding(
        resource: dict[str, Any], field: str, value: str
    ) -> bool:
        """Check if a coding field matches a code value."""
        coding = resource.get(field)
        if isinstance(coding, dict):
            return coding.get("code") == value
        return False

    @staticmethod
    def _field_matches_date(resource: dict[str, Any], value: str) -> bool:
        """Check if any datetime field starts with the given date string."""
        for key in ("effectiveDateTime", "authoredOn", "onsetDateTime", "recordedDate"):
            dt = resource.get(key)
            if isinstance(dt, str) and dt.startswith(value):
                return True
        # Check period
        period = resource.get("period", {})
        if isinstance(period, dict):
            for pkey in ("start", "end"):
                pt = period.get(pkey)
                if isinstance(pt, str) and pt.startswith(value):
                    return True
        return False

    @staticmethod
    def _references_patient(resource: dict[str, Any], ref_string: str) -> bool:
        """Check if any reference field in the resource points to a patient."""
        ref_fields = ("subject", "patient", "requester")
        for field in ref_fields:
            ref = resource.get(field)
            if isinstance(ref, dict) and ref.get("reference") == ref_string:
                return True
        # Check participant array
        for participant in resource.get("participant", []):
            ind = participant.get("individual", {})
            if isinstance(ind, dict) and ind.get("reference") == ref_string:
                return True
        return False


# ─── Singleton + Seed ────────────────────────────────────────────────────────

fhir_store = FHIRStore()


def seed_demo_data() -> None:
    """Seed the store with 5 sample patients and encounters."""
    now = datetime.now(UTC).isoformat()
    patients = [
        {
            "id": f"patient-{i:03d}",
            "resourceType": "Patient",
            "meta": {"lastUpdated": now},
            "active": True,
            "name": [
                {
                    "family": last,
                    "given": [first],
                    "use": "official",
                }
            ],
            "gender": gender,
            "identifier": [
                {"system": "http://hospital.example.org/mrn", "value": f"MRN-{i:04d}"}
            ],
            "telecom": [
                {"system": "phone", "value": f"555-010{i}", "use": "home"}
            ],
            "address": [
                {
                    "line": [f"{100 + i} Main St"],
                    "city": "Springfield",
                    "state": "IL",
                    "postalCode": f"6270{i}",
                    "country": "US",
                }
            ],
        }
        for i, (first, last, gender) in enumerate(
            [
                ("Alice", "Smith", "female"),
                ("Bob", "Johnson", "male"),
                ("Carol", "Williams", "female"),
                ("David", "Brown", "male"),
                ("Eve", "Davis", "female"),
            ],
            start=1,
        )
    ]

    for p in patients:
        fhir_store.create("Patient", p)

    encounter_statuses = ["planned", "arrived", "in-progress", "finished", "finished"]
    for i in range(1, 6):
        encounter = {
            "id": f"encounter-{i:03d}",
            "resourceType": "Encounter",
            "meta": {"lastUpdated": now},
            "status": encounter_statuses[i - 1],
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "EMER" if i <= 2 else "IMP",
                "display": "emergency" if i <= 2 else "inpatient encounter",
            },
            "subject": {"reference": f"Patient/patient-{i:03d}"},
            "period": {"start": now},
            "identifier": [
                {
                    "system": "http://hospital.example.org/encounter",
                    "value": f"ENC-{i:04d}",
                }
            ],
        }
        fhir_store.create("Encounter", encounter)

    logger.info("Seeded FHIR store with %d patients and 5 encounters", len(patients))
