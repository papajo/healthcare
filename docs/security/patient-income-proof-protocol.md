# Patient-Income Verifying Proof Security & Encryption Protocol

**Project:** Crisis-Cost Orchestrator  
**Status:** Draft v1.0  
**Owner:** Security / Compliance  
**Applies To:** Affordability Engine, Subsidy Orchestrator, Provider API, Patient App, Identity Vault, Audit Ledger

---

## 1. Purpose

This protocol defines how the Crisis-Cost Orchestrator securely handles **proofs of eligibility and financial status** used to calculate affordability caps and subsidy eligibility.

It is designed to:

- protect patient privacy and reduce collection of sensitive financial data
- prevent unnecessary exposure of **SDOH proxy data** such as ZIP code and eligibility status
- support auditability of affordability decisions
- align with **HIPAA**, and where applicable, **GLBA**, **FCRA**, **IRS/FTI handling rules**, state privacy laws, and contractual payer/provider obligations

This protocol applies to any workflow that verifies or derives:

- income bracket
- household-size-adjusted affordability tier
- public-program eligibility status
- residency or service-area qualification
- ZIP-derived or geography-derived SDOH proxy attributes

---

## 2. Core Policy: Attribute Proofs, Not Raw Financial Files

The platform MUST use an **attribute-proof model**.

The Crisis-Cost Orchestrator MUST **not** persist raw financial evidence unless legally required and explicitly approved.

### 2.1 Allowed model
A trusted verification component validates raw evidence and issues a **signed eligibility proof** containing only the minimum attributes needed for affordability decisions.

### 2.2 Disallowed model
The platform MUST NOT routinely store or replicate:

- tax returns
- pay stubs
- bank statements
- transaction histories
- full benefit letters
- full consumer report files
- SSNs
- full account numbers
- full 5-digit ZIP code when a lower-granularity service-area code is sufficient

**Default rule:** verify first, reduce to attributes, discard raw evidence.

---

## 3. Regulatory Alignment

## 3.1 HIPAA
Because income and eligibility data are used in connection with healthcare payment/support decisions, they must be treated as **regulated sensitive data** when linked to patient identity or care events.

Controls required:

- minimum necessary use
- access controls
- encryption in transit and at rest
- audit logging
- integrity controls
- workforce access review
- incident response and breach notification readiness

## 3.2 GLBA (when financial institutions or GLBA-regulated service providers are involved)
If data is sourced from banks, financial aggregators, or financial institutions, the organization MUST:

- use contractual service-provider controls
- limit data use to the stated verification purpose
- prohibit secondary use for analytics/marketing
- ensure secure handling consistent with the GLBA Safeguards Rule

## 3.3 FCRA (when consumer report data is used)
If a consumer reporting agency or consumer report is used to assess eligibility:

- permissible purpose MUST be documented
- use MUST be limited to the approved eligibility workflow
- adverse-action or denial workflows MUST be reviewed with legal/compliance
- dispute and correction procedures MUST exist

## 3.4 IRS / Federal Tax Information (FTI)
The preferred design is to **avoid ingesting FTI into the platform**.
If tax-return-derived data is used, only a reduced proof may enter the platform. Raw tax documents or transcripts MUST remain outside the core platform unless a dedicated, approved FTI-compliant environment exists.

## 3.5 State privacy laws and contractual rules
Applicable state privacy laws and payer/provider contract terms MUST be flowed down into:

- retention schedules
- deletion workflows
- consent/authorization language
- vendor data-processing terms

---

## 4. Data Classification

| Data Element | Classification | Storage Rule |
|---|---|---|
| Raw pay stub / bank statement / tax file | Restricted financial evidence | Do not store in core platform |
| Public benefits letter / eligibility screen | Restricted eligibility evidence | Do not store in core platform unless exception-approved |
| Eligibility proof token | Sensitive regulated data | Allowed with encryption and audit |
| Income bracket / affordability tier | Sensitive derived attribute | Allowed with encryption and least privilege |
| Eligibility status | Sensitive SDOH/benefits proxy | Allowed only as normalized enum; encrypted at field level |
| ZIP code | Sensitive SDOH proxy | Convert to service-area code or ZIP3; do not store ZIP5 by default |
| Patient pseudo ID | Sensitive identifier | Allowed; no direct identity meaning |
| Identity mapping | Highest sensitivity | Vault-only |

---

## 5. Approved Data Minimization Rules

