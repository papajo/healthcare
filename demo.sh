#!/usr/bin/env bash
# Crisis-Cost Orchestrator — Demo Encounter Flow
# Submits a full encounter through F-04 → F-01 → F-02 → F-03 → F-06
set -euo pipefail

API="http://localhost:8000"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}━━━ Crisis-Cost Orchestrator — Encounter Flow Demo ━━━${NC}\n"

# Check API is running
if ! nc -z localhost 8000 2>/dev/null; then
  echo -e "${YELLOW}API not running. Start it first: ./start.sh --fg${NC}"
  exit 1
fi

# Generate IDs
PATIENT_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
PROVIDER_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
ENCOUNTER_ID="ENC-$(date +%s)"
REQUEST_ID=$(python3 -c "import uuid; print(uuid.uuid4())")

# ─── Step 1: Classify Urgency (F-01) ────────────────────────────────────────

echo -e "${CYAN}[Step 1] F-01: Classify urgency${NC}"

URGENCY_RESULT=$(curl -sf -X POST "$API/v1/urgency/classify" \
  -H "Content-Type: application/json" \
  -d "{
    \"request_id\": \"$REQUEST_ID\",
    \"provider\": {
      \"provider_organization_id\": \"$PROVIDER_ID\",
      \"facility_id\": \"FAC-001\",
      \"facility_type\": \"ACUTE_CARE_HOSPITAL\",
      \"ehr_vendor\": \"EPIC\"
    },
    \"encounter\": {
      \"encounter_id\": \"$ENCOUNTER_ID\",
      \"encounter_class\": \"EMERGENCY\",
      \"encounter_status\": \"IN_TRIAGE\",
      \"arrival_mode\": \"EMS_GROUND\",
      \"occurred_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
      \"service_date\": \"$(date -u +%Y-%m-%d)\",
      \"acuity_level\": \"ESI_2\"
    },
    \"patient\": {
      \"patient_pseudo_id\": \"$PATIENT_ID\",
      \"age_bracket\": \"50-64\",
      \"sex_at_birth\": \"M\"
    },
    \"clinical_context\": {
      \"presenting_problem\": {
        \"chief_complaint_code\": \"29857009\",
        \"chief_complaint_text\": \"chest pain radiating to left arm, shortness of breath\"
      },
      \"vitals\": {
        \"heart_rate_bpm\": 112,
        \"respiratory_rate_bpm\": 24,
        \"spo2_percent\": 93,
        \"temperature_c\": 38.2,
        \"systolic_bp_mmhg\": 92,
        \"diastolic_bp_mmhg\": 58,
        \"pain_score_0_10\": 8
      },
      \"critical_lab_values\": {
        \"troponin_ng_ml\": 0.42
      },
      \"clinical_flags\": [\"CHEST_PAIN\", \"SHORTNESS_OF_BREATH\", \"HYPOTENSION\"],
      \"high_alert_medication_context\": [\"ANTICOAGULANT\"]
    }
  }")

if [ $? -ne 0 ]; then
  echo -e "  ${YELLOW}✗ Classification failed${NC}"
  exit 1
fi

URGENCY=$(echo "$URGENCY_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['urgency_label'])")
CONFIDENCE=$(echo "$URGENCY_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['confidence'])")
PATH_USED=$(echo "$URGENCY_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['classification_path'])")

echo -e "  ${GREEN}✓ Urgency:    $URGENCY${NC}"
echo -e "  ${GREEN}✓ Confidence: $CONFIDENCE${NC}"
echo -e "  ${GREEN}✓ Path:       $PATH_USED${NC}\n"

# ─── Step 2: Calculate Affordability (F-02) ─────────────────────────────────

echo -e "${CYAN}[Step 2] F-02: Calculate patient responsibility${NC}"

AFFORDABILITY=$(curl -sf -X POST "$API/v1/affordability/calculate" \
  -H "Content-Type: application/json" \
  -d "{
    \"encounter_id\": \"$ENCOUNTER_ID\",
    \"patient_pseudo_id\": \"$PATIENT_ID\",
    \"urgency_label\": \"$URGENCY\",
    \"estimated_total_cents\": 4500000,
    \"encounter_class\": \"EMERGENCY\",
    \"eligibility_proof\": {
      \"proof_id\": \"$(python3 -c "import uuid; print(uuid.uuid4())")\",
      \"income_bracket_code\": \"IB-06\",
      \"affordability_tier\": \"TIER-STANDARD\",
      \"eligibility_status_normalized\": \"ELIGIBLE\",
      \"verification_assurance_level\": \"HIGH\",
      \"proof_valid_from\": \"2026-01-01T00:00:00Z\",
      \"proof_valid_to\": \"2026-12-31T23:59:59Z\",
      \"revocation_status\": \"ACTIVE\",
      \"patient_pseudo_id\": \"$PATIENT_ID\"
    }
  }")

