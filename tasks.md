# Project Task Checklist

## Phase 1 — Schemas & Design ✅

### Agent Setup
- [x] Configured Zsh environment variable `PI_SKILLS_PATH`.
- [x] Configured VS Code `pi.skills.path` setting.
- [x] Identified custom agent repository path `${HOME}/Projects/agency-agents/`.
- [x] Reviewed `healthcare` project documents (`agenc-agents-conversation.md`, `agency-agents-info.md`, `prd.md`).
- [x] Brainstormed agent integration strategy and documented it in `agent-integration-strategy.md`.
- [x] Installed selected agents:
  - `specialized/medical-billing-coding-specialist`
  - `engineering/engineering-software-architect`
  - `engineering/engineering-ai-engineer`
  - `security/security-compliance-auditor`
  - `design/design-ux-architect`

### F-04 Provider API
- [x] Invoked `engineering-software-architect` to define an initial JSON schema for the Provider API (F-04).
- [x] Provided detailed feedback on the JSON schema and requested revisions.
- [x] Revised the Provider API (F-04) JSON schema (`provider-api-f04-request.schema.json`).
- [x] Generated Protobuf definitions for the Provider API (F-04) (`schemas/provider-api-f04-request.proto`).

### Security & Compliance
- [x] Generated security and encryption protocol for patient-income verifying proofs (`docs/security/patient-income-proof-protocol.md`).
- [x] Created `schemas/eligibility-proof.schema.json` defining the eligibility proof structure.
- [x] Produced a sample eligibility proof JSON (`schemas/eligibility-proof.json`).
- [x] Added a plaintext companion example (`schemas/eligibility-proof.protected-attributes.plaintext.json`).
- [x] Updated `schemas/eligibility-proof.schema.json` with a comment linking to the plaintext companion.
- [x] Generated an audit event schema for eligibility proof lifecycle events (`schemas/eligibility-proof-audit-event.schema.json`).
- [x] Generated comprehensive data retention schedule (`docs/security/retention-schedule.md`).

### Architecture & AI
- [x] Created a high-level sequence diagram for the encounter flow (`docs/architecture/encounter-flow.mmd`).
- [x] Designed a comprehensive prompt engineering strategy for the Urgency Classifier (`docs/ai/urgency-classifier-strategy.md`).
- [x] Generated production-ready system and developer prompts for the Urgency Classifier (`docs/ai/urgency-classifier-prompts.md`).

### Design
- [x] Designed Patient Cost Dashboard UX architecture (`docs/design/patient-cost-dashboard-ux.md`).

---

## Phase 2 — Implementation Specs ✅

### Planning
- [x] Created Phase 2 Implementation Plan (`docs/phases/phase-2-implementation-plan.md`).

### F-02 Affordability Engine
- [x] Created detailed implementation spec (`docs/architecture/f02-affordability-engine-spec.md`).
- [x] Defined income bracket mapping (12 brackets, IB-01 through IB-12).
- [x] Defined affordability tier rules (5 tiers: CRITICAL, LOW, STANDARD, MODERATE, UNVERIFIED).
- [x] Defined urgency override rules (CRITICAL gets 25% additional protection).
- [x] Defined household size adjustment factors.
- [x] Created unit test cases (happy path, edge cases, boundary tests).
- [x] Defined API endpoint and SLA requirements.

### F-03 Subsidy Orchestrator
- [x] Created detailed implementation spec (`docs/architecture/f03-subsidy-orchestrator-spec.md`).
- [x] Designed Temporal.io workflow topology (6-step process).
- [x] Defined subsidy record database schema (PostgreSQL).
- [x] Defined payment rails (ACH, Wire, Stablecoin).
- [x] Designed reconciliation job.
- [x] Defined API endpoints and SLA requirements.

### F-06 Audit Ledger
- [x] Created detailed implementation spec (`docs/architecture/f06-audit-ledger-spec.md`).
- [x] Designed QLDB schema and event taxonomy (24 event types).
- [x] Defined event envelope schema.
- [x] Defined event payloads for all major event types.
- [x] Designed integrity verification protocol.
- [x] Designed PostgreSQL projection for operational queries.
- [x] Defined API endpoints and SLA requirements.

### OpenAPI Specification
- [x] Generated OpenAPI 3.1 spec (`schemas/openapi-3.1.yaml`).
- [x] Documented all endpoints (F-04, F-01, F-02, F-03, F-06, Patient Dashboard).
- [x] Defined authentication and security requirements.
- [x] Defined request/response schemas for all endpoints.

