"""Tests for SMART on FHIR auth system."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.models.auth import Scope, UserRole
from src.services.auth_service import auth_service

client = TestClient(app)


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_auth_service():
    """Clear auth state between tests."""
    auth_service._users.clear()
    auth_service._blacklisted_refresh.clear()
    yield
    auth_service._users.clear()
    auth_service._blacklisted_refresh.clear()


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _register_patient(
    username: str = "testpatient",
    email: str = "patient@test.com",
    password: str = "securepass123",
) -> dict:
    resp = client.post(
        "/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": "Test Patient",
            "role": "PATIENT",
        },
    )
    return resp.json()


def _login(username: str = "testpatient", password: str = "securepass123") -> dict:
    resp = client.post(
        "/v1/auth/login",
        json={"username": username, "password": password},
    )
    return resp.json()


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _bootstrap_admin(
    username: str = "admin1",
    password: str = "adminpass123",
) -> dict:
    """Create an admin user directly via service and return tokens."""
    auth_service.register(
        __import__("src.models.auth", fromlist=["UserCreate"]).UserCreate(
            username=username,
            email=f"{username}@test.com",
            password=password,
            full_name="Admin",
            role=UserRole.ADMIN,
        )
    )
    return auth_service.login(username, password)


# ─── Registration ─────────────────────────────────────────────────────────────


def test_register_patient_success():
    resp = client.post(
        "/v1/auth/register",
        json={
            "username": "newpatient",
            "email": "new@test.com",
            "password": "securepass123",
            "full_name": "New Patient",
            "role": "PATIENT",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newpatient"
    assert data["role"] == "PATIENT"
    assert data["is_active"] is True
    assert "user_id" in data


def test_register_duplicate_username():
    _register_patient(username="dupuser", email="dup1@test.com")
    resp = client.post(
        "/v1/auth/register",
        json={
            "username": "dupuser",
            "email": "dup2@test.com",
            "password": "securepass123",
            "full_name": "Dup",
            "role": "PATIENT",
        },
    )
    assert resp.status_code == 409


def test_register_missing_fields():
    resp = client.post(
        "/v1/auth/register",
        json={"username": "x"},
    )
    assert resp.status_code == 422


def test_register_non_patient_forbidden():
    resp = client.post(
        "/v1/auth/register",
        json={
            "username": "tryadmin",
            "email": "admin@test.com",
            "password": "securepass123",
            "full_name": "Try Admin",
            "role": "ADMIN",
        },
    )
    assert resp.status_code == 403


# ─── Login ────────────────────────────────────────────────────────────────────


def test_login_success():
    _register_patient(username="logintest", email="login@test.com")
    resp = client.post(
        "/v1/auth/login",
        json={"username": "logintest", "password": "securepass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800


def test_login_wrong_password():
    _register_patient(username="wrongpw", email="wp@test.com")
    resp = client.post(
        "/v1/auth/login",
        json={"username": "wrongpw", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_login_nonexistent_user():
    resp = client.post(
        "/v1/auth/login",
        json={"username": "ghost", "password": "securepass123"},
    )
    assert resp.status_code == 401


# ─── Token Refresh ────────────────────────────────────────────────────────────


def test_refresh_success():
    _register_patient(username="refreshtest", email="refresh@test.com")
    tokens = _login("refreshtest")
    resp = client.post(
        "/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_invalid_token():
    resp = client.post(
        "/v1/auth/refresh",
        json={"refresh_token": "garbage.token.value"},
    )
    assert resp.status_code == 401


def test_refresh_with_access_token():
    """Sending an access token as refresh should fail."""
    _register_patient(username="wrongrefresh", email="wr@test.com")
    tokens = _login("wrongrefresh")
    resp = client.post(
        "/v1/auth/refresh",
        json={"refresh_token": tokens["access_token"]},
    )
    assert resp.status_code == 401


# ─── Protected Endpoints ─────────────────────────────────────────────────────


def test_me_without_token():
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_valid_token():
    _register_patient(username="metest", email="me@test.com")
    tokens = _login("metest")
    resp = client.get(
        "/v1/auth/me",
        headers=_auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "metest"


def test_me_with_invalid_token():
    resp = client.get(
        "/v1/auth/me",
        headers=_auth_header("invalid.jwt.token"),
    )
    assert resp.status_code == 401


# ─── Role-Based Access ────────────────────────────────────────────────────────


def test_clinician_cannot_access_admin_user_list():
    _register_patient(username="clinician1", email="clin@test.com")
    tokens = _login("clinician1")
    # Override role to CLINICIAN for this test
    user = auth_service._find_user_by_username("clinician1")
    user.role = UserRole.CLINICIAN

    resp = client.get(
        "/v1/auth/users",
        headers=_auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 403


def test_admin_can_access_admin_user_list():
    admin_tokens = _bootstrap_admin("admlist1")

    resp = client.get(
        "/v1/auth/users",
        headers=_auth_header(admin_tokens.access_token),
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ─── Scope Verification ──────────────────────────────────────────────────────


def test_patient_token_has_patient_read_scope():
    _register_patient(username="scopetest", email="scope@test.com")
    tokens = _login("scopetest")
    assert "patient/Patient.read" in tokens["scope"]


def test_patient_token_lacks_user_admin_scope():
    _register_patient(username="scopeadmin", email="sadmin@test.com")
    tokens = _login("scopeadmin")
    assert "user/*.admin" not in tokens["scope"]


def test_verify_scope_true():
    _register_patient(username="vscope", email="vs@test.com")
    tokens = _login("vscope")
    assert auth_service.verify_scope(tokens["access_token"], Scope.PATIENT_READ) is True


def test_verify_scope_false():
    _register_patient(username="vscope2", email="vs2@test.com")
    tokens = _login("vscope2")
    assert auth_service.verify_scope(tokens["access_token"], Scope.USER_ADMIN) is False


def test_verify_scope_bad_token():
    assert auth_service.verify_scope("bad.token.value", Scope.PATIENT_READ) is False


# ─── Logout ───────────────────────────────────────────────────────────────────


def test_logout_invalidates_refresh_token():
    _register_patient(username="logouttest", email="logout@test.com")
    tokens = _login("logouttest")

    # Logout
    resp = client.post(
        "/v1/auth/logout",
        headers=_auth_header(tokens["access_token"]),
    )
    assert resp.status_code == 200

    # Try to use refresh token — should fail
    resp = client.post(
        "/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 401


# ─── Admin User Management ───────────────────────────────────────────────────


def test_admin_create_user_and_deactivate():
    admin_tokens = _bootstrap_admin("admcr8")
    headers = _auth_header(admin_tokens.access_token)

    # Create nurse
    resp = client.post(
        "/v1/auth/users",
        headers=headers,
        json={
            "username": "nurse1",
            "email": "nurse1@test.com",
            "password": "securepass123",
            "full_name": "Nurse One",
            "role": "NURSE",
        },
    )
    assert resp.status_code == 201
    nurse_id = resp.json()["user_id"]

    # List users
    resp = client.get("/v1/auth/users", headers=headers)
    assert resp.status_code == 200
    usernames = [u["username"] for u in resp.json()]
    assert "nurse1" in usernames

    # Deactivate nurse
    resp = client.delete(f"/v1/auth/users/{nurse_id}", headers=headers)
    assert resp.status_code == 204


# ─── Duplicate Email ──────────────────────────────────────────────────────────


def test_register_duplicate_email():
    _register_patient(username="email1", email="same@test.com")
    resp = client.post(
        "/v1/auth/register",
        json={
            "username": "email2",
            "email": "same@test.com",
            "password": "securepass123",
            "full_name": "Email Two",
            "role": "PATIENT",
        },
    )
    assert resp.status_code == 409


# ─── Deactivated User ─────────────────────────────────────────────────────────


def test_deactivated_user_cannot_login():
    admin_tokens = _bootstrap_admin("admdeact")
    headers = _auth_header(admin_tokens.access_token)

    # Create patient
    resp = client.post(
        "/v1/auth/register",
        json={
            "username": "deactpat",
            "email": "deactpat@test.com",
            "password": "securepass123",
            "full_name": "Deact Patient",
            "role": "PATIENT",
        },
    )
    pat_id = resp.json()["user_id"]

    # Deactivate
    client.delete(f"/v1/auth/users/{pat_id}", headers=headers)

    # Try login
    resp = client.post(
        "/v1/auth/login",
        json={"username": "deactpat", "password": "securepass123"},
    )
    assert resp.status_code == 401
