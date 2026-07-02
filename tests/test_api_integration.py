"""Integration tests for API endpoints."""

from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.app import app
from src.models.auth import UserCreate, UserRole
from src.services.auth_service import auth_service

client = TestClient(app)


# ─── Auth helpers ────────────────────────────────────────────────────────────


def _ensure_admin():
    """Create admin user if not already seeded, return login token."""
    existing = {u.username for u in auth_service.list_users()}
    if "testadmin" not in existing:
        auth_service.register(
            UserCreate(
                username="testadmin",
                email="testadmin@test.example",
                password="testadmin123",
                full_name="Test Admin",
                role=UserRole.ADMIN,
            )
        )
    tokens = auth_service.login("testadmin", "testadmin123")
    return tokens.access_token


ADMIN_TOKEN = _ensure_admin()
AUTH_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}


# ─── Health Check ────────────────────────────────────────────────────────────


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


# ─── Readiness Check ─────────────────────────────────────────────────────────


def test_readiness_check():
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ready", "degraded")
    assert "postgresql" in data["services"]
    assert "temporal" in data["services"]


# ─── Affordability Calculation ───────────────────────────────────────────────


def test_affordability_calculation():
    response = client.post(
        "/v1/affordability/calculate",
        json={
            "encounter_id": "ENC-API-001",
            "patient_pseudo_id": str(uuid4()),
            "urgency_label": "URGENT",
            "estimated_total_cents": 5_000_000,
            "encounter_class": "EMERGENCY",
            "eligibility_proof": {
                "proof_id": str(uuid4()),
                "income_bracket_code": "IB-06",
                "affordability_tier": "TIER-STANDARD",
                "eligibility_status_normalized": "ELIGIBLE",
                "verification_assurance_level": "HIGH",
                "proof_valid_from": "2026-01-01T00:00:00Z",
                "proof_valid_to": "2026-12-31T23:59:59Z",
                "revocation_status": "ACTIVE",
                "patient_pseudo_id": str(uuid4()),
            },
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tier_applied"] == "TIER-STANDARD"
    assert data["patient_responsibility_cents"] == 312_500
    assert data["subsidy_amount_cents"] == 4_687_500


def test_affordability_calculation_no_proof():
    response = client.post(
        "/v1/affordability/calculate",
        json={
            "encounter_id": "ENC-API-002",
            "patient_pseudo_id": str(uuid4()),
            "urgency_label": "ROUTINE",
            "estimated_total_cents": 1_000_000,
            "encounter_class": "OUTPATIENT",
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tier_applied"] == "TIER-UNVERIFIED"
    assert data["patient_responsibility_cents"] == 1_000_000
    assert data["subsidy_amount_cents"] == 0


def test_affordability_calculation_invalid_bracket():
    response = client.post(
        "/v1/affordability/calculate",
        json={
            "encounter_id": "ENC-API-003",
            "patient_pseudo_id": str(uuid4()),
            "urgency_label": "URGENT",
            "estimated_total_cents": 1_000_000,
            "encounter_class": "EMERGENCY",
            "eligibility_proof": {
                "proof_id": str(uuid4()),
                "income_bracket_code": "IB-INVALID",
                "affordability_tier": "TIER-STANDARD",
                "eligibility_status_normalized": "ELIGIBLE",
                "verification_assurance_level": "HIGH",
                "proof_valid_from": "2026-01-01T00:00:00Z",
                "proof_valid_to": "2026-12-31T23:59:59Z",
                "revocation_status": "ACTIVE",
                "patient_pseudo_id": str(uuid4()),
            },
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 400
    assert "Unknown income bracket" in response.json()["detail"]


# ─── Subsidy Endpoints ──────────────────────────────────────────────────────


def test_create_and_get_subsidy():
    patient_id = str(uuid4())
    provider_id = str(uuid4())

    # Create
    create_response = client.post(
        "/v1/subsidies",
        json={
            "encounter_id": "ENC-API-004",
            "patient_pseudo_id": patient_id,
            "provider_org_id": provider_id,
            "subsidy_amount_cents": 500_000,
        },
        headers=AUTH_HEADERS,
    )
    assert create_response.status_code == 200
    subsidy_id = create_response.json()["subsidy_id"]
    assert create_response.json()["subsidy_status"] == "PENDING"

    # Get
    get_response = client.get(
        f"/v1/subsidies/{subsidy_id}",
        headers=AUTH_HEADERS,
    )
    assert get_response.status_code == 200
    assert get_response.json()["subsidy_id"] == subsidy_id


def test_settle_subsidy():
    # Create
    create_response = client.post(
        "/v1/subsidies",
        json={
            "encounter_id": "ENC-API-005",
            "patient_pseudo_id": str(uuid4()),
            "provider_org_id": str(uuid4()),
            "subsidy_amount_cents": 250_000,
        },
        headers=AUTH_HEADERS,
    )
    subsidy_id = create_response.json()["subsidy_id"]

    # Settle
    settle_response = client.post(
        f"/v1/subsidies/{subsidy_id}/settle",
        headers=AUTH_HEADERS,
    )
    assert settle_response.status_code == 200
    assert settle_response.json()["subsidy_status"] == "SETTLED"
    assert settle_response.json()["payment_reference"] is not None


def test_cancel_subsidy():
    # Create
    create_response = client.post(
        "/v1/subsidies",
        json={
            "encounter_id": "ENC-API-006",
            "patient_pseudo_id": str(uuid4()),
            "provider_org_id": str(uuid4()),
            "subsidy_amount_cents": 100_000,
        },
        headers=AUTH_HEADERS,
    )
    subsidy_id = create_response.json()["subsidy_id"]

    # Cancel
    cancel_response = client.post(
        f"/v1/subsidies/{subsidy_id}/cancel?reason=no longer needed",
        headers=AUTH_HEADERS,
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["subsidy_status"] == "CANCELLED"


def test_get_nonexistent_subsidy():
    fake_id = str(uuid4())
    response = client.get(
        f"/v1/subsidies/{fake_id}",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 404


# ─── Audit Endpoints ────────────────────────────────────────────────────────


def test_audit_events_query():
    response = client.get("/v1/audit/events", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "events" in data


def test_audit_integrity_check():
    response = client.get("/v1/audit/verify", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["chain_status"] in ("VALID", "INVALID")


# ─── Unauthorized access ────────────────────────────────────────────────────


def test_unauthorized_returns_401():
    """Protected endpoints return 401 without a token."""
    response = client.get("/v1/audit/events")
    assert response.status_code == 401


def test_fhir_requires_auth():
    """FHIR search requires authentication."""
    response = client.get("/fhir/Patient")
    assert response.status_code == 401
