# F-06 Audit Ledger — Implementation Spec

**Project:** Crisis-Cost Orchestrator  
**Feature:** F-06 Audit Ledger  
**Status:** Draft v1.0  
**Owner:** Engineering / Security  
**Depends On:** None (foundational infrastructure)

---

## 1. Purpose

The Audit Ledger is the **compliance backbone** of the Crisis-Cost Orchestrator. It provides an immutable, append-only record of every material event in the platform. No event may be silenced, altered, or deleted. The ledger ensures:

- **HIPAA compliance** — every access, decision, and data lifecycle event is recorded
- **Regulatory defense** — ability to prove that affordability decisions were made correctly
- **Fraud detection** — tamper-evident record of all financial transactions
- **Operational transparency** — complete visibility into system behavior

### 1.1 Design Principles

1. **Append-only** — events are never updated or deleted
2. **Cryptographically verifiable** — each event includes an integrity hash
3. **Schema-enforced** — all events conform to defined schemas
4. **Minimal but complete** — record what's needed for compliance, nothing extra
5. **Separation of concerns** — ledger is immutable; operational queries use projected views

---

## 2. Technology Stack

### 2.1 Primary Ledger: Amazon QLDB

| Feature | Benefit |
|---------|---------|
| Immutable journal | Cannot be altered after write |
| Cryptographic hash chain | Tamper-evident integrity |
| SQL-like query language (PartiQL) | Familiar query syntax |
| Managed service | No operational overhead |
| Ledger digest | Daily integrity verification |

### 2.2 Operational Store: PostgreSQL

QLDB is optimized for append-only writes, not complex queries. For operational needs:

| Store | Purpose | Sync |
|-------|---------|------|
| QLDB | Authoritative immutable ledger | Write-once |
| PostgreSQL | Projected views for dashboards, reporting | Async projection |
| Elasticsearch | Full-text search of audit events | Async projection |

### 2.3 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Event Producers                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Gateway  │ │Urgency  │ │Afford.  │ │Subsidy  │          │
│  │  (F-04) │ │(F-01)   │ │(F-02)   │ │(F-03)   │          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │
│       │           │           │           │                │
└───────┼───────────┼───────────┼───────────┼────────────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Audit Ledger Service                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Event Validation Layer                  │   │
│  │  - Schema validation                                │   │
│  │  - Integrity hash computation                       │   │
│  │  - Actor/workload attribution                       │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │                 Write Path                           │   │
│  │  ┌─────────────┐    ┌─────────────┐                 │   │
│  │  │   QLDB      │    │ PostgreSQL  │                 │   │
│  │  │ (Immutable) │───►│ (Projected) │                 │   │
│  │  └─────────────┘    └─────────────┘                 │   │
│  │         │                                            │   │
│  │         ▼                                            │   │
│  │  ┌─────────────┐                                    │   │
│  │  │Elasticsearch│                                    │   │
│  │  │  (Search)   │                                    │   │
│  │  └─────────────┘                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Integrity Verification                  │   │
│  │  - Daily hash chain verification                    │   │
│  │  - On-demand audit verification                     │   │
│  │  - Compliance export                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Event Taxonomy

### 3.1 Event Envelope Schema

