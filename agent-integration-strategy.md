# Agent Integration Strategy & Brainstorming Blueprint
**Project Codename:** Crisis-Cost Orchestrator  
**Date:** June 30, 2026  
**Status:** Planning & Brainstorming Phase  

---

## 1. Executive Summary & Vision

The **Crisis-Cost Orchestrator** is a decentralized, real-time economic engine designed to eliminate medical bankruptcy for patients requiring emergency/acute care. It accomplishes this by:
1. Classifying care urgency in real-time (Emergency vs. Routine).
2. Dynamically calculating an annual-income-based affordability cap (limiting patient out-of-pocket costs to 10% of income).
3. Orchestrating instant subsidy payloads from a pre-negotiated pool directly to healthcare providers.

To develop this platform efficiently and with institutional-grade security, compliance, and clinical accuracy, we must harness the specialized agents available in our `agency-agents` library. This document outlines **how** and **where** to deploy these agents across the product lifecycle.

---

## 2. Dynamic Agent-to-Feature Mapping Matrix

Below is a curated mapping of `agency-agents` specialties to the specific functional (F) and non-functional (N) requirements listed in `prd.md`.

### A. Core Engine & AI (Urgency Classification & Pricing)
*   **Target Features:** 
    *   **F-01 (Real-Time Urgency Classifier):** Low-latency (<150ms) classification of clinical vital signs, billing/diagnosis codes (CPT/ICD-10) as standard/acute emergency.
    *   **F-02 (Affordability Engine):** Income-proportionate calculation of out-of-pocket caps.
*   **Assigned Agents:**
    1.  `specialized/medical-billing-coding-specialist.md`: Understands raw billing semantics, CPT/ICD-10 structures, and pricing schedules. Crucial for designing the ingestion payloads.
    2.  `engineering/engineering-ai-engineer.md`: Responsible for creating the rule-based and machine-learning classifier models that run securely within confidential computing architectures.
    3.  `product/product-behavioral-nudge-engine.md`: Crafts micro-copy and UX loops that direct patients to the right care-seeking channels and clearly explain cost-protection thresholds without causing panic.

### B. Distributed Systems & Technical Architecture
*   **Target Features:**
    *   **F-03 (Subsidy Orchestrator):** State management of financial transactions, ledger indexing, and provider payouts using Temporal.io.
    *   **F-04 (Provider EHR Integration API):** High-throughput ingestion gateway using mTLS and Protobuf (gRPC).
*   **Assigned Agents:**
    1.  `engineering/engineering-software-architect.md`: Defines high-level system boundaries, API contracts between hospitals and our platform, and data model mapping.
    2.  `engineering/engineering-backend-architect.md`: Designs the robust Kafka/NATS streaming ingestion pipeline and translates Temporal.io distributed workflow requirements into code.
    3.  `engineering/engineering-autonomous-optimization-architect.md`: Keeps latency strictly under the 150ms p99 SLA (N-01) by profiling and optimizing database query executions and classifier execution runtimes.

### C. Trust, Security, HIPAA & Regulatory Compliance
*   **Target Features:**
    *   **F-06 (Audit Ledger):** Immutable record-keeping of every single classification and payout.
    *   **N-02 (HIPAA Compliance):** End-to-end encryption of Protected Health Information (PHI) at rest and in transit.
*   **Assigned Agents:**
    1.  `specialized/data-privacy-officer.md`: Enforces strict data-minimization practices (e.g., pseudonymizing patient data before it enters public models). Ensures only necessary telemetry is logged.
    2.  `security/security-compliance-auditor.md`: Conducts mock audits against HIPAA Security Rule frameworks and evaluates the Amazon QLDB schema to verify ledger immutability and compliance integrity.
    3.  `security/security-blockchain-security-auditor.md`: Leverages specialized audits on cryptography, ledger verification processes, and transaction signature patterns.

### D. Interface Design & Patient Touchpoints
*   **Target Features:**
    *   **F-05 (Patient Mobile App):** Real-time cost estimates and subsidy tracking interface.
    *   **F-07 (Provider Dashboard):** Reconciliation interface for safety-net Hospital CFOs.
*   **Assigned Agents:**
    1.  `design/design-ux-architect.md` & `design/design-ui-designer.md`: Brainstorms visual flows to make complex economic caps immediate, assuring, and accessible to a diverse user base (ranging from tech-savvy individuals to low-income populations on older devices).
    2.  `engineering/engineering-frontend-developer.md`: Translates design tokens into highly accessible, performance-optimized, and responsive mobile-first interfaces.

---

## 3. Operationalizing the Agents: A Multi-Agent Collaboration Workflow

To build the *Crisis-Cost Orchestrator*, we will deploy the agents in cooperative "workgroups" resembling an agile squad.

```
                           +----------------------------+
                           |  product-manager (Alex)    |  <-- Set Requirements
                           +--------------+-------------+
                                          |
                                          v
                           +----------------------------+
                           | software-architect (Lead)  |  <-- Design System & API
                           +--------------+-------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
                   v                                             v
     +-------------+---------------+               +-------------+---------------+
     | medical-billing-specialist  |               |  security-compliance-audit  |
     +-------------+---------------+               +-------------+---------------+
     | Validate CPT/ICD-10 schemas |               | Enforce HIPAA & Nitro Encl. |
     +-------------+---------------+               +-------------+---------------+
                   |                                             |
                   +----------------------+----------------------+
                                          |
                                          v
                           +--------------+-------------+
                           |   backend-architect (Eng)  |  <-- Build & Optimize
                           +----------------------------+
```

### Stage 1: Design & Verification (The "Three-Box" Review)
1.  **Drafting Specifications:** `engineering-software-architect` drafts API schemas, data contracts, and class logic.
2.  **Domain Assessment:** `medical-billing-coding-specialist` reviews the schema to ensure vital-signs structure and classification fields map standard clinical electronic data formats exactly (e.g., HL7/FHIR compatibility).
3.  **Security Gating:** `security-compliance-auditor` reviews the protocol for PHI ingestion, verifying that patient IDs are securely hashed (pseudonymized) before any pipeline log records them.

### Stage 2: Synthesis & Testing
1.  **Workgroup Action:** `engineering-backend-architect` initiates the codebase stubbing.
2.  **Continuous Evaluation:** Specialized testing agents pipeline API validation checks, mocking live EHR inputs to verify our latency remains below the strict 150ms benchmark.

---

## 4. Immediate Concrete Next Steps

To implement this vision, we propose executing the following roadmap:

1.  **Install Selected Agents in Workspace:**
    Run the install scripts on the identified specialized agents to bring their specific instruction models directly into active play.
2.  **EHR Ingestion Payload Schema (P0):**
    Engage the `medical-billing-coding-specialist` and `software-architect` to build the exact JSON payload contract that safety-net hospital EHR systems will POST towards our `Provider API (F-04)`.
3.  **Audit Trail Specifications:**
    Have the `security-compliance-auditor` write down the security/encryption protocol for patient-income verifying proofs (protecting personal tax proxies while complying with financial privacy laws).

---

*This document is the official record of our brainstorming and planning proceedings. Further iterations should follow standard version-control conventions.*
