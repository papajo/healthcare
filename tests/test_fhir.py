"""Tests for FHIR R4 data layer — models, store, mapper, validator, and API."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.models.domain import ClaimLineItem, ClaimResponse, ClaimStatus
from src.models.fhir import (
    FHIRAllergyIntolerance,
    FHIRBundle,
    FHIRClaim,
    FHIRCondition,
    FHIREncounter,
    FHIRMedicationRequest,
    FHIRObservation,
    FHIRPatient,
)
from src.models.fhir.types import (
    FHIRCoding,
    FHIRHumanName,
    FHIRMoney,
    FHIRReference,
)
from src.services.fhir_mapper import (
    domain_to_fhir_claim,
    domain_to_fhir_encounter,
    domain_to_fhir_patient,
    fhir_bundle_to_list,
    fhir_to_domain_claim,
)
from src.services.fhir_store import FHIRStore, fhir_store, seed_demo_data
from src.services.fhir_validator import make_operation_outcome, validate_resource

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _fresh_store() -> FHIRStore:
    """Return a clean FHIRStore (no seed data)."""
    return FHIRStore()


def _make_patient_dict(**overrides) -> dict:
    base = {
        "resourceType": "Patient",
        "active": True,
        "name": [{"family": "Test", "given": ["User"], "use": "official"}],
        "gender": "female",
        "identifier": [
            {"system": "http://example.org/mrn", "value": f"MRN-{uuid4().hex[:8]}"}
        ],
    }
    base.update(overrides)
    return base


def _make_encounter_dict(patient_id: str = "patient-001", **overrides) -> dict:
    base = {
        "resourceType": "Encounter",
        "status": "planned",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "IMP",
            "display": "inpatient encounter",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
    }
    base.update(overrides)
    return base


# ─── Model Tests ──────────────────────────────────────────────────────────────


class TestFHIRModels:
    """Test FHIR R4 Pydantic model construction."""

    def test_patient_model(self):
        p = FHIRPatient(
            id="test-1",
            name=[FHIRHumanName(family="Doe", given=["Jane"])],
            gender="female",
        )
        assert p.resource_type == "Patient"
        assert p.id == "test-1"
        assert p.name[0].family == "Doe"
        assert p.meta.lastUpdated is not None

    def test_encounter_model(self):
        e = FHIREncounter(
            id="enc-1",
            status="in-progress",
            class_=FHIRCoding(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="EMER",
                display="emergency",
            ),
            subject=FHIRReference(reference="Patient/p-1"),
        )
        assert e.resource_type == "Encounter"
        assert e.status == "in-progress"
        assert e.subject.reference == "Patient/p-1"

    def test_claim_model(self):
        c = FHIRClaim(
            id="claim-1",
            status="active",
            patient=FHIRReference(reference="Patient/p-1"),
            provider=FHIRReference(reference="Organization/o-1"),
            total=FHIRMoney(value=100.50, currency="USD"),
        )
        assert c.resource_type == "Claim"
        assert c.total.value == 100.50

    def test_bundle_model(self):
        b = FHIRBundle(type="searchset", total=0, entry=[])
        assert b.resource_type == "Bundle"
        assert b.type == "searchset"
        assert b.total == 0

    def test_observation_model(self):
        o = FHIRObservation(
            id="obs-1",
            status="final",
            code=FHIRCoding(system="http://loinc.org", code="8867-4", display="Heart rate"),
            subject=FHIRReference(reference="Patient/p-1"),
        )
        assert o.resource_type == "Observation"
        assert o.code.code == "8867-4"

    def test_condition_model(self):
        c = FHIRCondition(
            id="cond-1",
            subject=FHIRReference(reference="Patient/p-1"),
            clinicalStatus=FHIRCoding(code="active"),
        )
        assert c.resource_type == "Condition"

    def test_medication_request_model(self):
        m = FHIRMedicationRequest(
            id="med-1",
            status="active",
            intent="order",
            subject=FHIRReference(reference="Patient/p-1"),
        )
        assert m.resource_type == "MedicationRequest"

    def test_allergy_model(self):
        a = FHIRAllergyIntolerance(
            id="allergy-1",
            patient=FHIRReference(reference="Patient/p-1"),
            type="allergy",
            criticality="high",
        )
        assert a.resource_type == "AllergyIntolerance"


# ─── Store Tests ──────────────────────────────────────────────────────────────


class TestFHIRStore:
    """Test the in-memory FHIR store."""

    def setup_method(self):
        self.store = _fresh_store()

    def test_create_and_read(self):
        resource = _make_patient_dict()
        created = self.store.create("Patient", resource)
        assert created["id"] is not None
        assert created["resourceType"] == "Patient"
        assert "lastUpdated" in created["meta"]

        found = self.store.read("Patient", created["id"])
        assert found is not None
        assert found["id"] == created["id"]

    def test_read_not_found(self):
        assert self.store.read("Patient", "nonexistent") is None

    def test_update(self):
        resource = _make_patient_dict()
        created = self.store.create("Patient", resource)
        created["gender"] = "male"
        updated = self.store.update("Patient", created["id"], created)
        assert updated is not None
        assert updated["gender"] == "male"

    def test_update_not_found(self):
        result = self.store.update("Patient", "nonexistent", _make_patient_dict())
        assert result is None

    def test_delete(self):
        resource = _make_patient_dict()
        created = self.store.create("Patient", resource)
        assert self.store.delete("Patient", created["id"]) is True
        assert self.store.read("Patient", created["id"]) is None

    def test_delete_not_found(self):
        assert self.store.delete("Patient", "nonexistent") is False

    def test_count(self):
        assert self.store.count("Patient") == 0
        self.store.create("Patient", _make_patient_dict())
        self.store.create("Patient", _make_patient_dict())
        assert self.store.count("Patient") == 2

    def test_search_by_id(self):
        resource = _make_patient_dict()
        created = self.store.create("Patient", resource)
        bundle = self.store.search("Patient", {"_id": created["id"]})
        assert bundle.total == 1
        assert bundle.entry[0].resource["id"] == created["id"]

    def test_search_by_status(self):
        self.store.create(
            "Encounter",
            _make_encounter_dict(status="planned"),
        )
        self.store.create(
            "Encounter",
            _make_encounter_dict(status="finished"),
        )
        bundle = self.store.search("Encounter", {"status": "planned"})
        assert bundle.total == 1

    def test_search_by_patient(self):
        p = self.store.create("Patient", _make_patient_dict())
        self.store.create("Encounter", _make_encounter_dict(patient_id=p["id"]))
        bundle = self.store.search("Encounter", {"patient": f"Patient/{p['id']}"})
        assert bundle.total == 1

    def test_search_empty(self):
        bundle = self.store.search("Patient", {})
        assert bundle.total == 0
        assert bundle.entry == []

    def test_search_unsupported_type(self):
        bundle = self.store.search("UnsupportedType", {})
        assert bundle.total == 0

    def test_search_by_patient_method(self):
        p = self.store.create("Patient", _make_patient_dict())
        self.store.create("Encounter", _make_encounter_dict(patient_id=p["id"]))
        results = self.store.search_by_patient(p["id"])
        assert len(results) == 1

    def test_search_by_patient_with_type(self):
        p = self.store.create("Patient", _make_patient_dict())
        self.store.create("Encounter", _make_encounter_dict(patient_id=p["id"]))
        results = self.store.search_by_patient(p["id"], resource_type="Encounter")
        assert len(results) == 1
        results_other = self.store.search_by_patient(p["id"], resource_type="Condition")
        assert len(results_other) == 0

    def test_create_bundle(self):
        r1 = self.store.create("Patient", _make_patient_dict())
        r2 = self.store.create("Patient", _make_patient_dict())
        bundle = self.store.create_bundle("collection", [r1, r2])
        assert bundle.type == "collection"
        assert bundle.total == 2

    def test_create_unsupported_type(self):
        with pytest.raises(ValueError, match="Unsupported"):
            self.store.create("BadType", {})


# ─── Seed Data Tests ──────────────────────────────────────────────────────────


class TestSeedData:
    """Test that seed data is properly loaded."""

    def setup_method(self):
        seed_demo_data()

    def test_seed_patients(self):
        """Seeded store should have 5 patients."""
        assert fhir_store.count("Patient") >= 5

    def test_seed_encounters(self):
        """Seeded store should have 5 encounters."""
        assert fhir_store.count("Encounter") >= 5

    def test_patient_has_identifier(self):
        """Seeded patient should have MRN identifier."""
        bundle = fhir_store.search("Patient", {})
        patient = bundle.entry[0].resource
        assert len(patient.get("identifier", [])) > 0
        assert patient["identifier"][0]["system"] == "http://hospital.example.org/mrn"


# ─── Mapper Tests ─────────────────────────────────────────────────────────────


class TestFHIRMapper:
    """Test domain <-> FHIR mapping."""

    def test_domain_to_fhir_patient(self):
        p = domain_to_fhir_patient(
            "pseudo-123",
            family="Doe",
            given=["Jane"],
            gender="female",
        )
        assert p.resource_type == "Patient"
        assert p.id == "pseudo-123"
        assert p.name[0].family == "Doe"
        assert p.gender == "female"

    def test_domain_to_fhir_encounter(self):
        e = domain_to_fhir_encounter(
            "enc-001",
            "patient-001",
            status="in-progress",
            encounter_class_code="EMER",
            encounter_class_display="emergency",
        )
        assert e.resource_type == "Encounter"
        assert e.id == "enc-001"
        assert e.subject.reference == "Patient/patient-001"
        assert e.status == "in-progress"

    def test_domain_to_fhir_claim(self):
        claim = ClaimResponse(
            encounter_id="enc-001",
            patient_pseudo_id=uuid4(),
            provider_org_id=uuid4(),
            payer_id="payer-1",
            claim_type="PROFESSIONAL",
            claim_status=ClaimStatus.SUBMITTED,
            service_date=datetime.now(UTC).date(),
            line_items=[
                ClaimLineItem(
                    line_item_id="L1",
                    service_code="99213",
                    description="Office visit",
                    quantity=1,
                    unit_price_cents=15000,
                    total_cents=15000,
                )
            ],
            diagnosis_codes=["R07.9"],
            total_charged_cents=15000,
        )
        fhir_claim = domain_to_fhir_claim(claim)
        assert fhir_claim.resource_type == "Claim"
        assert fhir_claim.status == "active"
        assert fhir_claim.total.value == 150.0
        assert len(fhir_claim.item) == 1
        assert fhir_claim.item[0].service.code == "99213"

    def test_fhir_to_domain_claim_roundtrip(self):
        claim = ClaimResponse(
            encounter_id="enc-002",
            patient_pseudo_id=uuid4(),
            provider_org_id=uuid4(),
            payer_id="payer-1",
            claim_type="PROFESSIONAL",
            claim_status=ClaimStatus.SETTLED,
            service_date=datetime.now(UTC).date(),
            line_items=[
                ClaimLineItem(
                    line_item_id="L1",
                    service_code="99214",
                    description="Office visit complex",
                    quantity=1,
                    unit_price_cents=25000,
                    total_cents=25000,
                )
            ],
            diagnosis_codes=["I10"],
            total_charged_cents=25000,
        )
        fhir_claim = domain_to_fhir_claim(claim)
        domain_dict = fhir_to_domain_claim(fhir_claim)
        assert domain_dict["status"] == "SETTLED"
        assert domain_dict["total_cents"] == 25000
        assert domain_dict["diagnosis_codes"] == ["I10"]

    def test_fhir_bundle_to_list(self):
        bundle = FHIRBundle(
            type="searchset",
            total=2,
            entry=[
                {"fullUrl": "Patient/1", "resource": {"id": "1", "resourceType": "Patient"}},
                {"fullUrl": "Patient/2", "resource": {"id": "2", "resourceType": "Patient"}},
            ],
        )
        result = fhir_bundle_to_list(bundle)
        assert len(result) == 2
        assert result[0]["id"] == "1"


# ─── Validator Tests ──────────────────────────────────────────────────────────


class TestFHIRValidator:
    """Test FHIR resource validation."""

    def test_valid_patient(self):
        resource = _make_patient_dict()
        errors = validate_resource(resource)
        assert errors == []

    def test_patient_missing_name(self):
        resource = _make_patient_dict(name=[])
        errors = validate_resource(resource)
        assert any("name" in e for e in errors)

    def test_patient_missing_gender(self):
        resource = _make_patient_dict(gender="")
        errors = validate_resource(resource)
        assert any("gender" in e for e in errors)

    def test_encounter_missing_status(self):
        resource = _make_encounter_dict(status="")
        errors = validate_resource(resource)
        assert any("status" in e for e in errors)

    def test_encounter_missing_subject(self):
        resource = _make_encounter_dict()
        del resource["subject"]
        errors = validate_resource(resource)
        assert any("subject" in e for e in errors)

    def test_invalid_reference_format(self):
        resource = _make_patient_dict()
        resource["subject"] = {"reference": "bad reference format!!"}
        errors = validate_resource(resource)
        assert any("reference" in e for e in errors)

    def test_unknown_resource_type(self):
        errors = validate_resource({"resourceType": "Alien"})
        assert len(errors) == 1
        assert "Unknown" in errors[0]

    def test_invalid_status_value(self):
        resource = _make_encounter_dict(status="bananas")
        errors = validate_resource(resource)
        assert any("status" in e for e in errors)

    def test_operation_outcome(self):
        errors = ["err1", "err2"]
        outcome = make_operation_outcome(errors)
        assert outcome.resource_type == "OperationOutcome"
        assert len(outcome.issue) == 2
        assert outcome.issue[0].diagnostics == "err1"

    def test_claim_valid(self):
        resource = {
            "resourceType": "Claim",
            "status": "active",
            "patient": {"reference": "Patient/p-1"},
            "provider": {"reference": "Organization/o-1"},
        }
        errors = validate_resource(resource)
        assert errors == []


# ─── API Tests ────────────────────────────────────────────────────────────────


class TestFHIRAPI:
    """Test FHIR REST API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        # Reset the store to avoid cross-test contamination from seed data
        fhir_store._resources.clear()
        seed_demo_data()
        self.client = TestClient(app)

        # Ensure admin user exists for auth
        from src.services.auth_service import auth_service
        from src.models.auth import UserCreate, UserRole

        existing = {u.username for u in auth_service.list_users()}
        if "testfhiradmin" not in existing:
            auth_service.register(
                UserCreate(
                    username="testfhiradmin",
                    email="testfhiradmin@test.example",
                    password="testfhiradmin123",
                    full_name="Test FHIR Admin",
                    role=UserRole.ADMIN,
                )
            )
        tokens = auth_service.login("testfhiradmin", "testfhiradmin123")
        self.headers = {"Authorization": f"Bearer {tokens.access_token}"}

    def test_capability_statement(self):
        resp = self.client.get("/fhir/metadata")
        assert resp.status_code == 200
        data = resp.json()
        assert data["resourceType"] == "CapabilityStatement"
        assert data["fhirVersion"] == "4.0.1"
        resource_types = [r["type"] for r in data["rest"][0]["resource"]]
        assert "Patient" in resource_types
        assert "Encounter" in resource_types

    def test_create_patient(self):
        resp = self.client.post(
            "/fhir/Patient",
            json=_make_patient_dict(),
            headers=self.headers,
        )
        assert resp.status_code == 201
        assert resp.headers["content-type"] == "application/fhir+json"
        assert "Location" in resp.headers
        data = resp.json()
        assert data["resourceType"] == "Patient"
        assert data["id"] is not None

    def test_read_patient(self):
        create_resp = self.client.post(
            "/fhir/Patient",
            json=_make_patient_dict(),
            headers=self.headers,
        )
        patient_id = create_resp.json()["id"]

        resp = self.client.get(
            f"/fhir/Patient/{patient_id}",
            headers=self.headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == patient_id

    def test_read_patient_not_found(self):
        resp = self.client.get(
            "/fhir/Patient/nonexistent",
            headers=self.headers,
        )
        assert resp.status_code == 404

    def test_update_patient(self):
        create_resp = self.client.post(
            "/fhir/Patient",
            json=_make_patient_dict(),
            headers=self.headers,
        )
        patient_id = create_resp.json()["id"]

        updated = _make_patient_dict(gender="male")
        resp = self.client.put(
            f"/fhir/Patient/{patient_id}",
            json=updated,
            headers=self.headers,
        )
        assert resp.status_code == 200
        assert resp.json()["gender"] == "male"

    def test_delete_patient(self):
        create_resp = self.client.post(
            "/fhir/Patient",
            json=_make_patient_dict(),
            headers=self.headers,
        )
        patient_id = create_resp.json()["id"]

        resp = self.client.delete(
            f"/fhir/Patient/{patient_id}",
            headers=self.headers,
        )
        assert resp.status_code == 204

        read_resp = self.client.get(
            f"/fhir/Patient/{patient_id}",
            headers=self.headers,
        )
        assert read_resp.status_code == 404

    def test_search_patients(self):
        self.client.post(
            "/fhir/Patient",
            json=_make_patient_dict(),
            headers=self.headers,
        )
        self.client.post(
            "/fhir/Patient",
            json=_make_patient_dict(),
            headers=self.headers,
        )

        resp = self.client.get(
            "/fhir/Patient",
            headers=self.headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resourceType"] == "Bundle"
        assert data["total"] >= 2

    def test_create_encounter(self):
        resp = self.client.post(
            "/fhir/Encounter",
            json=_make_encounter_dict(),
            headers=self.headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["resourceType"] == "Encounter"

    def test_search_encounters_by_status(self):
        self.client.post(
            "/fhir/Encounter",
            json=_make_encounter_dict(status="planned"),
            headers=self.headers,
        )
        self.client.post(
            "/fhir/Encounter",
            json=_make_encounter_dict(status="finished"),
            headers=self.headers,
        )
        resp = self.client.get(
            "/fhir/Encounter?status=planned",
            headers=self.headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2  # 1 seeded + 1 created above

    def test_search_by_patient(self):
        p_resp = self.client.post(
            "/fhir/Patient",
            json=_make_patient_dict(),
            headers=self.headers,
        )
        patient_id = p_resp.json()["id"]
        self.client.post(
            "/fhir/Encounter",
            json=_make_encounter_dict(patient_id=patient_id),
            headers=self.headers,
        )

        resp = self.client.get(
            f"/fhir/Encounter?patient=Patient/{patient_id}",
            headers=self.headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_validation_error(self):
        resp = self.client.post(
            "/fhir/Patient",
            json={"resourceType": "Patient", "gender": "female"},
            headers=self.headers,
        )
        assert resp.status_code == 422

    def test_unsupported_resource_type(self):
        resp = self.client.get(
            "/fhir/Alien",
            headers=self.headers,
        )
        assert resp.status_code == 404

    def test_everything(self):
        p_resp = self.client.post(
            "/fhir/Patient",
            json=_make_patient_dict(),
            headers=self.headers,
        )
        patient_id = p_resp.json()["id"]
        self.client.post(
            "/fhir/Encounter",
            json=_make_encounter_dict(patient_id=patient_id),
            headers=self.headers,
        )

        resp = self.client.get(
            f"/fhir/Patient/{patient_id}/$everything",
            headers=self.headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "collection"
        assert data["total"] >= 2  # patient + at least 1 encounter

    def test_everything_patient_not_found(self):
        resp = self.client.get(
            "/fhir/Patient/nonexistent/$everything",
            headers=self.headers,
        )
        assert resp.status_code == 404

    def test_delete_nonexistent(self):
        resp = self.client.delete(
            "/fhir/Patient/nonexistent",
            headers=self.headers,
        )
        assert resp.status_code == 404

    def test_search_with_count_and_offset(self):
        for _ in range(5):
            self.client.post(
                "/fhir/Patient",
                json=_make_patient_dict(),
                headers=self.headers,
            )

        resp = self.client.get(
            "/fhir/Patient?_count=2&_offset=0",
            headers=self.headers,
        )
        data = resp.json()
        assert len(data["entry"]) == 2
        assert data["total"] >= 5

    def test_create_claim(self):
        resp = self.client.post(
            "/fhir/Claim",
            json={
                "resourceType": "Claim",
                "status": "active",
                "patient": {"reference": "Patient/p-1"},
                "provider": {"reference": "Organization/o-1"},
                "total": {"value": 100.0, "currency": "USD"},
            },
            headers=self.headers,
        )
        assert resp.status_code == 201

    def test_create_observation(self):
        resp = self.client.post(
            "/fhir/Observation",
            json={
                "resourceType": "Observation",
                "status": "final",
                "code": {"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"},
                "subject": {"reference": "Patient/p-1"},
                "valueQuantity": {"value": 72, "unit": "beats/min"},
            },
            headers=self.headers,
        )
        assert resp.status_code == 201

    def test_create_condition(self):
        resp = self.client.post(
            "/fhir/Condition",
            json={
                "resourceType": "Condition",
                "subject": {"reference": "Patient/p-1"},
                "clinicalStatus": {"code": "active"},
            },
            headers=self.headers,
        )
        assert resp.status_code == 201
