"""CDS Hooks API routes.

Implements the CDS Hooks specification endpoints:
- GET  /cds/services         — Discovery (list all available hooks)
- POST /cds/services/{hook}  — Execute a CDS hook (returns cards)
- GET  /cds/services/{hook}/view — Get hook details

Reference: https://cds-hooks.org/
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from src.models.cds_hooks import CDSHookRequest
from src.services.cds_hooks import cds_hooks_service

router = APIRouter()

CDS_CONTENT_TYPE = "application/json"


def _cds_json_response(data: dict | list, status_code: int = 200):
    """Return a JSON response with CDS content type."""
    from fastapi.responses import Response

    return Response(
        content=json.dumps(data, default=str),
        status_code=status_code,
        media_type=CDS_CONTENT_TYPE,
    )


# ─── Discovery ───────────────────────────────────────────────────────────────


@router.get(
    "/services",
    summary="CDS Hooks Discovery",
    description="Returns the list of all available CDS hooks.",
)
async def discovery():
    """CDS Hooks discovery endpoint.

    Returns all registered hooks so the EHR knows which services
    are available and what context to supply.
    """
    response = cds_hooks_service.discover()
    return _cds_json_response(
        response.model_dump(exclude_none=True, exclude_defaults=True)
    )


# ─── Execute Hook ────────────────────────────────────────────────────────────


@router.post(
    "/services/{hook_id}",
    summary="Execute CDS Hook",
    description="Execute a CDS hook and return clinical decision support cards.",
)
async def execute_hook(hook_id: str, request: CDSHookRequest):
    """Execute a CDS hook.

    The EHR sends a POST request when a hook fires. The service
    processes clinical data and returns decision support cards.
    """
    # Validate hook exists
    definition = cds_hooks_service.get_hook_definition(hook_id)
    if definition is None:
        raise HTTPException(
            status_code=404,
            detail=f"CDS hook not found: {hook_id}",
        )

    # Validate hook type matches
    if definition.hook != request.hook:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Hook type mismatch: endpoint expects '{definition.hook}', "
                f"request contains '{request.hook}'"
            ),
        )

    response = cds_hooks_service.execute_hook(hook_id, request)
    return _cds_json_response(
        response.model_dump(exclude_none=True, exclude_defaults=True)
    )


# ─── Hook Details ────────────────────────────────────────────────────────────


@router.get(
    "/services/{hook_id}/view",
    summary="View CDS Hook Details",
    description="Get details about a specific CDS hook.",
)
async def view_hook(hook_id: str):
    """Get details about a specific CDS hook."""
    definition = cds_hooks_service.get_hook_definition(hook_id)
    if definition is None:
        raise HTTPException(
            status_code=404,
            detail=f"CDS hook not found: {hook_id}",
        )

    return _cds_json_response(
        definition.model_dump(exclude_none=True, exclude_defaults=True)
    )
