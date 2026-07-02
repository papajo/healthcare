"""Seed demo users for RBAC testing.

Creates one user per role:
- admin   (password: admin123)
- doctor  (password: doctor123) — assigned to clinical-patient-001 and -003
- nurse   (password: nurse123)  — full read access
- patient (password: patient123) — linked to clinical-patient-002

All passwords meet the 8-char minimum and use bcrypt hashing.
"""

from __future__ import annotations

import logging

from src.models.auth import UserCreate, UserRole
from src.services.auth_service import auth_service

logger = logging.getLogger(__name__)


def seed_users() -> None:
    """Create demo users if they don't already exist."""
    existing = {u.username for u in auth_service.list_users()}
    if existing:
        logger.info("Users already seeded, skipping")
        return

    users = [
        UserCreate(
            username="admin",
            email="admin@hospital.example.org",
            password="admin123",
            full_name="Clinical Admin",
            role=UserRole.ADMIN,
        ),
        UserCreate(
            username="doctor",
            email="doctor@hospital.example.org",
            password="doctor123",
            full_name="Dr. Sarah Chen",
            role=UserRole.CLINICIAN,
            assigned_patient_ids=[
                "clinical-patient-001",
                "clinical-patient-003",
                "clinical-patient-005",
            ],
        ),
        UserCreate(
            username="nurse",
            email="nurse@hospital.example.org",
            password="nurse123",
            full_name="Nurse James Wilson",
            role=UserRole.NURSE,
        ),
        UserCreate(
            username="patient",
            email="maria.garcia@example.com",
            password="patient123",
            full_name="Maria Garcia",
            role=UserRole.PATIENT,
            fhir_patient_id="clinical-patient-002",
        ),
    ]

    for user in users:
        try:
            auth_service.register(user)
            logger.info("Seeded user: %s (%s)", user.username, user.role.value)
        except ValueError:
            logger.debug("User %s already exists", user.username)

    logger.info(
        "User seed complete — %d demo accounts available",
        len(auth_service.list_users()),
    )
