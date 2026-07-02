"""Clinical data service — wraps FHIR store for patient chart queries."""

from __future__ import annotations

from typing import Any

from src.services.fhir_store import FHIRStore, fhir_store


class ClinicalDataService:
    """Service for patient clinical data queries."""

    def __init__(self, store: FHIRStore = fhir_store) -> None:
        self._store = store

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        """Get a patient resource by id."""
        return self._store.read("Patient", patient_id)

    def list_patients(self) -> list[dict[str, Any]]:
        """List all patients."""
        bundle = self._store.search("Patient", {})
        return [e.resource for e in bundle.entry if e.resource is not None]

    def get_patient_conditions(self, patient_id: str) -> list[dict[str, Any]]:
        """Get all active conditions for a patient."""
        ref = f"Patient/{patient_id}"
        bundle = self._store.search("Condition", {"patient": ref})
        return [
            r
            for r in (e.resource for e in bundle.entry if e.resource is not None)
            if self._is_active(r, "clinicalStatus")
        ]

    def get_patient_medications(self, patient_id: str) -> list[dict[str, Any]]:
        """Get all active medications for a patient."""
        ref = f"Patient/{patient_id}"
        bundle = self._store.search("MedicationRequest", {"patient": ref})
        return [
            r
            for r in (e.resource for e in bundle.entry if e.resource is not None)
            if r.get("status") == "active"
        ]

    def get_patient_allergies(self, patient_id: str) -> list[dict[str, Any]]:
        """Get all allergies for a patient."""
        ref = f"Patient/{patient_id}"
        bundle = self._store.search("AllergyIntolerance", {"patient": ref})
        return [
            r
            for r in (e.resource for e in bundle.entry if e.resource is not None)
            if self._is_active(r, "clinicalStatus")
        ]

    def get_patient_observations(
        self, patient_id: str, category: str | None = None
    ) -> list[dict[str, Any]]:
        """Get observations for a patient, optionally filtered by category code."""
        ref = f"Patient/{patient_id}"
        bundle = self._store.search("Observation", {"patient": ref})
        results = [
            r
            for r in (e.resource for e in bundle.entry if e.resource is not None)
            if r.get("status") == "final"
        ]
        if category:
            results = [
                r for r in results if self._has_category(r, category)
            ]
        return results

    def get_patient_vitals(self, patient_id: str) -> list[dict[str, Any]]:
        """Get vital signs for a patient."""
        return self.get_patient_observations(patient_id, category="vital-signs")

    def get_patient_labs(self, patient_id: str) -> list[dict[str, Any]]:
        """Get lab results for a patient."""
        return self.get_patient_observations(patient_id, category="laboratory")

    def get_patient_encounters(self, patient_id: str) -> list[dict[str, Any]]:
        """Get encounters for a patient."""
        ref = f"Patient/{patient_id}"
        bundle = self._store.search("Encounter", {"patient": ref})
        return [e.resource for e in bundle.entry if e.resource is not None]

    def get_patient_summary(self, patient_id: str) -> dict[str, Any]:
        """Get full patient summary with all clinical data."""
        patient = self.get_patient(patient_id)
        if patient is None:
            return {}

        return {
            "patient": patient,
            "conditions": self.get_patient_conditions(patient_id),
            "medications": self.get_patient_medications(patient_id),
            "allergies": self.get_patient_allergies(patient_id),
            "vitals": self.get_patient_vitals(patient_id),
            "labs": self.get_patient_labs(patient_id),
            "recent_encounters": self.get_patient_encounters(patient_id),
        }

    def get_patient_timeline(
        self, patient_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get chronological timeline of all clinical events for a patient."""
        events: list[dict[str, Any]] = []

        for cond in self.get_patient_conditions(patient_id):
            code = cond.get("code", {})
            events.append(
                {
                    "event_type": "condition_diagnosed",
                    "date": cond.get("onsetDateTime") or cond.get("recordedDate", ""),
                    "summary": code.get("display", "Unknown condition"),
                    "resource_type": "Condition",
                    "resource_id": cond.get("id", ""),
                }
            )

        for med in self.get_patient_medications(patient_id):
            concept = med.get("medicationCodeableConcept", {})
            events.append(
                {
                    "event_type": "medication_prescribed",
                    "date": med.get("authoredOn", ""),
                    "summary": concept.get("display", "Unknown medication"),
                    "resource_type": "MedicationRequest",
                    "resource_id": med.get("id", ""),
                }
            )

        for allergy in self.get_patient_allergies(patient_id):
            code = allergy.get("code", {})
            events.append(
                {
                    "event_type": "allergy_recorded",
                    "date": allergy.get("recordedDate", ""),
                    "summary": code.get("display", "Unknown allergy"),
                    "resource_type": "AllergyIntolerance",
                    "resource_id": allergy.get("id", ""),
                }
            )

        for obs in self.get_patient_observations(patient_id):
            code = obs.get("code", {})
            vq = obs.get("valueQuantity", {})
            val_str = (
                f"{vq.get('value', '')} {vq.get('unit', '')}".strip()
                if vq
                else obs.get("valueString", "")
            )
            events.append(
                {
                    "event_type": "observation_recorded",
                    "date": obs.get("effectiveDateTime", ""),
                    "summary": f"{code.get('display', 'Observation')}: {val_str}",
                    "resource_type": "Observation",
                    "resource_id": obs.get("id", ""),
                }
            )

        for enc in self.get_patient_encounters(patient_id):
            enc_class = enc.get("class", {})
            events.append(
                {
                    "event_type": "encounter",
                    "date": enc.get("period", {}).get("start", ""),
                    "summary": enc_class.get("display", "Encounter"),
                    "resource_type": "Encounter",
                    "resource_id": enc.get("id", ""),
                }
            )

        events.sort(key=lambda e: e.get("date", "") or "", reverse=True)
        return events[:limit]

    # ─── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _is_active(resource: dict[str, Any], field: str) -> bool:
        """Check if a status field has active clinical status."""
        coding = resource.get(field)
        if isinstance(coding, dict):
            return coding.get("code") == "active"
        return False

    @staticmethod
    def _has_category(resource: dict[str, Any], category_code: str) -> bool:
        """Check if an observation has a given category code."""
        for cat in resource.get("category", []):
            if isinstance(cat, dict) and cat.get("code") == category_code:
                return True
        return False


# Singleton
clinical_data_service = ClinicalDataService()
