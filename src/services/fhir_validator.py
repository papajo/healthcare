"""FHIR R4 resource validation layer."""

from __future__ import annotations

import re
from typing import Any

from src.models.fhir import (
    FHIROperationOutcome,
    FHIROperationOutcomeIssue,
)

REFERENCE_PATTERN = re.compile(r"^[A-Za-z]+/[A-Za-z0-9\-]+$")

# Required fields per resource type
REQUIRED_FIELDS: dict[str, list[str]] = {
    "Patient": ["name", "gender"],
    "Encounter": ["status", "class", "subject"],
    "Condition": ["subject"],
    "MedicationRequest": ["status", "intent", "subject"],
    "AllergyIntolerance": ["patient"],
    "Observation": ["status", "code", "subject"],
    "Claim": ["status", "patient", "provider"],
}

VALID_STATUSES: dict[str, list[str]] = {
    "Patient": [],
    "Encounter": ["planned", "arrived", "in-progress", "finished", "cancelled"],
    "Condition": [],
    "MedicationRequest": [
        "active", "on-hold", "cancelled", "completed",
        "entered-in-error", "stopped",
    ],
    "AllergyIntolerance": [],
    "Observation": ["registered", "preliminary", "final", "amended"],
    "Claim": ["active", "cancelled", "draft", "entered-in-error"],
    "Bundle": ["searchset", "collection", "transaction", "batch"],
}


def validate_resource(resource: dict[str, Any]) -> list[str]:
    """Validate a FHIR resource. Returns list of errors (empty = valid)."""
    errors: list[str] = []
    resource_type = resource.get("resourceType", "")

    if resource_type not in REQUIRED_FIELDS:
        errors.append(f"Unknown resourceType: {resource_type}")
        return errors

    # Check required fields
    for field in REQUIRED_FIELDS[resource_type]:
        value = resource.get(field)
        if value is None or value == "" or value == []:
            errors.append(f"Missing required field: {field}")

    # Validate references
    for ref_field in ("subject", "patient", "provider", "requester"):
        ref = resource.get(ref_field)
        if ref is not None and isinstance(ref, dict):
            ref_value = ref.get("reference", "")
            if ref_value and not REFERENCE_PATTERN.match(ref_value):
                errors.append(
                    f"Invalid reference format for {ref_field}: {ref_value!r}"
                )

    # Validate status if applicable
    valid_statuses = VALID_STATUSES.get(resource_type, [])
    status = resource.get("status")
    if valid_statuses and status and status not in valid_statuses:
        errors.append(
            f"Invalid status '{status}' for {resource_type}. "
            f"Must be one of: {valid_statuses}"
        )

    return errors


def make_operation_outcome(errors: list[str]) -> FHIROperationOutcome:
    """Create a FHIR OperationOutcome from a list of error messages."""
    issues = [
        FHIROperationOutcomeIssue(
            severity="error",
            code="invalid",
            diagnostics=err,
        )
        for err in errors
    ]
    return FHIROperationOutcome(issue=issues)
