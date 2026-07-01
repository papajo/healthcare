# ADR-001: Use Amazon QLDB for Immutable Audit Ledger

**Status:** Accepted  
**Date:** 2026-07-01  
**Deciders:** Engineering, Security/Compliance  
**Relates to:** F-06 Audit Ledger

---

## Context

The Crisis-Cost Orchestrator requires an immutable, append-only audit trail for HIPAA compliance, regulatory defense, and fraud detection. Every material event — encounter ingestion, urgency classification, affordability decisions, subsidy payments — must be recorded in a tamper-evident manner.

We need to choose a ledger technology that provides:
1. Immutability (no updates or deletes)
2. Cryptographic integrity verification
3. Queryability for compliance exports
4. Managed operation (minimal operational overhead)
5. Integration with our existing AWS infrastructure

## Decision

**Use Amazon QLDB as the primary immutable audit ledger.**

PostgreSQL will serve as a projected view for operational queries (dashboards, reporting, search). Elasticsearch will provide full-text search capabilities.

## Options Considered

### Option 1: Amazon QLDB (Chosen)

**Pros:**
- Native immutability — journal cannot be altered after write
- Built-in cryptographic hash chain (SHA-256)
- Managed service — no operational overhead
- PartiQL (SQL-like) query language
- Kinesis stream for real-time projection to PostgreSQL
- Ledger digest for daily integrity verification
- Deletion protection enabled by default

**Cons:**
- AWS lock-in
- Higher cost than self-hosted PostgreSQL
- Limited query flexibility compared to PostgreSQL
- No cross-cloud option

### Option 2: PostgreSQL with Append-Only Tables

**Pros:**
- Familiar technology stack
- Lower cost
- Full SQL query flexibility
- No vendor lock-in

**Cons:**
- Immutability must be enforced via triggers/policies (not native)
- No built-in cryptographic hash chain
- Integrity verification must be custom-built
- Risk of silent data modification by privileged users
- More operational overhead for compliance guarantees

### Option 3: Amazon QLDB + PostgreSQL Hybrid (Chosen Approach)

**Pros:**
- QLDB provides authoritative immutability
- PostgreSQL provides operational query flexibility
- Best of both worlds
- Projection lag < 5 seconds

**Cons:**
- Two systems to maintain
- Projection sync must be reliable
- Eventual consistency between QLDB and PostgreSQL

## Consequences

1. **All event producers write to QLDB first**, then project to PostgreSQL asynchronously
2. **Daily integrity verification** runs automatically at 3:00 AM UTC
3. **Compliance exports** use QLDB as the authoritative source
4. **Operational dashboards** use PostgreSQL projected views
5. **If QLDB projection fails**, operations team is alerted but QLDB remains authoritative
6. **PostgreSQL data can be reconstructed** from QLDB if needed (re-projection)

## Compliance Impact

- QLDB satisfies HIPAA's requirement for audit trail integrity
- Hash chain provides tamper-evident evidence for regulatory audits
- Ledger digest verification provides daily compliance assurance
- Break-glass access is recorded as immutable events

## Cost Estimate

| Component | Monthly Cost (est.) |
|-----------|-------------------|
| QLDB writes | $500 (at 500k events/month) |
| QLDB storage | $100 |
| Kinesis stream | $150 |
| PostgreSQL RDS | $300 |
| **Total** | **$1,050/month** |

---

*This ADR documents the decision to use Amazon QLDB as the primary immutable audit ledger for the Crisis-Cost Orchestrator.*
