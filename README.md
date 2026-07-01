# Crisis-Cost Orchestrator

[![CI/CD](https://github.com/papajo/healthcare/actions/workflows/ci.yml/badge.svg)](https://github.com/papajo/healthcare/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

HIPAA-compliant healthcare cost protection platform that eliminates medical bankruptcy by classifying care urgency, capping patient costs at 10% of income, and orchestrating instant provider subsidies.

---

## Overview

The Crisis-Cost Orchestrator sits between clinical intake and financial settlement. When a patient arrives, the platform:

1. **Classifies urgency** — hybrid rule-based + LLM classifier (CRITICAL recall ≥ 0.98)
2. **Calculates affordability** — caps patient responsibility at 10% of verified income using a deterministic tier engine
3. **Orchestrates subsidies** — instant provider payments via ACH/Wire/Stablecoin through a durable Temporal workflow
4. **Maintains audit trail** — append-only, SHA-256-chained ledger with daily integrity verification
5. **Manages claims** — full claim lifecycle from draft through settlement with insurance adjudication

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Patient Dashboard                         │
│                   React + TypeScript + Tailwind                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                     FastAPI Application                          │
│  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌────────┐ ┌───────┐ │
│  │  F-01    │ │   F-02     │ │   F-03   │ │ F-06   │ │Claims │ │
│  │ Urgency  │ │Affordability│ │ Subsidy  │ │ Audit  │ │       │ │
│  │Classifier│ │  Engine    │ │Orchestr. │ │ Ledger │ │       │ │
│  └────┬─────┘ └─────┬──────┘ └────┬─────┘ └───┬────┘ └───┬───┘ │
└───────┼──────────────┼────────────┼────────────┼──────────┼─────┘
        │              │            │            │          │
        ▼              ▼            ▼            ▼          ▼
   ┌─────────┐   ┌──────────┐  ┌────────┐  ┌────────┐  ┌───────┐
   │  Rules  │   │  12 Tax  │  │Temporal│  │Postgres│  │In-    │
   │  + LLM  │   │ Brackets │  │  .io   │  │  QLDB  │  │Memory │
   └─────────┘   └──────────┘  └────────┘  └────────┘  └───────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, Pydantic v2 |
| **Frontend** | React 19, TypeScript 6, Vite 8, Tailwind CSS 4 |
| **Database** | PostgreSQL 16, Amazon QLDB (audit) |
| **Orchestration** | Temporal.io 1.24 |
| **Cache** | Redis 7 |
| **CI/CD** | GitHub Actions |
| **Container** | Docker multi-stage build |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose (optional, for PostgreSQL/Temporal)

### Local Development

```bash
# Clone
git clone git@github.com:papajo/healthcare.git
cd healthcare

# Install Python deps
pip install -e ".[dev]"

# Install frontend deps
cd frontend && npm install && cd ..

# Start services (in-memory mode — no Docker needed)
./start.sh --fg
```

The API runs at `http://localhost:8000` and the dashboard at `http://localhost:5173`.

### With Docker (full stack)

```bash
# Start PostgreSQL + Redis + Temporal
docker compose up -d

# Start the API
./start.sh --fg
```

### Run the Demo

```bash
# In another terminal
./demo.sh
```

This walks through the full flow: urgency classification → affordability calculation → subsidy creation → claim processing → audit verification.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/urgency/classify` | Classify encounter urgency (F-01) |
| `POST` | `/v1/affordability/calculate` | Calculate patient responsibility (F-02) |
| `POST` | `/v1/subsidies` | Create a subsidy record (F-03) |
| `POST` | `/v1/subsidies/{id}/settle` | Settle a subsidy via payment rail |
| `GET` | `/v1/audit/events` | Query immutable audit events (F-06) |
| `GET` | `/v1/audit/verify` | Verify audit chain integrity |
| `POST` | `/v1/claims` | Create a new claim |
| `POST` | `/v1/claims/{id}/submit` | Submit claim for review |
| `PATCH` | `/v1/claims/{id}/status` | Update claim status |
| `POST` | `/v1/claims/{id}/settle` | Settle claim |
| `GET` | `/v1/claims/summary` | Aggregate claim statistics |

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

**114 tests** across service logic, API integration, and end-to-end flows.

## Project Structure

```
healthcare/
├── src/
│   ├── api/                    # FastAPI routes + app
│   │   ├── app.py              # Lifespan, CORS, health probes
│   │   ├── routes_urgency.py   # F-01 classification endpoint
│   │   ├── routes_affordability.py  # F-02 affordability engine
│   │   ├── routes_subsidy.py   # F-03 subsidy orchestration
│   │   ├── routes_claims.py    # Claims CRUD + lifecycle
│   │   └── routes_audit.py     # F-06 audit ledger queries
│   ├── services/               # Business logic
│   │   ├── urgency_classifier.py    # Rule-based + LLM classifier
│   │   ├── affordability_engine.py  # Deterministic tier calculator
│   │   ├── subsidy_orchestrator.py  # Subsidy store
│   │   ├── temporal_client.py       # Temporal workflow + activities
│   │   ├── audit_ledger.py          # Append-only event store
│   │   ├── audit_projection.py      # PostgreSQL projection
│   │   └── claims_service.py        # Claim lifecycle manager
│   ├── db/                     # Database layer
│   │   ├── connection.py       # Async PostgreSQL pool
│   │   ├── audit_repository.py # Audit event queries
│   │   └── migrations.py       # Schema migrations
│   ├── models/
│   │   ├── domain.py           # Domain models + enums
│   │   └── f04_request.py      # F-04 request schema
│   └── config/
│       └── settings.py         # Pydantic settings
├── frontend/                   # React dashboard
│   └── src/
│       ├── pages/Dashboard.tsx # Main dashboard
│       ├── api/client.ts       # API client
│       └── types/api.ts        # TypeScript types
├── tests/                      # 114 tests
├── schemas/                    # JSON schemas
├── security/                   # Security protocols
├── docs/                       # Architecture docs
├── .github/workflows/ci.yml   # CI/CD pipeline
├── docker-compose.yml          # Local dev services
├── Dockerfile                  # Multi-stage build
├── demo.sh                     # Full flow demo
├── start.sh / stop.sh          # Service management
└── pyproject.toml              # Python config
```

## Key Design Decisions

- **Safety-first urgency classifier** — Optimizes for CRITICAL recall (≥ 0.98), not precision. Better to over-triage than miss a life-threatening case.
- **Attribute-proof model** — Never stores raw financial evidence. Verification happens externally; only reduced attributes are recorded.
- **Deterministic affordability** — Income bracket × tier multiplier ÷ frequency × urgency override. No randomness, fully auditable.
- **Durable subsidy workflow** — Temporal.io ensures exactly-once payment processing with automatic retry and compensation.
- **Append-only audit ledger** — SHA-256 hash chain makes tampering detectable. QLDB for cryptographic verification, PostgreSQL for fast queries.

## License

MIT
