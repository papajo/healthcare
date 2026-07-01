# Crisis-Cost Orchestrator Data Retention Schedule

**Project:** Crisis-Cost Orchestrator  
**Status:** Draft v1.0  
**Owner:** Security / Compliance  
**Applies To:** Affordability Engine, Subsidy Orchestrator, Provider API, Patient App, Identity Vault, Verification Provider boundary, Audit Ledger, analytics derivatives that handle regulated proof data

---

## 1. Purpose

This retention schedule defines how long the Crisis-Cost Orchestrator may retain sensitive eligibility and affordability data, why each period is justified, and how data must be securely purged.

This schedule is intended to align with `docs/security/patient-income-proof-protocol.md`, especially these established rules:

- raw financial evidence is **not stored in the core platform** by default
- the platform uses an **attribute-proof model**
- reduced proofs may be retained for **7 years after final subsidy/payment action** unless a longer legal obligation or legal hold applies
- SDOH proxies such as ZIP code must be minimized to `service_area_code` or `ZIP3`
- all material lifecycle actions must be recorded in the immutable audit trail

> **Interpretation rule:** if this schedule conflicts with a stricter statute, payer contract, court order, or approved legal hold, the stricter requirement governs. If this schedule conflicts with the patient-income-proof protocol, the protocol’s minimization rule governs unless Legal/Compliance approves an exception.

---

## 2. Governing Principles

1. **Minimum necessary retention** — keep only what is required for operations, audit defense, dispute handling, fraud review, or legal obligation.
2. **Reduced attributes over raw evidence** — retain signed proof attributes instead of source documents whenever possible.
3. **Retention starts from a clear trigger** — every record class must have a defined retention clock.
4. **Secure disposal is mandatory** — expiration means purge from active stores, caches, indexes, and derivative copies, plus crypto-shredding where supported.
5. **Immutable evidence remains immutable** — audit disposition must not silently undermine integrity claims.
6. **Legal holds suspend destruction** — no purge may proceed once a valid hold is applied.

---

## 3. Legal and Regulatory Basis

This schedule uses the following legal/compliance drivers.

### 3.1 HIPAA
- **45 CFR 164.316(b)(2)(i)** requires HIPAA-required policies, procedures, actions, activities, and assessments to be retained for **6 years** from creation or the date last in effect, whichever is later.
- The Security Rule’s minimum-necessary, access-control, audit, and integrity principles support retaining only the least amount of regulated data needed to defend payment/eligibility decisions.

### 3.2 GLBA
- The GLBA Safeguards Rule does not set a single universal retention duration for this project’s data classes, but it strongly supports **data minimization, secure handling, restricted use, and secure disposal when data is no longer necessary**.
- For data sourced from financial institutions or aggregators, the project must avoid retaining raw financial artifacts longer than operationally required.

### 3.3 FCRA
- If consumer report data or CRA-sourced eligibility inputs are used, the platform must document **permissible purpose**, support **dispute/correction handling**, and avoid broad retention of full consumer report contents.
- This schedule therefore prefers retaining **reduced proofs and audit trails** rather than consumer report payloads.

### 3.4 IRS / FTI Avoidance
- The project’s established protocol states that the preferred architecture is to **avoid ingesting FTI into the platform**.
- Any edge case involving tax-return-derived data must be reduced before entering the core platform.

### 3.5 Contractual / State / Program Audit Requirements
- Medicaid, payer, grant, fraud-review, and state oversight obligations may require supporting records to remain available beyond HIPAA’s 6-year documentation baseline.
- For this reason, the project adopts **7 years** for reduced proofs and decision audit evidence unless a stricter requirement applies.

---

## 4. Scope of This Schedule

This schedule covers the following data classes requested for the project:

1. **Raw financial evidence** (if stored transiently)
2. **Reduced eligibility proofs**
3. **Audit events**
4. **SDOH proxy data**

It also applies to:
- backups containing those data classes
- search indexes, caches, and temporary processing stores
- exported compliance evidence sets
- analytics derivatives containing regulated fields

---

## 5. Retention Schedule Summary

