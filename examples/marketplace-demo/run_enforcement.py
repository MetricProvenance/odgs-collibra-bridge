#!/usr/bin/env python3
"""
Step 3 — Enforce the Collibra-derived governance rules with the real
ODGS engine (odgs.OdgsInterceptor, the package's public API).

    python3 run_enforcement.py payloads/transaction_ok.json
    python3 run_enforcement.py payloads/transaction_bad.json   # -> HARD_STOP

Flow:
  1. OdgsInterceptor loads the signed rule pack (verifying its ES256 JWS
     against the JWKS endpoint declared in authorities.json).
  2. interceptor.intercept(process_urn, payload) evaluates every bound rule;
     any HARD_STOP violation raises ProcessBlockedException and the engine
     writes a tri-partite-hashed audit record to its audit log.
  3. This script then seals that audit record with an Ed25519 signature
     (keys/audit_ed25519_private.pem) and appends it to audit/signed_audit.jsonl.
"""

import json
import logging
import os
import sys
import datetime

# Keep engine housekeeping quiet for the demo output
logging.getLogger("sovereign_git_logger").setLevel(logging.ERROR)

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

import odgs
from odgs import OdgsInterceptor, ProcessBlockedException

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.join(HERE, "odgs_project")
PROCESS_URN = "urn:odgs:process:finance:record_transaction"

# The engine's GitAuditLogger writes JSONL audit records here (daily rotation)
ENGINE_AUDIT_DIR = os.path.join(os.path.dirname(os.path.abspath(odgs.__file__)), "audit_logs")


def load_payload(path):
    with open(path) as f:
        return json.load(f)


def last_engine_audit_entry():
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(ENGINE_AUDIT_DIR, f"audit_{today}.jsonl")
    with open(path) as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    return json.loads(lines[-1]), path


def ed25519_seal(audit_entry):
    """Sign the engine's audit record with the org's Ed25519 audit key."""
    with open(os.path.join(HERE, "keys", "audit_ed25519_private.pem"), "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=None)
    canonical = json.dumps(audit_entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = priv.sign(canonical)
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)

    # verify before persisting
    Ed25519PublicKey.from_public_bytes(pub_raw).verify(signature, canonical)

    sealed = {
        "audit_entry": audit_entry,
        "seal": {
            "alg": "Ed25519",
            "signature": signature.hex(),
            "public_key": pub_raw.hex(),
            "signed_fields": "canonical-json(audit_entry)",
        },
    }
    os.makedirs(os.path.join(HERE, "audit"), exist_ok=True)
    out_path = os.path.join(HERE, "audit", "signed_audit.jsonl")
    with open(out_path, "a") as f:
        f.write(json.dumps(sealed) + "\n")
    return signature.hex(), pub_raw.hex(), out_path


def main():
    payload_path = sys.argv[1]
    payload = load_payload(payload_path)

    print("=" * 74)
    print(f"ODGS ENFORCEMENT  |  process: {PROCESS_URN}")
    print(f"payload ({os.path.basename(payload_path)}): {json.dumps(payload)}")
    print("-" * 74)

    interceptor = OdgsInterceptor(project_root_path=PROJECT)

    # Report the pack attestation the engine verified at load time
    for rule in interceptor.rules.values():
        att = rule.get("__attestation__")
        if att:
            print(f"rule pack signature : VERIFIED ({att['issuer']}, key {att['key_id']})")
            break
    print(f"active rules loaded : {len(interceptor.rules)}")

    blocked_reason = None
    try:
        interceptor.intercept(process_urn=PROCESS_URN, data_context=payload)
        print("\nVERDICT: APPROVED — all governance rules passed")
    except ProcessBlockedException as e:
        blocked_reason = str(e)
        print(f"\nVERDICT: BLOCKED — {blocked_reason}")

    # The engine has now written its audit record; seal it with Ed25519.
    audit_entry, engine_log = last_engine_audit_entry()
    sig_hex, pub_hex, sealed_log = ed25519_seal(audit_entry)

    print("-" * 74)
    print("AUDIT RECORD (engine-generated, tri-partite binding)")
    print(f"  event_id        : {audit_entry['event_id']}")
    print(f"  verdict         : {audit_entry['verdict']}")
    print(f"  rule_id         : {audit_entry['rule_id']}")
    print(f"  s_cert_status   : {audit_entry['s_cert_status']}  ({audit_entry['certification_status']})")
    print(f"  payload_hash    : {audit_entry['tri_partite_binding']['payload_hash']}")
    print(f"  definition_hash : {audit_entry['tri_partite_binding']['definition_hash']}")
    print(f"  config_hash     : {audit_entry['tri_partite_binding']['config_hash']}")
    if audit_entry["violations"]:
        for v in audit_entry["violations"]:
            print(f"  violation       : {v}")
    print(f"  engine log      : {engine_log}")
    print("AUDIT SEAL (Ed25519, verified)")
    print(f"  signature       : {sig_hex}")
    print(f"  public_key      : {pub_hex}")
    print(f"  sealed log      : {sealed_log}")
    print("=" * 74)

    sys.exit(1 if blocked_reason else 0)


if __name__ == "__main__":
    main()
