"""CDS Hooks specification Pydantic models.

Follows the CDS Hooks v2.0 specification:
https://cds-hooks.org/

CDS Hooks is a FHIR-based specification for integrating clinical
decision support (CDS) into EHR workflows at the point of care.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ─── Request Models ──────────────────────────────────────────────────────────


class CDSContext(BaseModel):  # noqa: N815
    """Context passed to CDS services.

    Fields vary by hook type. The patientId field is required for all hooks.
    """

    patientId: str
    encounterId: str | None = None
    userId: str | None = None
    orderId: str | None = None
    selections: list[str] = Field(default_factory=list)
    draftOrders: dict[str, Any] | None = None
    action: str | None = None


class CDSHookRequest(BaseModel):  # noqa: N815
    """Request to a CDS service (cards endpoint).

    Sent by the EHR when a hook fires. Contains the hook identifier,
    a unique invocation ID, the context, and any pre-fetched FHIR resources.
    """

    hook: str
    hookInstance: str
    context: CDSContext
    prefetch: dict[str, Any] | None = None


# ─── Response Models ─────────────────────────────────────────────────────────


class CDSIndicator(str, Enum):
    """Card indicator — determines visual severity in the EHR UI."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CDSAction(BaseModel):  # noqa: N815
    """A single action within a CDS card.

    Actions describe what the EHR should do when the user accepts a suggestion.
    """

    label: str
    description: str | None = None
    uuid: str | None = None
    type: str = "create"
    descriptionUrl: str | None = None


class CDSSource(BaseModel):
    """Source information for a CDS card."""

    label: str
    url: str | None = None
    icon: str | None = None
    topic: CDSLink | None = None


class CDSSuggestion(BaseModel):  # noqa: N815
    """A suggestion within a CDS card.

    Suggestions present recommended actions to the clinician.
    """

    label: str
    uuid: str | None = None
    isRecommended: bool = False
    actions: list[CDSAction] = Field(default_factory=list)


class CDSLink(BaseModel):  # noqa: N815
    """A link within a CDS card."""

    label: str
    url: str
    type: str = "absolute"
    appleSmartAppUrl: str | None = None


class CDSCard(BaseModel):
    """A CDS card returned by a CDS service.

    Cards are the primary output of a CDS Hooks service. Each card
    conveys a single clinical recommendation or alert.
    """

    uuid: str | None = None
    summary: str
    indicator: CDSIndicator
    detail: str | None = None
    source: CDSSource
    suggestions: list[CDSSuggestion] = Field(default_factory=list)
    links: list[CDSLink] = Field(default_factory=list)


class CDSHookResponse(BaseModel):  # noqa: N815
    """Response from a CDS service."""

    cards: list[CDSCard] = Field(default_factory=list)
    systemActions: list[CDSAction] = Field(default_factory=list)


# ─── Discovery Models ────────────────────────────────────────────────────────


class CDSHookDefinition(BaseModel):  # noqa: N815
    """Definition of a supported CDS hook.

    Returned by the discovery endpoint so EHRs know which hooks
    this service implements and what prefetch data to supply.
    """

    id: str
    title: str
    description: str
    hook: str
    version: str
    fhirVersion: str = "4.0.1"
    fhirAuthentication: str = "oauth2"
    systemActions: list[CDSAction] = Field(default_factory=list)


class CDSDiscoveryResponse(BaseModel):
    """Discovery response listing all supported hooks."""

    services: list[CDSHookDefinition] = Field(default_factory=list)
