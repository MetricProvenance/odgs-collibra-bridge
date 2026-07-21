#!/usr/bin/env python3
"""
Mock Collibra Data Intelligence Platform — REST API v2.0
=========================================================

A local stand-in for a Collibra instance, implementing exactly the
endpoints that the `odgs-collibra-bridge` client (odgs_collibra/client.py)
calls:

    GET  /rest/2.0/communities   ?name=&limit=
    GET  /rest/2.0/domains       ?communityId=&limit=
    GET  /rest/2.0/assets        ?domainId=&communityId=&typeId=&limit=
    GET  /rest/2.0/attributes    ?assetId=&limit=
    GET  /rest/2.0/relations     ?sourceId=&limit=
    POST /rest/2.0/comments      (ODGS write-backs)

Plus one extra endpoint used by the ODGS engine's cryptographic
attestation layer (CryptoResolver / PyJWKClient):

    GET  /jwks.json              (public signing keys for the governance pack)

Auth: Bearer token, expects "Authorization: Bearer demo-token".

-----------------------------------------------------------------------
NOTE: ALL DATA BELOW IS SAMPLE DATA, invented for demo purposes only.
It models a believable "Finance" community of a Collibra Business
Glossary (business terms, metrics, and data-quality rules) so the
bridge has something realistic to sync. It is not real company data.
-----------------------------------------------------------------------
"""

import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

PORT = 8580
API_TOKEN = "demo-token"
KEYS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

# ============================================================================
# SAMPLE DATASET (demo purposes only)
# ============================================================================

COMMUNITY = {
    "id": "c0mm-0001-fin-4a2b-9c8d7e6f5a4b",
    "name": "Finance",
    "description": "Finance business glossary and data governance community",
}

DOMAINS = [
    {
        "id": "d0m-1001-glos-4a2b-9c8d7e6f5a4b",
        "name": "Finance Glossary",
        "type": {"name": "Glossary"},
        "communityId": COMMUNITY["id"],
        "community": {"id": COMMUNITY["id"], "name": COMMUNITY["name"]},
        "description": "Approved business terms and KPI definitions for Finance",
    },
    {
        "id": "d0m-1002-dqrl-4a2b-9c8d7e6f5a4b",
        "name": "Data Quality Rules",
        "type": {"name": "Rulebook"},
        "communityId": COMMUNITY["id"],
        "community": {"id": COMMUNITY["id"], "name": COMMUNITY["name"]},
        "description": "Executable data quality rules for financial transaction data",
    },
]

DOM_GLOSSARY = DOMAINS[0]
DOM_DQ = DOMAINS[1]


def _asset(asset_id, name, asset_type, domain, status, description):
    """Build a Collibra-shaped asset resource (matches what client.list_assets reads)."""
    return {
        "id": asset_id,
        "name": name,
        "displayName": name,
        "type": {"id": f"type-{asset_type.lower().replace(' ', '-')}", "name": asset_type},
        "status": {"id": f"status-{status.lower()}", "name": status},
        "domain": {
            "id": domain["id"],
            "name": domain["name"],
            "community": {"id": COMMUNITY["id"], "name": COMMUNITY["name"]},
        },
        "description": description,
    }


