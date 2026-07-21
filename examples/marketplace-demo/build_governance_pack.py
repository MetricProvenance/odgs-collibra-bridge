#!/usr/bin/env python3
"""
Step 2 — Compile the bridge-generated schemas into an enforceable
ODGS Sovereign Project and cryptographically sign the rule pack.

The ODGS engine (OdgsInterceptor) loads a 3-plane project layout:

    odgs_project/
      legislative/ontology_graph.json       (concept graph)
      legislative/standard_metrics.json     (metric definitions  <- bridge output)
      judiciary/standard_data_rules.json    (enforcement rules   <- bridge output, JWS-signed)
      executive/context_bindings.json       (binds process URNs -> rule URNs)
      authorities.json                      (issuer -> JWKS endpoint for signature verification)

Signing:
  * The judiciary rule pack is signed with an ES256 JWS (the engine's
    CryptoResolver verifies it against the JWKS endpoint at runtime).
  * An Ed25519 keypair is generated for sealing audit records
    (used by run_enforcement.py).
"""

import json
import hashlib
import os

import jwt
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives import serialization

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = os.path.join(HERE, "keys")
PROJECT = os.path.join(HERE, "odgs_project")

ISSUER = "did:web:governance.acme-finance.demo"
KID = "acme-gov-2026-01"
JWKS_URL = "http://localhost:8580/jwks.json"
PROCESS_URN = "urn:odgs:process:finance:record_transaction"

os.makedirs(KEYS, exist_ok=True)
for plane in ("legislative", "judiciary", "executive"):
    os.makedirs(os.path.join(PROJECT, plane), exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Keys
# ---------------------------------------------------------------------------

def _write_pem_private(key, path):
    with open(path, "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))

ec_key_path = os.path.join(KEYS, "es256_pack_signing_key.pem")
if os.path.exists(ec_key_path):
    with open(ec_key_path, "rb") as f:
        ec_key = serialization.load_pem_private_key(f.read(), password=None)
    print(f"[keys] Reusing ES256 pack-signing key: {ec_key_path}")
else:
    ec_key = ec.generate_private_key(ec.SECP256R1())
    _write_pem_private(ec_key, ec_key_path)
    print(f"[keys] Generated ES256 (P-256) pack-signing keypair -> {ec_key_path}")

# Publish public key as JWKS (served by the mock server at /jwks.json)
jwk = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(ec_key.public_key()))
jwk.update({"kid": KID, "use": "sig", "alg": "ES256"})
with open(os.path.join(KEYS, "jwks.json"), "w") as f:
    json.dump({"keys": [jwk]}, f, indent=2)
print(f"[keys] Published public JWKS -> keys/jwks.json (served at {JWKS_URL})")

ed_key_path = os.path.join(KEYS, "audit_ed25519_private.pem")
if os.path.exists(ed_key_path):
    print(f"[keys] Reusing Ed25519 audit-sealing key: {ed_key_path}")
else:
    ed_key = ed25519.Ed25519PrivateKey.generate()
    _write_pem_private(ed_key, ed_key_path)
    print(f"[keys] Generated Ed25519 audit-sealing keypair -> {ed_key_path}")

# ---------------------------------------------------------------------------
# 2. Load the bridge-generated ODGS schemas
# ---------------------------------------------------------------------------

with open(os.path.join(HERE, "schemas/custom/collibra_acme_finance_metrics.json")) as f:
    metrics_schema = json.load(f)
with open(os.path.join(HERE, "schemas/custom/collibra_acme_finance_rules.json")) as f:
    rules_schema = json.load(f)

rules = rules_schema["items"]
rule_urns = [f"urn:odgs:rule:{r['rule_id']}" for r in rules]

print(f"\n[compile] {len(metrics_schema['items'])} metrics, {len(rules)} enforcement rules from Collibra sync")
for r in rules:
    print(f"  - {r['rule_id']}: {r['logic_expression']}  [{r['severity']}]")

# ---------------------------------------------------------------------------
# 3. Write the 3-plane Sovereign Project
# ---------------------------------------------------------------------------

# Legislative plane: metric definitions + concept graph
with open(os.path.join(PROJECT, "legislative", "standard_metrics.json"), "w") as f:
    json.dump(metrics_schema, f, indent=2)

ontology = {
    "graph_edges": [
        {"source_urn": urn, "target_urn": PROCESS_URN, "relationship": "BLOCKS_PROCESS"}
        for urn in rule_urns
    ]
}
with open(os.path.join(PROJECT, "legislative", "ontology_graph.json"), "w") as f:
    json.dump(ontology, f, indent=2)

# Judiciary plane: the rule pack (signed below)
pack = {
    "pack_id": "collibra_acme_finance_dq",
    "source": rules_schema["metadata"],
    "rules": rules,
}

canonical = json.dumps(pack, sort_keys=True, separators=(",", ":"))
file_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
signature = jwt.encode(
    {"iss": ISSUER, "file_hash": file_hash},
    ec_key,
    algorithm="ES256",
    headers={"kid": KID},
)
pack["signature"] = signature

with open(os.path.join(PROJECT, "judiciary", "standard_data_rules.json"), "w") as f:
    json.dump(pack, f, indent=2)

print(f"\n[sign] Rule pack canonical SHA-256: {file_hash}")
print(f"[sign] JWS (ES256, kid={KID}, iss={ISSUER}):")
print(f"       {signature[:88]}...")

# Executive plane: bind the payment-recording process to the DQ rules
bindings = {
    "contexts": [
        {
            "context_id": PROCESS_URN,
            "description": "Recording a customer transaction in the finance ledger",
            "rules": rule_urns,
        }
    ]
}
with open(os.path.join(PROJECT, "executive", "context_bindings.json"), "w") as f:
    json.dump(bindings, f, indent=2)

# Trust anchors: issuer -> JWKS endpoint (engine verifies the pack signature here)
with open(os.path.join(PROJECT, "authorities.json"), "w") as f:
    json.dump({ISSUER: JWKS_URL}, f, indent=2)

with open(os.path.join(PROJECT, "odgs.json"), "w") as f:
    json.dump({"project_name": "acme_finance_governance", "architecture": "sovereign_v1"}, f, indent=2)

print(f"\n[done] ODGS Sovereign Project written to {PROJECT}/")
print(f"       process context: {PROCESS_URN}")
print(f"       bound rules:     {len(rule_urns)}")
