"""
Example: Sync Collibra Business Glossary → ODGS Schemas
========================================================

This script demonstrates how to use the ODGS Collibra Bridge
to transform a Collibra community's assets into ODGS enforcement schemas.

Prerequisites:
    pip install odgs-collibra-bridge

Usage:
    export COLLIBRA_API_TOKEN=your-token
    python sync_glossary.py
"""

import os
from odgs_collibra import CollibraBridge

# Configuration — replace with your Collibra instance details
COLLIBRA_URL = os.environ.get("COLLIBRA_URL", "https://your-org.collibra.com")
API_TOKEN = os.environ.get("COLLIBRA_API_TOKEN", "your-api-token")
ORGANIZATION = "acme_corp"  # Your URN namespace
COMMUNITY = "Finance"  # Collibra community to sync

if __name__ == "__main__":
    bridge = CollibraBridge(
        base_url=COLLIBRA_URL,
        api_token=API_TOKEN,
        organization=ORGANIZATION,
    )

    # 1. Sync business terms as ODGS metric definitions
    print("📊 Syncing metric definitions...")
    metrics_path = bridge.sync(
        community=COMMUNITY,
        output_dir="./schemas/custom/",
        output_type="metrics",
    )
    print(f"   → {metrics_path}")

    # 2. Sync data quality rules as ODGS enforcement rules
    print("\n🛡️  Syncing enforcement rules...")
    rules_path = bridge.sync(
        community="Data Quality",
        output_dir="./schemas/custom/",
        output_type="rules",
        severity="HARD_STOP",  # Will block pipeline on violation
    )
    print(f"   → {rules_path}")

    print("\n✅ Done! Load these schemas with the ODGS Interceptor:")
    print("   from odgs.executive.interceptor import OdgsInterceptor")
    print("   interceptor = OdgsInterceptor('./schemas/custom/')")