### 5.1 Persistent attributes allowed in the core platform
Only the following proof attributes may be persisted:

- `proof_id`
- `patient_pseudo_id`
- `verification_provider_id`
- `verification_method` (document, payroll API, benefits API, manual review)
- `income_bracket_code` (not raw income by default)
- `affordability_tier`
- `eligibility_status_normalized` (enum only)
- `household_size_band` (if required)
- `service_area_code` or `zip3` only if needed
- `proof_valid_from`
- `proof_valid_to`
- `proof_confidence` / `verification_assurance_level`
- `source_type`
- `proof_hash`
- `signature_metadata`
- `revocation_status`
- `consent_reference_id`
- `created_at`, `verified_at`

### 5.2 Data that MUST NOT be persisted in the core platform
- full tax documents
- full pay stubs
- bank account or card numbers
- transaction-level bank data
- SSN / TIN
- exact employer payroll records unless required for manual exception handling
- full consumer report contents
- full 5-digit ZIP code unless a documented exception is approved
- named assistance-program documents when normalized status is sufficient

### 5.3 ZIP code handling rule
ZIP code is treated as an SDOH proxy and MUST be minimized.

- Default: convert ZIP5 to `service_area_code` or `ZIP3` at intake, then discard ZIP5.
- ZIP5 may be used transiently for routing or validation if required, but MUST NOT be stored in the operational database by default.
- If a use case requires ZIP5 retention, it requires documented approval, field-level encryption, restricted access, and a separate retention rule.

### 5.4 Eligibility-status handling rule
Eligibility status is sensitive because it may reveal poverty status, disability status, Medicaid participation, or other protected socioeconomic signals.

- Store only normalized values such as `ELIGIBLE`, `CONDITIONALLY_ELIGIBLE`, `NOT_VERIFIED`, `EXPIRED`.
- If the source program matters operationally, store it separately in encrypted form with restricted access.
- Analytics MUST use aggregated categories, not named benefit programs, unless explicitly approved.

---

## 6. Trust Model and System Roles

## 6.1 Verification Provider
A dedicated verification provider or isolated verification service handles raw financial evidence.

Responsibilities:

- collect evidence securely
- validate source authenticity
- derive reduced attributes
- sign the resulting proof
- delete raw evidence according to the ephemeral retention rule

## 6.2 Core Platform
The core platform consumes only the reduced proof and MUST NOT require raw evidence for normal operation.

## 6.3 Identity Vault
Identity re-linking MUST occur only in the vault boundary.
The affordability engine and analytics layers MUST operate on `patient_pseudo_id`.

## 6.4 Audit Ledger
All material proof lifecycle events MUST be written to the immutable audit ledger.

---

## 7. Cryptographic Protocol

## 7.1 Encryption in transit
All proof-related traffic MUST use:

- TLS 1.3 minimum
- mTLS for service-to-service calls
- certificate pinning or trust-store pinning for high-sensitivity verifier integrations where feasible

No proof payload may be transmitted over email, unsecured webhooks, or shared file drops.

## 7.2 Encryption at rest
All persisted proof data MUST use:

- AES-256-GCM or equivalent authenticated encryption
- envelope encryption via KMS/HSM-backed key management
- separate keys for:
  - proof records
  - identity mapping
  - raw exception artifacts
  - audit exports

## 7.3 Key management
Keys MUST be managed in a FIPS-validated or equivalent approved cryptographic boundary.

Requirements:

- CMKs/HSM-backed keys for production
- automatic rotation at least annually, or more frequently per policy
- access to decrypt operations limited by role and workload identity
- all key use logged
- emergency key disable / revoke process documented

## 7.4 Field-level protection
The following fields MUST be field-level encrypted in addition to storage-level encryption:

- `eligibility_status_normalized`
- source-program metadata if stored
- `service_area_code`/`zip3` when linked to a patient record and not strictly needed in cleartext
- household-size data where retained
- any manual-review notes

## 7.5 Integrity and non-repudiation
Each proof MUST be signed by the issuing verifier.

Approved signing pattern:

- JWS/CWT/COSE-signed token or equivalent signed canonical proof document
- asymmetric key pair per issuer
- signature verification performed on every ingestion
- issuer key registry with versioning and revocation support

Recommended algorithms:

- ECDSA P-256 with SHA-256 for FIPS-aligned deployments
- RSA-3072 only if required for compatibility

