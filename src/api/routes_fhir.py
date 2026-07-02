"""FHIR R4 RESTful API routes — protected with role-based data scoping."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.api.deps import PatientScopeDep, require_role
from src.models.auth import UserRole
from src.services.fhir_store import SUPPORTED_RESOURCE_TYPES, fhir_store
from src.services.fhir_validator import make_operation_outcome, validate_resource

router = APIRouter()

FHIR_CONTENT_TYPE = "application/fhir+json"


class _FHIRJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime and other non-serializable types."""

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def _fhir_json(data: Any) -> str:
    """Serialize data to JSON string with datetime handling."""
    return json.dumps(data, cls=_FHIRJSONEncoder)


def _fhir_response(
    data: dict | list,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> Response:
    """Return a Response with FHIR content type and proper JSON serialization."""
    return Response(
        content=_fhir_json(data),
        status_code=status_code,
        media_type=FHIR_CONTENT_TYPE,
        headers=headers,
    )


# ─── Capability Statement (public) ──────────────────────────────────────────


@router.get(
    "/metadata",
    summary="Capability Statement",
    description="Returns the FHIR server capability statement.",
)
async def capability_statement():
    """Return FHIR R4 capability statement."""
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "security": {"cors": True},
                "resource": [
                    {
                        "type": rt,
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                        ],
                    }
                    for rt in sorted(SUPPORTED_RESOURCE_TYPES)
                ],
            }
        ],
    }


# ─── Generic CRUD (protected) ───────────────────────────────────────────────


def _extract_patient_id(resource: dict[str, Any]) -> str | None:
    """Extract the FHIR Patient ID from a resource's subject/patient reference."""
    for field in ("subject", "patient"):
        ref = resource.get(field)
        if isinstance(ref, dict):
            ref_str = ref.get("reference", "")
            if ref_str.startswith("Patient/"):
                return ref_str.split("/", 1)[1]
    return None


@router.get(
    "/{resource_type}",
    summary="Search resources",
    description="Search for FHIR resources of a given type.",
)
async def search_resources(
    resource_type: str,
    scope: PatientScopeDep,
    _id: str | None = Query(default=None),
    patient: str | None = Query(default=None),
    subject: str | None = Query(default=None),
    status: str | None = Query(default=None),
    code: str | None = Query(default=None),
    date: str | None = Query(default=None),
    identifier: str | None = Query(default=None),
    _count: int = Query(default=20, ge=1, le=100),
    _offset: int = Query(default=0, ge=0),
):
    """Search resources with FHIR search parameters.

    Results are scoped by the authenticated user's role:
    - Admin/System/Nurse: all resources
    - Clinician: only assigned patients
    - Patient: only own records
    """
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(
            status_code=404,
            detail=f"Resource type not supported: {resource_type}",
        )

    params: dict[str, str] = {}
    if _id:
        params["_id"] = _id
    if patient:
        params["patient"] = patient
    if subject:
        params["subject"] = subject
    if status:
        params["status"] = status
    if code:
        params["code"] = code
    if date:
        params["date"] = date
    if identifier:
        params["identifier"] = identifier

    bundle = fhir_store.search(resource_type, params)

    # Apply patient-scoping filter
    if scope.patient_ids is not None:
        filtered_entries = []
        for entry in bundle.entry:
            res = entry.resource
            # For Patient resources, check the resource id directly
            if resource_type == "Patient":
                if res.get("id") in scope.patient_ids:
                    filtered_entries.append(entry)
            else:
                # For other resources, check the subject/patient reference
                pid = _extract_patient_id(res)
                if pid and pid in scope.patient_ids:
                    filtered_entries.append(entry)
        bundle.entry = filtered_entries
        bundle.total = len(filtered_entries)

    # Apply pagination
    all_entries = bundle.entry
    paginated = all_entries[_offset : _offset + _count]
    bundle.entry = paginated
    bundle.total = len(all_entries)

    return _fhir_response(bundle.model_dump(by_alias=True, exclude_none=True))


@router.get(
    "/{resource_type}/{resource_id}",
    summary="Read resource",
    description="Read a single FHIR resource by id.",
)
async def read_resource(
    resource_type: str,
    resource_id: str,
    scope: PatientScopeDep,
):
    """Read a single resource with patient-scoping."""
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(
            status_code=404,
            detail=f"Resource type not supported: {resource_type}",
        )

    resource = fhir_store.read(resource_type, resource_id)
    if resource is None:
        raise HTTPException(
            status_code=404,
            detail=f"{resource_type}/{resource_id} not found",
        )

    # Check patient access
    if scope.patient_ids is not None:
        if resource_type == "Patient":
            if resource_id not in scope.patient_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied to this patient",
                )
        else:
            pid = _extract_patient_id(resource)
            if pid and pid not in scope.patient_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied to this patient's data",
                )

    return _fhir_response(resource)


