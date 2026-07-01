# ADR-002: Use Temporal.io for Subsidy Orchestration Workflows

**Status:** Accepted  
**Date:** 2026-07-01  
**Deciders:** Engineering  
**Relates to:** F-03 Subsidy Orchestrator

---

## Context

The Subsidy Orchestrator must manage multi-step payment workflows that span hours to days:
1. Validate eligibility
2. Create subsidy record
3. Initiate payment via payment rail (ACH/wire/stablecoin)
4. Await payment confirmation (up to 72 hours)
5. Settle or retry on failure
6. Emit audit events

These workflows must be:
- **Durable** — survive process crashes and restarts
- **Retryable** — exponential backoff with configurable retry policies
- **Observable** — real-time visibility into workflow state
- **Compensatable** — ability to undo partial progress on failure
- **Auditable** — complete history of every workflow execution

## Decision

**Use Temporal.io as the workflow orchestration engine for F-03 Subsidy Orchestrator.**

## Options Considered

### Option 1: Temporal.io (Chosen)

**Pros:**
- Durable execution — workflows survive crashes
- Native retry policies with exponential backoff
- Built-in timeout handling (72-hour payment timeout)
- Saga pattern for compensation
- Workflow history is itself an audit trail
- Temporal UI for real-time workflow visibility
- Strong community and production-proven at scale
- Supports multiple languages (Go, Java, TypeScript, Python)

**Cons:**
- Additional infrastructure to operate (Temporal cluster)
- Learning curve for team unfamiliar with Temporal
- Vendor risk (though open-source)

### Option 2: Custom State Machine + PostgreSQL

**Pros:**
- Full control over implementation
- No additional infrastructure
- Familiar technology

**Cons:**
- Must build durability, retry, timeout, and compensation from scratch
- No built-in workflow visibility
- Higher risk of bugs in critical financial flows
- Significant engineering effort

### Option 3: AWS Step Functions

**Pros:**
- Managed service
- Native AWS integration
- Visual workflow editor

**Cons:**
- AWS lock-in
- Less flexible than Temporal for complex workflows
- Limited language support
- Higher cost at scale
- Less community support

## Consequences

1. **Temporal cluster** will be deployed alongside existing infrastructure
2. **Workflow definitions** will be version-controlled and tested
3. **Workflow history** provides built-in audit trail (supplements QLDB)
4. **Temporal UI** gives operations team real-time visibility
5. **Retry policies** are configured per workflow step (max 3 retries, exponential backoff)
6. **Timeout handling** ensures stuck payments are detected and resolved within 72 hours
7. **Compensation actions** handle partial failures gracefully

## Technical Design

```
Temporal Cluster:
  - Namespace: crisiscost-subsidy
  - Task Queue: subsidy-orchestrator
  - Workflow Timeout: 7 days
  - Max Retries: 3
  - Backoff: Exponential (1h, 4h, 12h)
  - Non-retryable: INVALID_ACCOUNT, COMPLIANCE_BLOCK
```

## Integration Points

| Component | Integration |
|-----------|------------|
| Subsidy Orchestrator API | Starts workflows via Temporal client |
| Payment Rails | Called as activities within workflows |
| Audit Ledger (QLDB) | Emits events from workflow steps |
| Provider Dashboard | Queries workflow status via API |

## Cost Estimate

| Component | Monthly Cost (est.) |
|-----------|-------------------|
| Temporal Cloud (Standard) | $500 |
| Temporal UI | Included |
| **Total** | **$500/month** |

---

*This ADR documents the decision to use Temporal.io for subsidy orchestration workflows in the Crisis-Cost Orchestrator.*