| Data Class | Typical Contents | Storage Boundary | Retention Trigger | Retention Period | Legal / Control Justification | Required Disposition |
|---|---|---|---|---|---|---|
| Raw financial evidence (transient only) | pay stubs, bank statements, tax files, benefit letters, full document uploads, payroll/aggregator payloads | **Verification Provider boundary only**; not core platform | proof issuance completed, verification failure closure, or upload abandonment | **Delete immediately after proof issuance; hard maximum 24 hours** unless approved fraud/legal exception applies | HIPAA minimum necessary; GLBA data minimization and secure disposal; FCRA minimization for consumer report content; protocol §12.1 sets 24-hour max | purge object + metadata, purge temp files/caches, wipe queues, remove thumbnails/OCR text, crypto-shred transient keys, ledger tombstone only |
| Reduced eligibility proofs | signed proof token/document; proof_id; patient_pseudo_id; income_bracket_code; affordability_tier; eligibility_status_normalized; service_area_code/ZIP3; assurance metadata; proof hash | Core regulated stores | **final subsidy/payment action** tied to the proof, or proof supersession if no final action occurred | **7 years after final subsidy/payment action**; if no action occurs, 7 years after proof expiration or withdrawal | HIPAA 6-year documentation baseline plus additional year for payer/program dispute and audit defense; aligns with protocol §12.2 and §15 | purge operational copies, caches, replicas, analytics extracts; destroy field keys where isolated; retain audit tombstone/reference |
| Audit events | consent capture, proof issuance/ingestion, proof reads, affordability decisions, overrides, break-glass, key events, retention purge events, ledger digest verification | Immutable audit ledger + controlled audit exports | **final subsidy/payment action, incident closure, or investigation closure, whichever is later** | **7 years** minimum; extend while an incident, dispute, investigation, or legal hold remains open | HIPAA 6-year documentation baseline; need to reproduce financial/eligibility decisions and security activity; supports FCRA dispute/permissible-purpose evidence; protocol requires immutable auditability | no silent mutation; archive verified events; delete non-authoritative replicas at expiry; for immutable stores use cohort-based retirement or verified export + controlled decommissioning |
| SDOH proxy data | service_area_code, ZIP3, normalized eligibility status, geography-derived risk bands, household-size band where retained | Core stores only if needed; no unnecessary denormalized copies | **last operational use** for decisioning or proof refresh | **2 years after last operational use** for standalone SDOH proxy tables/features; **if embedded inside a reduced proof, the proof’s 7-year retention governs** | HIPAA minimum necessary; protocol requires minimizing ZIP and eligibility proxies; shorter period reduces socioeconomic profiling risk; keep only long enough for refresh, appeals, and short-cycle analytics | purge standalone datasets, feature stores, dashboards, cached extracts, and re-computable derived fields; preserve only values embedded in retained proofs/audit evidence |

---

## 6. Detailed Rules by Data Class

### 6.1 Raw Financial Evidence (Transient Only)

#### Allowed retention
- Raw financial evidence must **not** be retained in the core platform.
- If a verifier temporarily stores evidence to validate authenticity and issue a reduced proof, that retention must be **as short as technically possible**.
- Default rule: delete as soon as the reduced proof is issued or the verification attempt is abandoned/failed.
- Maximum standard retention: **24 hours**.

#### Exceptions
Retention beyond 24 hours is permitted only when all of the following are true:
- a documented fraud investigation, legal request, or regulator-mandated review requires it
- Legal/Compliance approves the exception
- the evidence is moved to a separately encrypted exception store
- the exception has a defined destruction deadline
- access is restricted to specifically assigned reviewers

#### Legal justification
- **HIPAA:** minimum necessary and risk reduction support immediate disposal of raw source documents once they are reduced.
- **GLBA:** supports secure handling and disposal of financial-source data when no longer needed.
- **FCRA:** if consumer report data is involved, retaining a reduced proof and audit trail is preferable to storing full reports.
- **Protocol alignment:** `patient-income-proof-protocol.md` §2, §5.2, and §12.1 prohibit routine persistence and set a 24-hour maximum.

#### Secure deletion protocol
- delete the primary object/blob/document
- delete OCR text, thumbnails, derivatives, temp files, and staging rows
- purge message queues and retry payloads containing evidence
- purge search indexes and caches
- crypto-shred any ephemeral content-encryption key if unique per object/session
- append `RETENTION_PURGE_EXECUTED` event to the audit ledger with object reference, actor/workload, timestamp, and reason

---

### 6.2 Reduced Eligibility Proofs

#### Allowed retention
Retain reduced signed proofs for **7 years after the final subsidy/payment action** that relied on the proof.

If no final subsidy/payment action occurs, retain for **7 years after proof expiration, revocation, or case withdrawal**, whichever closes the workflow.

#### Why 7 years
- Meets and exceeds HIPAA’s **6-year** documentation baseline.
- Preserves evidence long enough to defend affordability calculations, subsidy determinations, fraud reviews, reimbursement disputes, state/payer audits, and program integrity reviews.
- Avoids retaining raw financial artifacts while still preserving decision reproducibility.
- Aligns directly with `patient-income-proof-protocol.md` §12.2 and §15.