### Architecture Decision Records
- [x] ADR-001: Use Amazon QLDB for Audit Ledger (`docs/adr/001-use-amazon-qldb-for-audit-ledger.md`).
- [x] ADR-002: Use Temporal.io for Subsidy Orchestration (`docs/adr/002-use-temporal-for-subsidy-orchestration.md`).
- [x] ADR-003: Attribute-Proof Model for Eligibility (`docs/adr/003-attribute-proof-model-for-eligibility.md`).
- [x] ADR-004: Safety-First Urgency Classification (`docs/adr/004-safety-first-urgency-classification.md`).

---

## Phase 3 — Core Services ✅

### F-01 Urgency Classifier
- [x] Hybrid rule-based + LLM classifier with 30+ clinical threshold rules.
- [x] Compound condition detection (Fever+Hypotension=CRITICAL, Opioid+Resp depression=CRITICAL).
- [x] SNOMED CT codes for high-risk complaint classification.
- [x] 15 Pydantic models for F-04 request validation.
- [x] 30 unit tests (82% coverage).

### F-02 Affordability Engine
- [x] 12 income brackets (IB-01 through IB-12), midpoint-based calculation.
- [x] 5 affordability tiers (TIER-CRITICAL 0.05 through TIER-UNVERIFIED 1.00).
- [x] Urgency override (CRITICAL gets 0.75 multiplier).
- [x] Household size adjustment factors.
- [x] Fully deterministic/stateless/idempotent.
- [x] 16 unit tests (95% coverage).

### F-03 Subsidy Orchestrator
- [x] Payment rails: ACH (<$100k), Wire ($100k-$500k), Stablecoin (>$500k).
- [x] Lifecycle management: PENDING → VALIDATING → INITIATING_PAYMENT → PAYMENT_PROCESSING → PAYMENT_SETTLED.
- [x] Temporal.io workflow with retry (3 attempts, exponential backoff) and saga compensation.
- [x] 10 unit tests (93% coverage).

### F-06 Audit Ledger
- [x] Append-only immutable event store (in-memory for dev).
- [x] 16 event types covering full encounter lifecycle.
- [x] SHA-256 integrity hash chain verification.
- [x] PostgreSQL projection for operational queries.
- [x] 7 unit tests (92% coverage).

### Infrastructure
- [x] PostgreSQL database module (`src/db/connection.py`, `src/db/audit_repository.py`).
- [x] Database migrations runner (`src/db/migrations.py`).
- [x] Temporal.io client integration (`src/services/temporal_client.py`).
- [x] FastAPI app with lifespan DB init, CORS, health/readiness probes.
- [x] Dockerfile (multi-stage) and docker-compose.yml (PostgreSQL, Redis, Temporal).
- [x] `.env.example` with all configuration variables.

### API Layer
- [x] F-01: POST /v1/urgency/classify
- [x] F-02: POST /v1/affordability/calculate
- [x] F-03: POST /v1/subsidies, GET, SETTLE, CANCEL
- [x] F-06: GET /v1/audit/events, /v1/audit/entity/{type}/{id}, /v1/audit/verify
- [x] GET /health, GET /ready

### Tests
- [x] F-01 Urgency Classifier: 30 tests.
- [x] F-02 Affordability Engine: 16 tests.
- [x] F-03 Subsidy Orchestrator: 10 tests.
- [x] F-03 Temporal Client: 10 tests.
- [x] F-06 Audit Ledger: 7 tests.
- [x] F-06 DB Repository: 9 tests.
- [x] API Integration: 12 tests.
- [x] E2E Integration: 5 tests (full encounter flow).
- [x] **98 total tests passing**.

---

## Phase 4 — Frontend ✅

### F-05 Patient Dashboard
- [x] React + TypeScript + Vite + Tailwind CSS project setup.
- [x] TypeScript API types (`frontend/src/types/api.ts`).
- [x] API client with all endpoints (`frontend/src/api/client.ts`).
- [x] Dashboard page with stats, audit event table, system status.
- [x] Production build verified.

---

## Phase 5 — CI/CD ✅

### GitHub Actions
- [x] Backend CI: Python lint (Ruff), tests with coverage, PostgreSQL service.
- [x] Frontend CI: TypeScript type check, build verification.
- [x] Docker build (on main branch).
- [x] Coverage upload to Codecov.

---

## Phase 6 — Production Readiness 🔵 (Future)

### Security & Compliance
- [ ] Security audit and penetration testing.
- [ ] HIPAA compliance review.
- [ ] Clinical validation of urgency classifier.

### Integration
- [ ] Integration with real payment rails (ACH, Wire).
- [ ] Integration with verification providers.
- [ ] Temporal server production deployment.

### Monitoring
- [ ] Observability stack (Prometheus, Grafana).
- [ ] Alerting rules for critical failures.
- [ ] Audit log export to compliance storage.

---

*This checklist is automatically updated as tasks are completed. It resides in the project root (`tasks.md`).*