Every event follows this structure:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://crisiscost.health/schemas/audit-event.schema.json",
  "title": "AuditEvent",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "event_id",
    "event_type",
    "event_timestamp",
    "actor",
    "entity",
    "schema_version",
    "integrity_hash"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "Globally unique event identifier."
    },
    "event_type": {
      "type": "string",
      "enum": [
        "ENCOUNTER_INGESTED",
        "ENCOUNTER_VALIDATION_FAILED",
        "URGENCY_CLASSIFIED",
        "URGENCY_CLASSIFICATION_FAILED",
        "ELIGIBILITY_PROOF_INGESTED",
        "ELIGIBILITY_PROOF_VERIFIED",
        "ELIGIBILITY_PROOF_REJECTED",
        "ELIGIBILITY_PROOF_EXPIRED",
        "ELIGIBILITY_PROOF_REVOKED",
        "AFFORDABILITY_DECISION_COMPUTED",
        "SUBSIDY_CREATED",
        "SUBSIDY_PAYMENT_INITIATED",
        "SUBSIDY_SETTLED",
        "SUBSIDY_FAILED",
        "SUBSIDY_CANCELLED",
        "BREAK_GLASS_ACCESS_GRANTED",
        "BREAK_GLASS_ACCESS_CLOSED",
        "KEY_ROTATED",
        "RETENTION_PURGE_EXECUTED",
        "LEDGER_DIGEST_VERIFIED",
        "RECONCILIATION_COMPLETED",
        "CONSENT_CAPTURED",
        "DATA_EXPORT_REQUESTED",
        "DATA_EXPORT_COMPLETED"
      ]
    },
    "event_timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "UTC timestamp when the event occurred."
    },
    "actor": {
      "type": "object",
      "additionalProperties": false,
      "required": ["actor_type", "actor_id"],
      "properties": {
        "actor_type": {
          "type": "string",
          "enum": [
            "SYSTEM",
            "PROVIDER_EHR",
            "PATIENT_APP",
            "VERIFICATION_PROVIDER",
            "OPERATOR",
            "AUDIT_SYSTEM"
          ]
        },
        "actor_id": {
          "type": "string",
          "maxLength": 128,
          "description": "Service principal, provider ID, or patient pseudo ID."
        }
      }
    },
    "entity": {
      "type": "object",
      "additionalProperties": false,
      "required": ["entity_type", "entity_id"],
      "properties": {
        "entity_type": {
          "type": "string",
          "enum": [
            "ENCOUNTER",
            "ELIGIBILITY_PROOF",
            "AFFORDABILITY_DECISION",
            "SUBSIDY",
            "SYSTEM"
          ]
        },
        "entity_id": {
          "type": "string",
          "maxLength": 128,
          "description": "ID of the primary entity this event relates to."
        }
      }
    },
    "payload": {
      "type": "object",
      "description": "Event-specific data. Must conform to the event type's payload schema."
    },
    "correlation_id": {
      "type": "string",
      "format": "uuid",
      "description": "Optional correlation ID linking related events across the same encounter."
    },
    "schema_version": {
      "type": "string",
      "const": "1.0.0"
    },
    "integrity_hash": {
      "type": "string",
      "description": "SHA-256 hash of the event payload (excluding this field). Computed before write."
    }
  }
}
```

### 3.2 Event Payloads by Type

#### ENCOUNTER_INGESTED

```json
{
  "encounter_id": "string",
  "patient_pseudo_id": "uuid",
  "provider_org_id": "uuid",
  "facility_type": "string",
  "encounter_class": "string",
  "payload_hash": "SHA-256 of the F-04 request body",
  "ingestion_latency_ms": 0
}
```

#### URGENCY_CLASSIFIED

```json
{
  "encounter_id": "string",
  "urgency_label": "CRITICAL|URGENT|ROUTINE",
  "confidence": 0.0,
  "triggered_evidence": ["string"],
  "rationale_summary": "string",
  "model_version": "string",
  "classification_latency_ms": 0
}
```

#### AFFORDABILITY_DECISION_COMPUTED

```json
{
  "encounter_id": "string",
  "patient_pseudo_id": "uuid",
  "proof_id": "uuid",
  "urgency_label": "string",
  "estimated_total_cents": 0,
  "affordability_cap_cents": 0,
  "patient_responsibility_cents": 0,
  "subsidy_amount_cents": 0,
  "tier_applied": "string",
  "cap_rule_applied": "string",
  "urgency_override_applied": false,
  "confidence_level": "HIGH|MODERATE|LOW"
}
```

#### SUBSIDY_SETTLED

```json
{
  "subsidy_id": "uuid",
  "encounter_id": "string",
  "patient_pseudo_id": "uuid",
  "provider_org_id": "uuid",
  "subsidy_amount_cents": 0,
  "payment_method": "ACH|WIRE|STABLECOIN",
  "payment_reference": "string",
  "settlement_time_ms": 0
}
```

#### LEDGER_DIGEST_VERIFIED

```json
{
  "verification_type": "DAILY|ON_DEMAND|INVESTIGATION",
  "events_since_last_check": 0,
  "chain_status": "VALID|INVALID",
  "last_event_id": "uuid",
  "digest_computed": "hex-string",
  "digest_expected": "hex-string",
  "verified_by": "string"
}
```

#### RETENTION_PURGE_EXECUTED

```json
{
  "data_class": "RAW_FINANCIAL_EVIDENCE|REDUCED_PROOF|AUDIT_EVENT|SDOH_PROXY",
  "retention_rule": "string",
  "records_purged": 0,
  "date_range_start": "date",
  "date_range_end": "date",
  "systems_purged": ["string"],
  "purge_method": "APPLICATION_DELETE|CRYPTO_SHRED|LIFECYCLE_EXPIRY"
}
```

---

## 4. QLDB Schema

### 4.1 Table Design

QLDB uses a document model. Each event type maps to a "table" (Ion documents):

```sql
-- QLDB PartiQL (conceptual)