#### What should be retained
Only the reduced proof set, such as:
- `proof_id`
- `patient_pseudo_id`
- issuer and signature metadata
- verification method
- income bracket code
- affordability tier
- normalized eligibility status
- service area code / ZIP3 if required
- validity window
- proof hash / revocation metadata
- consent reference ID

Do **not** retain raw source documents as part of the proof record.

#### Secure deletion protocol
At expiry, the system must:
- purge proof rows/documents from active data stores
- purge replicas, read models, indexes, caches, and reporting marts
- purge proof payloads from object stores and search systems
- destroy record-specific or field-isolated keys where the design supports crypto-shredding
- preserve only the minimum tombstone/reference needed to explain lawful deletion in the audit trail
- log the purge in the immutable ledger

---

### 6.3 Audit Events

#### Allowed retention
Retain audit events for **7 years after the later of**:
- final subsidy/payment action,
- incident closure,
- dispute resolution,
- investigation closure.

If a legal hold or regulatory inquiry remains open, retention continues until release.

#### Why 7 years
- HIPAA requires documentation of required actions and activities for **6 years**.
- The project needs an additional buffer to defend healthcare-payment and financial-assistance decisions, investigate misuse, demonstrate permissible purpose where FCRA-related sources are involved, and prove retention/deletion actions.
- The patient-income-proof protocol requires immutable events for proof lifecycle, break-glass access, digest verification, and purge execution.

#### Important implementation note for immutable ledgers
Because the project uses an immutable audit model:
- individual event mutation or silent backfill is prohibited
- deletion must not undermine integrity claims
- if the authoritative ledger technology cannot selectively delete aged records, the system must use one of these approved patterns:
  1. **Cohort-based ledger retirement:** segregate records so expired cohorts can be archived and the retired ledger/table/environment decommissioned on schedule.
  2. **Verified export + controlled decommissioning:** export and verify the ledger segment to a compliant WORM archive for the required period, then decommission queryable operational replicas according to the retention architecture.
  3. **Authoritative ledger + non-authoritative replica purge:** if the ledger must remain intact longer for technical reasons, all queryable replicas, marts, SIEM mirrors, and convenience indexes must still be purged on schedule, and the residual authoritative store must remain tightly access-controlled.

#### Secure deletion / disposition protocol
For audit data:
- do not alter or overwrite existing authoritative events
- purge non-authoritative copies from SIEM hot storage, analytics marts, caches, and search indexes at retention expiry
- maintain digest-verification evidence for archived segments
- record archive/decommission actions in a final ledger management event
- document residual immutable-store constraints if any remain after the primary retention window

---

### 6.4 SDOH Proxy Data

#### What this includes
- `service_area_code`
- `ZIP3`
- temporary `ZIP5` before minimization
- normalized eligibility status where it reflects socioeconomic or public-benefit participation
- geography-derived deprivation / access bands
- household-size band where retained for affordability logic

#### Retention rule
- **Temporary ZIP5** used for intake routing or validation must be discarded immediately after conversion to `service_area_code` or `ZIP3`, and never retained by default.
- **Standalone SDOH proxy datasets, feature tables, analytics views, and caches** may be retained for **2 years after last operational use**.
- If an SDOH proxy value is embedded inside a **retained reduced proof**, the proof’s **7-year** schedule governs that specific record copy.
- No separate denormalized copy should be kept merely for convenience if the value already exists in the proof record.

#### Why 2 years for standalone copies
- The protocol classifies ZIP and eligibility data as sensitive SDOH proxies that can reveal poverty, disability, benefits participation, or geography-linked vulnerability.
- The platform needs a limited operational window for proof refreshes, appeals, case follow-up, and near-term service optimization.
- A shorter period reduces profiling risk and is more consistent with HIPAA minimum-necessary expectations than retaining SDOH features for the full proof lifecycle in every downstream dataset.

#### Legal / compliance rationale
- **HIPAA:** minimize retained socioeconomic indicators when not necessary for continued payment/eligibility operations.
- **GLBA/FCRA:** neither regime justifies broad downstream persistence of derived socioeconomic proxies once the specific decision need ends.
- **Protocol alignment:** `patient-income-proof-protocol.md` §5.3 and §5.4 require ZIP and eligibility minimization and restricted storage.

#### Secure deletion protocol
- purge standalone feature tables and caches
- purge BI extracts, notebooks, and dashboard snapshots containing person-level SDOH proxies
- remove proxy values from search indexes and ad hoc exports
- re-run downstream materializations without expired records
- record the purge in the audit trail

---

## 7. Secure Deletion and Purging Standard

The following disposal controls apply to all covered data classes unless a stricter system-specific control exists.

