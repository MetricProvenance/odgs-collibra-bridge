# Marketplace Demo — end-to-end without a Collibra tenant

Self-contained demonstration of the ODGS Collibra Bridge: a local mock of the
Collibra REST API (`mock_collibra.py`, port 8580) serves a **sample** Finance
community — 8 glossary assets across Business Terms, Metrics, and Data Quality
rules, clearly labeled sample data. The real, unmodified `odgs-collibra-bridge`
package syncs from it; the real `odgs` engine then enforces the generated rules.

## Run

```bash
pip install odgs-collibra-bridge odgs flask
bash demo_full.sh
```

`demo_full.sh` starts the mock server, runs the full flow, and stops it. Steps
(also runnable individually — see `demo_script.sh`):

1. `sync_from_collibra.py` — bridge fetches the Finance community over the
   Collibra REST API (Bearer auth, paged results) and writes two ODGS schema
   files to `schemas/custom/`
2. `build_governance_pack.py` — compiles the synced rules into an ODGS project
   (legislative/judiciary/executive planes), generates keys if missing, and
   signs the rules pack (ES256 JWS, JWKS served by the mock)
3. `run_enforcement.py payloads/transaction_ok.json` — VERDICT: APPROVED
4. `run_enforcement.py payloads/transaction_bad.json` — VERDICT: BLOCKED
   (HARD_STOP, exit 1) with an audit record

`verified_run_output.txt` is a captured full run for reference;
`manifest.txt` documents the recording timeline of the marketplace demo video.

## Honest accounting

- The rules pack signature is **ES256/JWS**, verified by the engine's own
  `CryptoResolver` against the mock's JWKS at load time (the engine's built-in
  verification supports RS256/ES256/HS256).
- The **Ed25519 "audit seal"** shown in the demo output is applied to the
  engine-generated audit record by `run_enforcement.py` glue — it is a
  demonstration of the S-Cert signing pattern, not a built-in engine feature.
- Everything else — bridge code, API calls, transformation, enforcement,
  blocking — is the real published packages doing real work. Only the glossary
  data is sample data.

The same rig pattern (mock API + real bridge + real engine) is intended to be
reused for the Databricks marketplace listing demo.
