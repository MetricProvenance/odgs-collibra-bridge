#!/usr/bin/env bash
# =============================================================================
# ODGS <- Collibra bridge demo (viewer-facing command sequence)
# Assumes the mock Collibra server is already running on http://localhost:8580
# (demo_full.sh starts/stops it around this script).
# =============================================================================
set -e
cd "$(dirname "$0")"

step() { echo; echo "\$ $*"; }

# --- (a) install the bridge + engine (cached, so fast) -----------------------
step "pip install odgs-collibra-bridge odgs"
pip install --break-system-packages -q odgs-collibra-bridge odgs 2>/dev/null || true
pip show odgs-collibra-bridge odgs 2>/dev/null | grep -E '^(Name|Version)'

# --- (b) sync the Collibra Finance community into ODGS schemas ---------------
step "python3 sync_from_collibra.py"
python3 sync_from_collibra.py

# --- (c) look at one generated ODGS schema -----------------------------------
step "head -c 1600 schemas/custom/collibra_acme_finance_rules.json"
head -c 1600 schemas/custom/collibra_acme_finance_rules.json
echo; echo "  ..."

# --- (d) compile + sign the governance pack, then enforce --------------------
step "python3 build_governance_pack.py"
python3 build_governance_pack.py

step "python3 run_enforcement.py payloads/transaction_ok.json"
python3 run_enforcement.py payloads/transaction_ok.json

step "python3 run_enforcement.py payloads/transaction_bad.json"
if python3 run_enforcement.py payloads/transaction_bad.json; then
    echo "ERROR: violating payload was NOT blocked" >&2
    exit 1
else
    echo "(exit code 1 — the violating payload was hard-stopped, as intended)"
fi

echo
echo "Demo complete. Signed audit trail: audit/signed_audit.jsonl"