@router.post(
    "/{resource_type}",
    status_code=201,
    summary="Create resource",
    description="Create a new FHIR resource.",
    dependencies=[
        Depends(
            require_role(
                UserRole.CLINICIAN, UserRole.NURSE,
                UserRole.ADMIN, UserRole.SYSTEM,
            )
        )
    ],
)
async def create_resource(
    resource_type: str,
    resource: dict[str, Any],
    scope: PatientScopeDep,
):
    """Create a new resource (clinician/nurse/admin only)."""
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(
            status_code=404,
            detail=f"Resource type not supported: {resource_type}",
        )

    resource["resourceType"] = resource_type
    errors = validate_resource(resource)
    if errors:
        outcome = make_operation_outcome(errors)
        return _fhir_response(
            outcome.model_dump(by_alias=True, exclude_none=True),
            status_code=422,
        )

    # Clinicians can only create resources for assigned patients
    if scope.patient_ids is not None and resource_type != "Patient":
        pid = _extract_patient_id(resource)
        if pid and pid not in scope.patient_ids:
            raise HTTPException(
                status_code=403,
                detail="Cannot create resources for unassigned patients",
            )

    created = fhir_store.create(resource_type, resource)
    location = f"/fhir/{resource_type}/{created['id']}"

    return _fhir_response(created, status_code=201, headers={"Location": location})


@router.put(
    "/{resource_type}/{resource_id}",
    summary="Update resource",
    description="Update an existing FHIR resource.",
    dependencies=[
        Depends(
            require_role(
                UserRole.CLINICIAN, UserRole.NURSE,
                UserRole.ADMIN, UserRole.SYSTEM,
            )
        )
    ],
)
async def update_resource(
    resource_type: str,
    resource_id: str,
    resource: dict[str, Any],
    scope: PatientScopeDep,
):
    """Update an existing resource (clinician/nurse/admin only)."""
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(
            status_code=404,
            detail=f"Resource type not supported: {resource_type}",
        )

    existing = fhir_store.read(resource_type, resource_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"{resource_type}/{resource_id} not found",
        )

    # Check access
    if scope.patient_ids is not None:
        if resource_type == "Patient":
            if resource_id not in scope.patient_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied to this patient",
                )
        else:
            pid = _extract_patient_id(existing)
            if pid and pid not in scope.patient_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied to this patient's data",
                )

    resource["resourceType"] = resource_type
    resource["id"] = resource_id
    errors = validate_resource(resource)
    if errors:
        outcome = make_operation_outcome(errors)
        return _fhir_response(
            outcome.model_dump(by_alias=True, exclude_none=True),
            status_code=422,
        )

    updated = fhir_store.update(resource_type, resource_id, resource)
    location = f"/fhir/{resource_type}/{resource_id}"

    return _fhir_response(updated, headers={"Location": location})


@router.delete(
    "/{resource_type}/{resource_id}",
    status_code=204,
    summary="Delete resource",
    description="Delete a FHIR resource.",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.SYSTEM))],
)
async def delete_resource(resource_type: str, resource_id: str):
    """Delete a resource (admin/system only)."""
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(
            status_code=404,
            detail=f"Resource type not supported: {resource_type}",
        )

    deleted = fhir_store.delete(resource_type, resource_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"{resource_type}/{resource_id} not found",
        )

    return _fhir_response({}, status_code=204)


# ─── Patient $everything ─────────────────────────────────────────────────────


@router.get(
    "/Patient/{patient_id}/$everything",
    summary="Patient everything",
    description="Return all resources related to a patient.",
)
async def patient_everything(patient_id: str, scope: PatientScopeDep):
    """Return all resources for a patient as a Bundle, scoped to user access."""
    if scope.patient_ids is not None and patient_id not in scope.patient_ids:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this patient",
        )

    patient = fhir_store.read("Patient", patient_id)
    if patient is None:
        raise HTTPException(
            status_code=404,
            detail=f"Patient/{patient_id} not found",
        )

    related = fhir_store.search_by_patient(patient_id)

    all_resources = [patient] + related
    bundle = fhir_store.create_bundle("collection", all_resources)

    return _fhir_response(bundle.model_dump(by_alias=True, exclude_none=True))