CREATE TABLE audit_events;

-- Indexes for common query patterns
CREATE INDEX idx_event_type ON audit_events (event_type);
CREATE INDEX idx_entity ON audit_events (entity.entity_type, entity.entity_id);
CREATE INDEX idx_actor ON audit_events (actor.actor_type, actor.actor_id);
CREATE INDEX idx_timestamp ON audit_events (event_timestamp);
CREATE INDEX idx_correlation ON audit_events (correlation_id);
```

### 4.2 Document Structure

Each document in QLDB:

```json
{
  "id": "event_id (UUID)",
  "event_type": "string",
  "event_timestamp": "timestamp",
  "actor": { "actor_type": "string", "actor_id": "string" },
  "entity": { "entity_type": "string", "entity_id": "string" },
  "payload": { ... },
  "correlation_id": "uuid",
  "schema_version": "1.0.0",
  "integrity_hash": "SHA-256"
}
```

### 4.3 QLDB Ledger Configuration

```yaml
qldb:
  ledger_name: crisiscost-audit-ledger
  permissions_mode: STANDARD
  deletion_protection: true  # Cannot be disabled
  stream:
    enabled: true
    arn: arn:aws:kinesis:us-east-1:ACCOUNT:stream/crisiscost-audit-stream
```

---

## 5. Integrity Verification Protocol

### 5.1 Daily Automated Verification

```
Job: DailyLedgerIntegrityCheck
Schedule: 0 3 * * * (3:00 AM UTC daily)

Steps:
  1. Retrieve last verified digest from secure storage
  2. Compute current digest from QLDB journal
  3. Compare digests
  4. IF match: 
       - Write LEDGER_DIGEST_VERIFIED event (chain_status = VALID)
       - Store new digest
  5. IF mismatch:
       - Write LEDGER_DIGEST_VERIFIED event (chain_status = INVALID)
       - Trigger INCIDENT_RESPONSE workflow
       - Alert security team immediately
       - Do NOT write any further events until verified
```

### 5.2 On-Demand Verification

Available via API for compliance teams:

```
POST /api/v1/audit/verify
Authorization: Bearer <compliance-admin-token>

Response 200:
{
  "verification_type": "ON_DEMAND",
  "chain_status": "VALID",
  "last_verified_at": "timestamp",
  "events_since_last_check": 15423,
  "digest_computed": "hex-string",
  "verified_by": "compliance-admin@crisiscost.health"
}
```

### 5.3 Compliance Export

```
GET /api/v1/audit/export?start_date={start}&end_date={end}&entity_type={type}
Authorization: Bearer <compliance-admin-token>

Response 200:
{
  "export_id": "uuid",
  "event_count": 0,
  "date_range": { "start": "...", "end": "..." },
  "download_url": "https://...",
  "integrity_verified": true,
  "generated_at": "timestamp"
}
```

---

## 6. PostgreSQL Projection

For operational queries (dashboards, reporting, search), events are projected to PostgreSQL:

### 6.1 Projection Table

```sql
CREATE TABLE audit_events_projected (
    event_id          UUID PRIMARY KEY,
    event_type        VARCHAR(64) NOT NULL,
    event_timestamp   TIMESTAMP NOT NULL,
    actor_type        VARCHAR(32) NOT NULL,
    actor_id          VARCHAR(128) NOT NULL,
    entity_type       VARCHAR(32) NOT NULL,
    entity_id         VARCHAR(128) NOT NULL,
    correlation_id    UUID,
    payload           JSONB NOT NULL,
    integrity_hash    VARCHAR(64) NOT NULL,
    
    -- Derived columns for fast queries
    encounter_id      VARCHAR(64),
    patient_pseudo_id UUID,
    provider_org_id   UUID,
    subsidy_id        UUID
);

CREATE INDEX idx_proj_event_type ON audit_events_projected(event_type);
CREATE INDEX idx_proj_entity ON audit_events_projected(entity_type, entity_id);
CREATE INDEX idx_proj_encounter ON audit_events_projected(encounter_id);
CREATE INDEX idx_proj_patient ON audit_events_projected(patient_pseudo_id);
CREATE INDEX idx_proj_timestamp ON audit_events_projected(event_timestamp);
```

### 6.2 Projection Sync

```
Projection Service:
  - Polls QLDB Kinesis stream
  - Validates each event against schema
  - Projects to PostgreSQL
  - Tracks last projected sequence number
  - Handles duplicates idempotently