## 7.6 Tokenization and hashing
Where joinability is needed without exposing source values:

- use HMAC-SHA-256 tokenization with a secret pepper held in KMS/HSM
- use SHA-256 or stronger for canonical proof hashes
- never use unsalted plain hashes for identity-bearing values

---

## 8. Proof Structure

A proof MUST be a reduced, signed statement of verified attributes.

### 8.1 Required proof fields
```json
{
  "proof_id": "uuid",
  "patient_pseudo_id": "uuid",
  "issuer": "verifier-01",
  "verification_method": "benefits_api",
  "income_bracket_code": "IB-03",
  "affordability_tier": "TIER-LOW",
  "eligibility_status_normalized": "ELIGIBLE",
  "service_area_code": "SA-142",
  "proof_valid_from": "2026-06-30T00:00:00Z",
  "proof_valid_to": "2027-06-30T00:00:00Z",
  "verification_assurance_level": "HIGH",
  "source_type": "STATE_BENEFITS",
  "proof_hash": "base64url...",
  "signature": "base64url...",
  "key_id": "kid-2026-01"
}
```

### 8.2 Optional fields
Optional fields MAY include:

- `household_size_band`
- `manual_review_required`
- `revocation_endpoint`
- `consent_reference_id`

### 8.3 Prohibited proof contents
The proof MUST NOT contain:

- raw income amount unless strictly needed
- SSN/TIN
- account numbers
- full document images
- transaction lists
- raw address when service area or ZIP3 suffices

---

## 9. Eligibility Verification Workflow

## 9.1 Step 1: Consent and notice
Before collecting proof inputs, the patient MUST receive clear notice describing:

- what data source will be checked
- why the check is needed
- what reduced attributes will be retained
- how long records will be kept
- what third parties/processors are involved

A `consent_reference_id` MUST be recorded.

## 9.2 Step 2: Evidence collection in the verifier boundary
Raw evidence, if any, MUST be collected only by the isolated verification provider/service.

Collection channels:

- direct patient upload over TLS
- payroll/benefits API with explicit authorization
- verified document-review workflow
- approved manual review channel

## 9.3 Step 3: Canonicalization and reduction
The verifier MUST:

- validate authenticity
- normalize data into the approved attribute set
- convert ZIP5 to `service_area_code` or `ZIP3`
- normalize benefit/program outcomes to an enum
- remove non-required fields before proof issuance

## 9.4 Step 4: Proof issuance
The verifier issues a signed proof containing only reduced attributes.

## 9.5 Step 5: Proof ingestion
The core platform MUST:

- verify signature
- verify issuer trust
- verify proof validity window
- verify proof has not been revoked
- reject malformed, oversized, or over-verbose proofs
- write proof-ingestion event to the ledger

## 9.6 Step 6: Decision use
The affordability engine may use only the approved reduced attributes.
It MUST NOT call back to raw evidence stores during normal decisioning.

## 9.7 Step 7: Expiry and refresh
Expired proofs MUST NOT be used for new decisions.
The system MUST require refresh/reverification based on policy-defined validity windows.

---

## 10. Access Control Protocol

## 10.1 Least privilege
Access to proof data MUST be restricted by workload and role.

| Role | Access |
|---|---|
| Affordability Engine | Read reduced proof attributes only |
| Subsidy Orchestrator | Read eligibility outcome and decision metadata only |
| Support / Ops | No raw financial evidence; limited case metadata |
| Compliance / Audit | Time-bound audited access to proof records and ledger events |
| Data Science / Analytics | Aggregated or de-identified outputs only |
| Identity Vault Service | Re-identification only for approved payment/legal workflows |

## 10.2 Break-glass access
Break-glass access MUST:

- require documented reason code
- be time-limited
- require approval or dual control where feasible
- generate high-priority audit events and alerts

## 10.3 Segregation of duties
No single operator should be able to:

- alter proof data
- approve exception storage of raw artifacts
- suppress audit logs
- execute retention purge overrides

---

## 11. Audit and Immutable Logging Protocol

All material events MUST be written to the immutable audit ledger (QLDB or approved equivalent).

