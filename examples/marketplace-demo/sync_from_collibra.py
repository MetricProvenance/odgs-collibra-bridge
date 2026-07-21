#!/usr/bin/env python3
"""
Step 1 — Sync Collibra Business Glossary → ODGS enforcement schemas.

Uses the real `odgs-collibra-bridge` package (CollibraBridge / CollibraClient)
against the Collibra REST API at http://localhost:8580.
"""

import logging

from odgs_collibra.bridge import CollibraBridge

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(name)s | %(message)s")
logging.getLogger("werkzeug").setLevel(logging.ERROR)

BASE_URL = "http://localhost:8580"
API_TOKEN = "demo-token"

bridge = CollibraBridge(
    base_url=BASE_URL,
    api_token=API_TOKEN,
    organization="acme_finance",
)

# --- Show what's in the glossary before syncing -------------------------
print("=" * 74)
print("Connecting to Collibra:", BASE_URL)
communities = bridge.client.list_communities(name="Finance")
community = communities[0]
print(f"Community:  {community['name']}  ({community['id']})")

domains = bridge.client.list_domains(community_id=community["id"])
domain_by_name = {d["name"]: d for d in domains}
for d in domains:
    print(f"  Domain:   {d['name']}  ({d['id']})")

assets = bridge.client.list_assets(community_id=community["id"])
print(f"\nGlossary assets in community '{community['name']}':")
for a in assets:
    print(f"  [{a.status:>8}] {a.asset_type:<18} {a.name:<35} ({a.domain_name})")
print("=" * 74)

# --- Sync 1: business terms & metrics → ODGS metric definitions ---------
print("\n>>> bridge.sync(community='Finance', output_type='metrics')  [Finance Glossary]")
metrics_path = bridge.sync(
    community="Finance",
    domain_id=domain_by_name["Finance Glossary"]["id"],
    output_dir="./schemas/custom/",
    output_type="metrics",
)

# --- Sync 2: data quality rules → ODGS enforcement rules (HARD_STOP) ----
print("\n>>> bridge.sync(community='Finance', output_type='rules', severity='HARD_STOP')  [Data Quality Rules]")
rules_path = bridge.sync(
    community="Finance",
    domain_id=domain_by_name["Data Quality Rules"]["id"],
    output_dir="./schemas/custom/",
    output_type="rules",
    severity="HARD_STOP",
)

print("\nGenerated ODGS schemas:")
print("  metrics:", metrics_path)
print("  rules:  ", rules_path)
