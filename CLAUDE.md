# CLAUDE.md — healthcare (Crisis-Cost Orchestrator)

## Stack
- Backend: Python 3.11+, FastAPI, Pydantic v2, asyncpg/PostgreSQL, Temporal (`temporalio`), JWT auth (`src/`)
- Frontend: React + TypeScript + Vite (`frontend/`)
- Infra: Docker / docker-compose; CI in `.github/workflows/ci.yml`

## Commands
```
pip install -e ".[dev]"                 # backend deps + test tools
cd frontend && npm install && cd ..     # frontend deps
docker compose up -d                    # Postgres / Temporal / API
./start.sh --fg | ./status.sh | ./stop.sh
./demo.sh                               # end-to-end encounter flow (API on :8000)
python -m pytest tests/ -v              # tests
python -m pytest tests/ --cov=src --cov-report=term-missing
ruff check .
```

## Conventions
- Features are numbered modules (F-01 urgency, F-02 affordability, F-03 subsidy, F-04 intake, F-06 ledger, Claims).
- JSON request schemas live in `schemas/`; product spec in `prd.md`, task list in `tasks.md`.
- Affordability engine is deterministic; LLM is used only in urgency classification (hybrid with rules).
- Audit ledger entries are SHA-256 chained — never mutate past entries.