# --- SAMPLE business terms & metrics (Finance Glossary domain) ---
ASSETS = [
    _asset(
        "a5e7-2001-netr", "Net Revenue", "Business Term", DOM_GLOSSARY, "Approved",
        "Total revenue recognized in the period after deducting product returns, "
        "allowances, and customer discounts. Primary top-line KPI reported to the board.",
    ),
    _asset(
        "a5e7-2002-chrn", "Customer Churn Rate", "Metric", DOM_GLOSSARY, "Approved",
        "Percentage of active customers at the start of the period that cancelled "
        "all subscriptions during the period. Reported monthly; board threshold is 2.5%.",
    ),
    _asset(
        "a5e7-2003-gmar", "Gross Margin", "Metric", DOM_GLOSSARY, "Approved",
        "Net revenue minus cost of goods sold, expressed as a percentage of net revenue. "
        "Used in quarterly earnings and FP&A variance analysis.",
    ),
    _asset(
        "a5e7-2004-dso", "Days Sales Outstanding", "Metric", DOM_GLOSSARY, "Approved",
        "Average number of days to collect payment after a sale. "
        "Treasury early-warning indicator; escalation threshold is 45 days.",
    ),
    _asset(
        "a5e7-2005-arr", "Annual Recurring Revenue", "Business Term", DOM_GLOSSARY, "Approved",
        "Normalized annualized value of all active recurring subscription contracts, "
        "excluding one-time fees and usage overages.",
    ),
    # --- SAMPLE data quality rules (Data Quality Rules domain) ---
    _asset(
        "a5e7-3001-txnn", "Transaction Amount Non-Negative", "Data Quality Rule", DOM_DQ, "Approved",
        "transaction_amount must be non-negative. Negative amounts must be booked "
        "as refunds through the credit-note process, never as negative transactions.",
    ),
    _asset(
        "a5e7-3002-cidf", "Customer ID Format Check", "Data Quality Rule", DOM_DQ, "Approved",
        "customer_id must not be null and must match the corporate master-data "
        "format CUST-\\d{6} (e.g. CUST-004821).",
    ),
    _asset(
        "a5e7-3003-curw", "Settlement Currency Whitelist", "Data Quality Rule", DOM_DQ, "Approved",
        "Settlement currency must be one of the treasury-approved currencies: "
        "USD, EUR, or GBP.",
    ),
]

# --- SAMPLE attributes per asset (what /rest/2.0/attributes returns) ---
ATTRIBUTES = {
    "a5e7-2001-netr": {
        "Formula": "gross_revenue - returns - allowances - discounts",
        "Description": "Top-line revenue net of returns, allowances and discounts.",
        "Data Steward": "J. Alvarez (Finance Data Office)",
    },
    "a5e7-2002-chrn": {
        "Formula": "(customers_lost_in_period / customers_at_period_start) * 100",
        "Quality Threshold": "<= 2.5% monthly",
        "Data Steward": "M. Okafor (Revenue Operations)",
    },
    "a5e7-2003-gmar": {
        "Formula": "((net_revenue - cost_of_goods_sold) / net_revenue) * 100",
        "Quality Threshold": ">= 62% quarterly",
        "Data Steward": "J. Alvarez (Finance Data Office)",
    },
    "a5e7-2004-dso": {
        "Formula": "(accounts_receivable / total_credit_sales) * days_in_period",
        "Quality Threshold": "<= 45 days",
        "Data Steward": "S. Lindqvist (Treasury)",
    },
    "a5e7-2005-arr": {
        "Calculation Logic": "SUM(active_subscription_mrr) * 12",
        "Data Steward": "M. Okafor (Revenue Operations)",
    },
    "a5e7-3001-txnn": {
        "Logic Expression": "transaction_amount >= 0",
        "Legislative Source": "Finance Data Policy FDP-104 §3.2 (SOX 404 control TXN-07)",
        "Verbatim Source Text": "Transaction amounts recorded in the ledger shall be "
                                "greater than or equal to zero; reversals are processed "
                                "exclusively via credit notes.",
    },
    "a5e7-3002-cidf": {
        "Logic Expression": "customer_id != None and customer_id != '' and "
                            "regex_match('CUST-[0-9]{6}$', customer_id)",
        "Legislative Source": "Master Data Standard MDS-011 §2.1",
        "Verbatim Source Text": "Every financial transaction shall reference a customer "
                                "identifier conforming to the pattern CUST-NNNNNN.",
    },
    "a5e7-3003-curw": {
        "Logic Expression": "currency == 'USD' or currency == 'EUR' or currency == 'GBP'",
        "Legislative Source": "Treasury Policy TP-220 §5 (Approved Settlement Currencies)",
        "Verbatim Source Text": "Settlement of customer transactions is permitted only in "
                                "USD, EUR, or GBP.",
    },
}

