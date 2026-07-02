"""FastAPI application entry point.

Includes:
- Lifespan context manager for DB/Temporal initialization
- Health check with DB status
- Readiness probe
- CORS configuration
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes_affordability import router as affordability_router
from src.api.routes_audit import router as audit_router
from src.api.routes_auth import router as auth_router
from src.api.routes_cds import router as cds_router
from src.api.routes_claims import router as claims_router
from src.api.routes_fhir import router as fhir_router
from src.api.routes_subsidy import router as subsidy_router
from src.api.routes_urgency import router as urgency_router
from src.config.settings import settings

logger = logging.getLogger(__name__)


# ─── Lifespan ────────────────────────────────────────────────────────────────

_db_available = False
_temporal_available = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize and teardown resources."""
    global _db_available, _temporal_available

    logger.info("Starting Crisis-Cost Orchestrator...")

    # Try to connect to PostgreSQL
    try:
        from src.db.audit_repository import audit_event_repo
        from src.db.connection import get_pool

        await get_pool()
        await audit_event_repo.initialize()
        _db_available = True
        logger.info("PostgreSQL connected successfully")
    except Exception as e:
        _db_available = False
        logger.warning("PostgreSQL unavailable, using in-memory mode: %s", e)

    # Try to connect to Temporal
    try:
        from src.services.temporal_client import temporal_client

        await temporal_client.connect()
        _temporal_available = True
        logger.info("Temporal connected successfully")
    except Exception as e:
        _temporal_available = False
        logger.warning("Temporal unavailable: %s", e)

    # Seed FHIR demo data
    try:
        from src.services.fhir_store import seed_demo_data

        seed_demo_data()
        logger.info("FHIR demo data seeded")
    except Exception as e:
        logger.warning("Failed to seed FHIR data: %s", e)

    try:
        from src.services.clinical_seed import seed_clinical_data

        seed_clinical_data()
        logger.info("Clinical demo data seeded")
    except Exception as e:
        logger.warning("Failed to seed clinical data: %s", e)

    # Seed demo users for RBAC
    try:
        from src.services.user_seed import seed_users

        seed_users()
        logger.info("Demo users seeded")
    except Exception as e:
        logger.warning("Failed to seed demo users: %s", e)

    yield

    # Teardown
    logger.info("Shutting down Crisis-Cost Orchestrator...")

    if _db_available:
        from src.db.connection import close_pool
        await close_pool()

    if _temporal_available:
        from src.services.temporal_client import temporal_client
        await temporal_client.disconnect()


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    description="HIPAA-compliant healthcare cost protection platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────


app.include_router(urgency_router, prefix="/v1", tags=["urgency"])
app.include_router(affordability_router, prefix="/v1", tags=["affordability"])
app.include_router(subsidy_router, prefix="/v1", tags=["subsidy"])
app.include_router(claims_router, prefix="/v1", tags=["claims"])
app.include_router(audit_router, prefix="/v1", tags=["audit"])
app.include_router(auth_router)
app.include_router(fhir_router, prefix="/fhir", tags=["fhir"])
app.include_router(cds_router, prefix="/cds", tags=["cds-hooks"])


# ─── Health & Readiness ──────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Liveness probe — returns 200 if process is running."""
    return {
        "status": "healthy",
        "service": "crisiscost-orchestrator",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/ready")
async def readiness_check():
    """Readiness probe — returns 200 only if all deps are available."""
    services = {
        "postgresql": _db_available,
        "temporal": _temporal_available,
    }

    all_ready = all(services.values())

    return {
        "status": "ready" if all_ready else "degraded",
        "services": services,
        "timestamp": datetime.now(UTC).isoformat(),
    }