### 11.1 Required audit events
- `CONSENT_CAPTURED`
- `EVIDENCE_VERIFICATION_STARTED`
- `PROOF_ISSUED`
- `PROOF_INGESTED`
- `PROOF_SIGNATURE_VERIFIED`
- `PROOF_REJECTED`
- `PROOF_READ_FOR_DECISION`
- `AFFORDABILITY_DECISION_COMPUTED`
- `PROOF_EXPIRED`
- `PROOF_REVOKED`
- `BREAK_GLASS_ACCESS_GRANTED`
- `BREAK_GLASS_ACCESS_CLOSED`
- `KEY_ROTATED`
- `LEDGER_DIGEST_VERIFIED`
- `RETENTION_PURGE_EXECUTED`

### 11.2 Audit event content
Audit events MUST include:

- event type
- timestamp
- actor/workload identity
- patient pseudo ID
- proof ID
- reason code
- request correlation ID
- outcome
- cryptographic hash/reference of the proof used

Audit events MUST NOT include raw evidence contents.

### 11.3 Ledger verification
Ledger digest verification MUST run at least daily and on-demand for investigations.
Verification failures MUST trigger incident response.

---

## 12. Retention and Deletion Rules

## 12.1 Raw evidence
Default: raw evidence is **not stored** in the core platform.
If handled by the verifier, it MUST be deleted as soon as proof issuance completes, with a default maximum retention of **24 hours**, unless a documented fraud/legal exception applies.

## 12.2 Reduced proofs
Signed reduced proofs MAY be retained for **7 years after final subsidy/payment action** or longer only if required by law, payer contract, Medicaid/state audit rule, or active legal hold.

## 12.3 Exception artifacts
If manual-review artifacts must be retained:

- store separately from operational systems
- encrypt with a separate key
- restrict access to designated reviewers only
- apply the shortest legally supportable retention period

## 12.4 Deletion method
Deletion MUST include:

- record purge from active stores
- purge from searchable indexes/caches
- tombstone in audit ledger
- crypto-shredding where field/key isolation allows it

## 12.5 Legal hold
Legal hold overrides MUST be explicit, approved, and auditable.

---

## 13. Monitoring and Detection

The system MUST alert on:

- repeated failed proof signature verification
- unknown issuer key IDs
- proof replay attempts
- unusually broad proof reads
- repeated break-glass requests
- access from unauthorized workloads
- retention-purge failures
- ledger digest verification failures

Proof access patterns MUST be included in periodic privacy and security review.

---

## 14. Exception Handling

Any workflow that requires storage of raw financial or benefits evidence MUST have:

- written business justification
- privacy/security review
- retention exception approval
- separate encrypted store
- separate access policy
- documented deletion deadline

Exception use MUST be the rare case, not the default architecture.

---

## 15. Implementation Requirements for Crisis-Cost Orchestrator

The project MUST implement the following concrete controls:

1. **Pseudo-ID only** in affordability, subsidy, and analytics workflows  
2. **Vault-only identity mapping**  
3. **No raw income or full document storage in core systems**  
4. **Field-level encryption** for eligibility status and retained SDOH proxies  
5. **ZIP minimization** to service-area code or ZIP3  
6. **Signed proof tokens** from trusted verifiers  
7. **QLDB audit events** for proof lifecycle and access  
8. **Daily ledger digest verification**  
9. **Ephemeral raw evidence retention** outside the core platform  
10. **7-year retention** for reduced proofs unless superseded by applicable law/contract  
11. **Break-glass controls** for exceptional human access  
12. **Vendor/issuer trust registry** for proof issuers and signing keys  

---

## 16. Definition of Compliance for This Protocol

This protocol is considered implemented when:

- raw evidence is isolated from the core platform
- only reduced proof attributes are stored in operational systems
- proof records are encrypted, signed, and auditable
- SDOH proxy data is minimized and protected
- proof use in affordability decisions is reproducible from ledger evidence
- retention and deletion rules are enforced technically, not just procedurally
- legal/compliance has validated any FCRA/GLBA/FTI edge cases tied to actual data sources

---

## 17. Recommended Next Artifacts

To operationalize this protocol, create:

- `docs/security/hipaa-review.md`
- `docs/security/data-classification.md`
- `docs/security/key-management-standard.md`
- `docs/security/retention-schedule.md`
- `docs/architecture/eligibility-proof-sequence.mmd`
- `schemas/eligibility-proof.schema.json`

---

## 18. Short Form Engineering Rule

**Engineering rule:** never pass raw patient financial evidence through the normal care-cost pipeline. Verify externally, reduce to a signed attribute proof, encrypt it, audit every read, and retain only what is needed to defend the affordability decision.
