"""Tests for Claims Service and API — CRUD + lifecycle."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from src.models.domain import (
    ClaimCreateRequest,
    ClaimLineItem,
    ClaimStatus,
    ClaimStatusUpdate,
)
from src.services.claims_service import ClaimStore

# ─── Helpers ──────────────────────────────────────────────────────────────────


def make_line_item(**overrides) -> ClaimLineItem:
    defaults = {
        "line_item_id": "LINE-001",
        "service_code": "99213",
        "description": "Office visit",
        "quantity": 1,
        "unit_price_cents": 15000,
        "total_cents": 15000,
    }
    defaults.update(overrides)
    return ClaimLineItem(**defaults)


def make_claim_request(**overrides) -> ClaimCreateRequest:
    defaults = {
        "encounter_id": "ENC-CLAIM-001",
        "patient_pseudo_id": uuid4(),
        "provider_org_id": uuid4(),
        "payer_id": "PAYER-001",
        "service_date": date(2026, 7, 1),
        "line_items": [make_line_item()],
        "diagnosis_codes": ["R07.9"],
    }
    defaults.update(overrides)
    return ClaimCreateRequest(**defaults)


# ─── Service Tests ───────────────────────────────────────────────────────────


class TestClaimStore:
    """Test in-memory claim store."""

    def setup_method(self):
        self.store = ClaimStore()

    def test_create_claim(self):
        """Should create a claim with DRAFT status."""
        request = make_claim_request()
        claim = self.store.create_claim(request)

        assert claim.claim_status == ClaimStatus.DRAFT
        assert claim.encounter_id == "ENC-CLAIM-001"
        assert claim.total_charged_cents == 15000
        assert len(claim.line_items) == 1

    def test_get_claim(self):
        """Should retrieve claim by ID."""
        request = make_claim_request()
        claim = self.store.create_claim(request)
        found = self.store.get_claim(str(claim.claim_id))

        assert found is not None
        assert found.claim_id == claim.claim_id

    def test_get_claim_not_found(self):
        """Should return None for nonexistent claim."""
        assert self.store.get_claim("nonexistent") is None

    def test_list_claims(self):
        """Should list all claims."""
        self.store.create_claim(make_claim_request())
        self.store.create_claim(make_claim_request())

        claims, total = self.store.list_claims()
        assert total == 2
        assert len(claims) == 2

    def test_list_claims_by_status(self):
        """Should filter claims by status."""
        self.store.create_claim(make_claim_request())
        claim2 = self.store.create_claim(make_claim_request())
        self.store.submit_claim(str(claim2.claim_id))

        claims, total = self.store.list_claims(claim_status="SUBMITTED")
        assert total == 1
        assert claims[0].claim_status == ClaimStatus.SUBMITTED

    def test_submit_claim(self):
        """Should transition DRAFT → SUBMITTED."""
        claim = self.store.create_claim(make_claim_request())
        updated = self.store.submit_claim(str(claim.claim_id))

        assert updated is not None
        assert updated.claim_status == ClaimStatus.SUBMITTED

    def test_submit_nonexistent_claim(self):
        """Should return None for nonexistent claim."""
        assert self.store.submit_claim("nonexistent") is None

    def test_settle_claim(self):
        """Should transition to SETTLED with auto-subsidy calculation."""
        claim = self.store.create_claim(make_claim_request())
        self.store.submit_claim(str(claim.claim_id))
        self.store.update_status(
            str(claim.claim_id),
            ClaimStatusUpdate(
                claim_status=ClaimStatus.APPROVED,
                insurance_responsibility_cents=10000,
                patient_responsibility_cents=5000,
            ),
        )
        settled = self.store.settle_claim(str(claim.claim_id))

        assert settled.claim_status == ClaimStatus.SETTLED
        assert settled.settled_at is not None
        # Subsidy = 15000 - 10000 - 5000 = 0
        assert settled.subsidy_applied_cents == 0

    def test_void_claim(self):
        """Should transition to VOIDED."""
        claim = self.store.create_claim(make_claim_request())
        voided = self.store.void_claim(str(claim.claim_id))

        assert voided.claim_status == ClaimStatus.VOIDED

    def test_summary(self):
        """Should aggregate claim statistics."""
        self.store.create_claim(make_claim_request())
        claim2 = self.store.create_claim(make_claim_request())
        self.store.submit_claim(str(claim2.claim_id))

        summary = self.store.get_summary()
        assert summary["total_claims"] == 2
        assert summary["by_status"]["DRAFT"] == 1
        assert summary["by_status"]["SUBMITTED"] == 1
        assert summary["total_charged_cents"] == 30000


# ─── API Tests ───────────────────────────────────────────────────────────────


class TestClaimsAPI:
    """Test claims API endpoints via TestClient."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        from fastapi.testclient import TestClient

        from src.api.app import app
        from src.models.auth import UserCreate, UserRole
        from src.services.auth_service import auth_service

        self.client = TestClient(app)

        # Ensure admin user exists for auth
        existing = {u.username for u in auth_service.list_users()}
        if "testclaimsadmin" not in existing:
            auth_service.register(
                UserCreate(
                    username="testclaimsadmin",
                    email="testclaimsadmin@test.example",
                    password="testclaimsadmin123",
                    full_name="Test Claims Admin",
                    role=UserRole.ADMIN,
                )
            )
        tokens = auth_service.login("testclaimsadmin", "testclaimsadmin123")
        self.headers = {"Authorization": f"Bearer {tokens.access_token}"}

    def test_create_claim(self):
        response = self.client.post(
            "/v1/claims",
            json={
                "encounter_id": "ENC-API-001",
                "patient_pseudo_id": str(uuid4()),
                "provider_org_id": str(uuid4()),
                "payer_id": "PAYER-001",
                "service_date": "2026-07-01",
                "line_items": [
                    {
                        "line_item_id": "L1",
                        "service_code": "99213",
                        "description": "Office visit",
                        "quantity": 1,
                        "unit_price_cents": 15000,
                        "total_cents": 15000,
                    }
                ],
                "diagnosis_codes": ["R07.9"],
            },
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["claim_status"] == "DRAFT"
        assert data["total_charged_cents"] == 15000

    def test_create_and_submit_claim(self):
        # Create
        create_resp = self.client.post(
            "/v1/claims",
            json={
                "encounter_id": "ENC-API-002",
                "patient_pseudo_id": str(uuid4()),
                "provider_org_id": str(uuid4()),
                "payer_id": "PAYER-001",
                "service_date": "2026-07-01",
                "line_items": [
                    {
                        "line_item_id": "L1",
                        "service_code": "99214",
                        "description": "Office visit complex",
                        "quantity": 1,
                        "unit_price_cents": 25000,
                        "total_cents": 25000,
                    }
                ],
                "diagnosis_codes": ["I10"],
            },
            headers=self.headers,
        )
        claim_id = create_resp.json()["claim_id"]

        # Submit
        submit_resp = self.client.post(
            f"/v1/claims/{claim_id}/submit",
            headers=self.headers,
        )
        assert submit_resp.status_code == 200
        assert submit_resp.json()["claim_status"] == "SUBMITTED"

    def test_get_claim(self):
        create_resp = self.client.post(
            "/v1/claims",
            json={
                "encounter_id": "ENC-API-003",
                "patient_pseudo_id": str(uuid4()),
                "provider_org_id": str(uuid4()),
                "payer_id": "PAYER-001",
                "service_date": "2026-07-01",
                "line_items": [
                    {
                        "line_item_id": "L1",
                        "service_code": "99213",
                        "description": "Visit",
                        "quantity": 1,
                        "unit_price_cents": 10000,
                        "total_cents": 10000,
                    }
                ],
                "diagnosis_codes": ["J06.9"],
            },
            headers=self.headers,
        )
        claim_id = create_resp.json()["claim_id"]

        get_resp = self.client.get(
            f"/v1/claims/{claim_id}",
            headers=self.headers,
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["claim_id"] == claim_id

    def test_get_nonexistent_claim(self):
        response = self.client.get(
            "/v1/claims/nonexistent",
            headers=self.headers,
        )
        assert response.status_code == 404

    def test_list_claims(self):
        response = self.client.get(
            "/v1/claims",
            headers=self.headers,
        )
        assert response.status_code == 200
        assert "total" in response.json()
        assert "claims" in response.json()

    def test_claim_summary(self):
        response = self.client.get(
            "/v1/claims/summary",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_claims" in data
        assert "by_status" in data