TOTAL=45000.00
PATIENT_RESP=$(echo "$AFFORDABILITY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'\${d[\"patient_responsibility_cents\"]/100:,.2f}')")
SUBSIDY_AMT=$(echo "$AFFORDABILITY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'\${d[\"subsidy_amount_cents\"]/100:,.2f}')")
TIER=$(echo "$AFFORDABILITY" | python3 -c "import sys,json; print(json.load(sys.stdin)['tier_applied'])")

echo -e "  ${GREEN}✓ Total cost:          $TOTAL${NC}"
echo -e "  ${GREEN}✓ Patient pays:        $PATIENT_RESP${NC}"
echo -e "  ${GREEN}✓ Platform subsidizes: $SUBSIDY_AMT${NC}"
echo -e "  ${GREEN}✓ Tier applied:        $TIER${NC}\n"

# ─── Step 3: Create & Settle Subsidy (F-03) ─────────────────────────────────

echo -e "${CYAN}[Step 3] F-03: Create and settle subsidy${NC}"

SUBSIDY_AMT_CENTS=$(echo "$AFFORDABILITY" | python3 -c "import sys,json; print(json.load(sys.stdin)['subsidy_amount_cents'])")

SUBSIDY=$(curl -sf -X POST "$API/v1/subsidies" \
  -H "Content-Type: application/json" \
  -d "{
    \"encounter_id\": \"$ENCOUNTER_ID\",
    \"patient_pseudo_id\": \"$PATIENT_ID\",
    \"provider_org_id\": \"$PROVIDER_ID\",
    \"subsidy_amount_cents\": $SUBSIDY_AMT_CENTS
  }")

SUBSIDY_ID=$(echo "$SUBSIDY" | python3 -c "import sys,json; print(json.load(sys.stdin)['subsidy_id'])")
echo -e "  ${GREEN}✓ Subsidy created: $SUBSIDY_ID${NC}"

# Settle it
SETTLED=$(curl -sf -X POST "$API/v1/subsidies/$SUBSIDY_ID/settle")
FINAL_STATUS=$(echo "$SETTLED" | python3 -c "import sys,json; print(json.load(sys.stdin)['subsidy_status'])")
PAYMENT_REF=$(echo "$SETTLED" | python3 -c "import sys,json; print(json.load(sys.stdin).get('payment_reference', 'N/A'))")

echo -e "  ${GREEN}✓ Status:       $FINAL_STATUS${NC}"
echo -e "  ${GREEN}✓ Payment ref:  $PAYMENT_REF${NC}\n"

# ─── Step 4: Audit Trail (F-06) ─────────────────────────────────────────────

echo -e "${CYAN}[Step 4] F-06: Verify audit trail${NC}"

AUDIT=$(curl -sf "$API/v1/audit/events?entity_type=SUBSIDY&entity_id=$SUBSIDY_ID")
EVENT_COUNT=$(echo "$AUDIT" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")

echo -e "  ${GREEN}✓ $EVENT_COUNT audit events for this subsidy${NC}"

INTEGRITY=$(curl -sf "$API/v1/audit/verify")
CHAIN_STATUS=$(echo "$INTEGRITY" | python3 -c "import sys,json; print(json.load(sys.stdin)['chain_status'])")
TOTAL_EVENTS=$(echo "$INTEGRITY" | python3 -c "import sys,json; print(json.load(sys.stdin)['total_events'])")

echo -e "  ${GREEN}✓ Chain: $CHAIN_STATUS | Total events: $TOTAL_EVENTS${NC}\n"

# ─── Done ────────────────────────────────────────────────────────────────────

echo -e "${GREEN}━━━ Flow Complete ━━━${NC}"
echo ""
echo "  Refresh http://localhost:5173 to see audit events on the dashboard."
echo ""