# --- SAMPLE relations (kept minimal; bridge only fetches when asked) ---
RELATIONS = {
    "a5e7-3001-txnn": [
        {"id": "rel-9001", "source": {"id": "a5e7-3001-txnn", "name": "Transaction Amount Non-Negative"},
         "target": {"id": "a5e7-2001-netr", "name": "Net Revenue"},
         "type": {"role": "governs", "corole": "is governed by"}},
    ],
}

COMMENTS = []  # ODGS write-backs land here


# ============================================================================
# Auth + helpers
# ============================================================================

def _authorized() -> bool:
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {API_TOKEN}"


def _page(results):
    return jsonify({"total": len(results), "offset": 0, "limit": int(request.args.get("limit", 100)), "results": results})


@app.before_request
def check_auth():
    if request.path.startswith("/rest/2.0/") and not _authorized():
        return jsonify({"statusCode": 401, "titleMessage": "Unauthorized",
                        "userMessage": "Valid bearer token required."}), 401


# ============================================================================
# Collibra REST 2.0 endpoints (exactly what odgs_collibra.client calls)
# ============================================================================

@app.route("/rest/2.0/communities")
def communities():
    name = request.args.get("name")
    results = [COMMUNITY] if (name is None or name == COMMUNITY["name"]) else []
    return _page(results)


@app.route("/rest/2.0/domains")
def domains():
    community_id = request.args.get("communityId")
    results = [d for d in DOMAINS if community_id in (None, d["communityId"])]
    return _page(results)


@app.route("/rest/2.0/assets")
def assets():
    domain_id = request.args.get("domainId")
    community_id = request.args.get("communityId")
    type_id = request.args.get("typeId")
    results = ASSETS
    if domain_id:
        results = [a for a in results if a["domain"]["id"] == domain_id]
    if community_id:
        results = [a for a in results if a["domain"]["community"]["id"] == community_id]
    if type_id:
        results = [a for a in results if a["type"]["id"] == type_id or a["type"]["name"] == type_id]
    return _page(results)


@app.route("/rest/2.0/attributes")
def attributes():
    asset_id = request.args.get("assetId")
    attrs = ATTRIBUTES.get(asset_id, {})
    results = [
        {"id": f"attr-{asset_id}-{i}", "asset": {"id": asset_id},
         "type": {"name": attr_name}, "value": attr_value}
        for i, (attr_name, attr_value) in enumerate(attrs.items())
    ]
    return _page(results)


@app.route("/rest/2.0/relations")
def relations():
    source_id = request.args.get("sourceId")
    return _page(RELATIONS.get(source_id, []))


@app.route("/rest/2.0/comments", methods=["POST"])
def comments():
    payload = request.get_json(force=True, silent=True) or {}
    comment = {"id": f"comment-{len(COMMENTS) + 1}", **payload}
    COMMENTS.append(comment)
    return jsonify(comment), 201


# ============================================================================
# JWKS endpoint — public keys for the signed ODGS governance pack.
# The ODGS engine's CryptoResolver resolves the pack issuer to this URL
# (via authorities.json) and verifies the pack's JWS signature against it.
# ============================================================================

@app.route("/jwks.json")
def jwks():
    jwks_path = os.path.join(KEYS_DIR, "jwks.json")
    if not os.path.exists(jwks_path):
        return jsonify({"keys": []}), 404
    with open(jwks_path) as f:
        return jsonify(json.load(f))


@app.route("/")
def index():
    return jsonify({"service": "mock-collibra", "version": "2.0",
                    "note": "SAMPLE demo instance — Finance community"})


if __name__ == "__main__":
    print(f"Mock Collibra (SAMPLE data) listening on http://localhost:{PORT}")
    app.run(host="127.0.0.1", port=PORT)