### 7.1 Purge workflow
1. Identify records whose retention trigger has expired.
2. Check for active legal hold, open incident, fraud review, payment dispute, or regulator request.
3. If none apply, execute purge across:
   - primary databases
   - object stores
   - caches
   - search indexes
   - analytics stores
   - async queues / dead-letter queues
   - backups according to backup expiry rules
4. Write `RETENTION_PURGE_EXECUTED` to the immutable audit trail.
5. Verify purge completion and raise an incident if deletion fails.

### 7.2 Deletion methods
Use the strongest method supported by the storage system:

- **Application-layer purge** of the record/object
- **Index/cache invalidation** for derivative copies
- **Crypto-shredding** by destroying object- or field-specific encryption keys where feasible
- **Storage lifecycle enforcement** for ephemeral buckets and temp stores
- **Backup expiration** so deleted records age out of encrypted backups on schedule

### 7.3 Backup rule
Expired records may remain in **encrypted, access-restricted backups only until the backup set itself expires**. Backup media must not be restored for routine access to expired data. Any restore requires ticketed approval and must re-apply deletion controls before the environment returns to service.

### 7.4 Purge verification
Purge jobs must produce evidence showing:
- data class
- retention rule applied
- record cohort / date range
- systems purged
- exceptions skipped due to hold/investigation
- job outcome
- verification timestamp

---

## 8. Legal Hold Handling

### 8.1 When a legal hold applies
A legal hold may be issued for:
- litigation or anticipated litigation
- government inquiry or subpoena
- payer/provider dispute
- fraud investigation
- security incident or breach investigation
- records preservation notice from Legal/Compliance

### 8.2 Hold effects
Once a hold is issued:
- scheduled deletion for covered records is suspended
- crypto-shredding of relevant keys is suspended
- backup expiry exceptions are documented where necessary
- the hold scope must identify record classes, date ranges, patient/case identifiers, and systems in scope
- the hold event must be logged in the immutable audit trail

### 8.3 Hold governance
Legal holds must include:
- issuing authority
- written reason / matter ID
- scope of affected records
- start date
- review cadence
- release condition

### 8.4 Hold release
When Legal/Compliance releases the hold:
- retention clocks resume
- records already past normal retention become eligible for purge in the next scheduled cycle
- the release and resulting purge must both be auditable

---

## 9. Roles and Responsibilities

| Role | Responsibility |
|---|---|
| Security / Compliance | Own this schedule, review exceptions, verify purge evidence |
| Legal | Approve legal holds, interpret conflicts with law or contracts |
| Verification Provider Owner | Enforce 24-hour max retention for raw evidence and exception segregation |
| Platform Engineering | Implement lifecycle policies, purge jobs, cache/index deletion, crypto-shredding hooks |
| Data Engineering / Analytics | Eliminate unnecessary downstream copies; enforce SDOH proxy expiry |
| IAM / KMS Owners | Ensure key access control, rotation, and key-destruction procedures |
| Audit / Risk | Validate retention evidence and control effectiveness |

---

## 10. Control Checklist

- [ ] Raw financial evidence is not stored in the core platform.
- [ ] Verification boundary enforces automatic deletion with a 24-hour maximum.
- [ ] Reduced proofs are retained for 7 years from final subsidy/payment action.
- [ ] Audit events are retained for 7 years from the latest relevant closure point.
- [ ] Standalone SDOH proxy datasets expire after 2 years from last operational use.
- [ ] ZIP5 is converted then discarded by default.
- [ ] Purge jobs remove data from caches, indexes, queues, and analytics replicas.
- [ ] Purge execution is logged as an immutable audit event.
- [ ] Backup expiry aligns with this schedule.
- [ ] Legal hold issuance and release are explicit and auditable.

---

## 11. Open Implementation Notes

1. If Amazon QLDB or its successor architecture cannot satisfy time-bounded disposition cleanly, engineering must document the approved archive/decommission pattern before production.
2. If any payer, grant, or state Medicaid rule requires longer retention for a specific workflow, that requirement must be added as a scoped exception rather than expanding all data classes by default.
3. If consumer-report data is used in a way that triggers additional adverse-action or dispute-record obligations, Legal/Compliance must publish a workflow-specific addendum.
4. If any workflow requires retaining raw evidence beyond 24 hours, it must use the protocol’s exception path and separate encryption boundary.

---

## 12. Short Form Schedule

- **Raw financial evidence:** delete immediately after proof issuance; **24-hour max** unless approved exception/hold.  
- **Reduced eligibility proofs:** retain **7 years after final subsidy/payment action**.  
- **Audit events:** retain **7 years after final action / incident / dispute closure, whichever is later**.  
- **Standalone SDOH proxy data:** retain **2 years after last operational use**; if embedded in a retained proof, the proof’s **7-year** rule applies.  
- **Legal hold:** suspend deletion until formal release.