```

---

## 7. Access Control

### 7.1 QLDB Access Roles

| Role | Permissions | Use Case |
|------|------------|----------|
| `audit-writer` | INSERT only | All event producers |
| `audit-reader` | SELECT only | Compliance, operations dashboards |
| `audit-admin` | SELECT + verify | Compliance team, security |

### 7.2 Break-Glass Access

When emergency access to raw audit data is needed:

```
Break-Glass Workflow:
  1. Requestor submits reason code and ticket ID
  2. System grants time-limited read access (max 4 hours)
  3. System writes BREAK_GLASS_ACCESS_GRANTED event
  4. Access is automatically revoked after timeout
  5. System writes BREAK_GLASS_ACCESS_CLOSED event
  6. Security team reviews within 24 hours
```

---

## 8. API Endpoints

### 8.1 Query Events

```
GET /api/v1/audit/events
Authorization: Bearer <service-token>

Query Parameters:
  - event_type: filter by event type
  - entity_type: filter by entity type
  - entity_id: filter by specific entity
  - encounter_id: filter by encounter
  - patient_pseudo_id: filter by patient
  - start_date: filter from date
  - end_date: filter to date
  - limit: max results (default 100, max 1000)
  - offset: pagination cursor

Response 200:
{
  "events": [...],
  "total": 0,
  "has_more": false,
  "next_offset": null
}
```

### 8.2 Get Single Event

```
GET /api/v1/audit/events/:event_id
Authorization: Bearer <service-token>

Response 200:
{
  "event": { ... }
}
```

### 8.3 Verify Ledger Integrity

```
POST /api/v1/audit/verify
Authorization: Bearer <compliance-admin-token>

Response 200:
{
  "chain_status": "VALID",
  "last_verified_at": "timestamp",
  "events_since_last_check": 0
}
```

---

## 9. Retention & Disposition

Per the Data Retention Schedule:

| Data Class | Retention | Disposition |
|-----------|-----------|-------------|
| Audit events (QLDB) | 7 years | Cohort-based retirement |
| Audit events (PostgreSQL) | 7 years | Purge at expiry |
| Audit events (Elasticsearch) | 1 year | Index rollover |
| Audit exports (compliance) | Per compliance policy | Secure deletion |

### 9.1 Purge Process

```
Job: AuditRetentionPolicyEnforcement
Schedule: 0 4 1 * * (1st of month, 4:00 AM UTC)

Steps:
  1. Identify events older than 7 years
  2. Check for active legal holds
  3. Purge from PostgreSQL (batch delete)
  4. Purge from Elasticsearch (index rollover)
  5. For QLDB: mark cohort for retirement (do not delete from immutable journal)
  6. Write RETENTION_PURGE_EXECUTED event
  7. Verify purge completion
```

---

## 10. SLA Requirements

| Metric | Target |
|--------|--------|
| Event write latency (p99) | < 100ms |
| Event write throughput | 5,000 events/sec |
| Projection lag (QLDB → PostgreSQL) | < 5 seconds |
| Daily integrity verification | < 5 minutes |
| On-demand verification | < 30 seconds |
| Compliance export | < 5 minutes for 30-day range |
| Availability | 99.99% |

---

## 11. Monitoring & Alerting

| Metric | Alert Threshold |
|--------|----------------|
| Ledger integrity check failure | Any occurrence |
| Event write failure rate | > 0.1% in 5 minutes |
| Projection lag > 30 seconds | Any occurrence |
| Break-glass access | Every occurrence |
| Daily verification not completed by 4 AM | Any occurrence |
| Purge job failure | Any occurrence |

---

## 12. Integration Points

| Service | Events Emitted | Protocol |
|---------|---------------|----------|
| Provider API Gateway | ENCOUNTER_INGESTED | Async (event bus) |
| Urgency Classifier | URGENCY_CLASSIFIED | Async (event bus) |
| Eligibility Verification | ELIGIBILITY_PROOF_* | Async (event bus) |
| Affordability Engine | AFFORDABILITY_DECISION_COMPUTED | Async (event bus) |
| Subsidy Orchestrator | SUBSIDY_* | Async (event bus) |
| Key Management | KEY_ROTATED | Async (event bus) |
| Retention Service | RETENTION_PURGE_EXECUTED | Async (event bus) |

---

*This document defines the complete implementation specification for the F-06 Audit Ledger. All changes must be reviewed by engineering and security/compliance.*
