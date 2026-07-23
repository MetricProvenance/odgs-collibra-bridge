# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
adhering to [Semantic Versioning](https://semver.org/).

## [v0.4.3] - 2026-07-23

### 🐛 Fixed

- **`content_hash` was computed after `provenance.synced_at` (a live timestamp) was already added to the dict**, so the hash changed on every single sync run even when the underlying Collibra asset was byte-for-byte unchanged — defeating the whole point of content hashing for immutability verification. Hash is now computed before provenance is attached.
- **Null-unsafe chained `.get()` calls** in `client.py` crashed with `AttributeError` whenever Collibra returned an explicit JSON `null` for `type`, `domain`, `domain.community`, or `status` (not just a missing key) — e.g. an asset with no domain/status assigned yet. Fixed with `(raw.get("x") or {}).get(...)`.
- **`transform_assets` silently no-op'd** on an unrecognized `output_type` (e.g. a CLI typo) — wrote a valid-looking but empty schema file instead of failing. Now raises `ValueError`.
- **`communities[0]`** was taken unconditionally from a name-filtered search with no exact-match check; if Collibra's `name` query does partial matching, the bridge could silently sync the wrong community. Now prefers an exact name match, warns and falls back to the first result otherwise.
- **Hardcoded `"0.4.2"` `bridge_version` literal** in three separate places in `transformer.py` instead of importing `odgs_collibra.__version__` — the same drift class of bug that v0.4.1 fixed once already. Now references `__version__` everywhere.

### 📄 Docs

- Fixed this changelog's own structure: a rename-instead-of-insert commit had turned a genuine `[0.2.0]` entry into a second, unrelated `[v0.3.0]` entry (this file used to have two different `v0.3.0` sections). Restored the correct `[0.2.0]` heading below and moved the `# Changelog` title back to the top of the file.
- README's Output Schema example didn't match any real code path (mixed metric and rule fields, plus a `plain_english_description` field that's never emitted anywhere) — corrected to a real `asset_to_metric()`/`asset_to_rule()` output.
- README architecture diagram said `LOG_ONLY`; the actual code/docstrings say `INFO` — diagram corrected to match.
- `LICENSE` had a stale copyright holder ("Authentic Intelligence Labs", 2025) predating every dated release — updated to Metric Provenance, 2026.

## [v0.4.2] - 2026-07-20

### Docs

- Removed a committee/standards-body reference from the README that named specific external bodies — the standard and the software are two different things and this repo's docs should describe the latter, not standardization-process status.

## [v0.4.1] - 2026-07-18

### 🔧 Fixed — Version unification

- **Unified version metadata:** `pyproject.toml`, `__version__`, and the `bridge_version` stamped into emitted ODGS schemas now all report `0.4.1`. Previously these disagreed (package 0.4.0, `__version__` 1.0.0, emitted `bridge_version` stale), which made provenance metadata in generated schemas unreliable.

No functional changes to transformation logic.

## [v0.4.0] - 2026-04-13

### ✨ Added — ODGS v6.0 Compatibility

- **`SOFT_STOP` severity support:** CLI `--severity` flag and Python API now accept `SOFT_STOP`, the override-gated severity introduced in ODGS v6.0.0. Existing `HARD_STOP`, `WARNING`, and `INFO` remain unchanged.
- **Badge updated** to `v5.1+ | v6.0 Compatible` — signals forward compatibility with the ODGS Sovereign Validation Engine.
- **Architecture diagram** updated to include `SOFT_STOP` in the Universal Interceptor severity list.

### 🔗 Compatibility

- Requires `odgs>=5.1.0` — works with both v5.x and v6.0 engines.
- All changes are **additive, backward-compatible, and non-breaking**.

---

## [v0.3.0] - 2026-03-19

### ✨ Added

- **Legislative lineage fields (ODGS S-Cert v5.1.0):** Rules now include:
  - `legislative_source` — declares the source authority (defaults to `"BRIDGE_GENERATED_UNATTESTED"`; set explicitly in asset attributes to declare your legislative source)
  - `verbatim_source_text` — optional raw text from source (Collibra bridge reads from asset attributes)
  - `semantic_hash: "UNATTESTED"` — placeholder for Registry-attested SHA-256 hash; upgrade to Registry at https://registry.metricprovenance.com
  - `verdict_on_pass: "PASS"` — explicit pass verdict per ODGS S-Cert specification

- **Bridge version bumped to 0.3.0** in all generated schema packs.

### ⚠️ Migration Notes

All new fields are additive. Existing schemas continue to work. Rules without `legislative_source` set in source attributes will show `"BRIDGE_GENERATED_UNATTESTED"`.

## [0.2.0] - 2026-03-19

### 🔧 Fixed
- **Python 3.14 Forward Compatibility:** Replaced deprecated `datetime.datetime.utcnow()` with
  `datetime.datetime.now(datetime.timezone.utc)`. Timestamp format changes from
  `"2026-03-19T12:00:00Z"` (naive UTC with `Z`) to `"2026-03-19T12:00:00+00:00"` (timezone-aware ISO 8601).
- **Schema Reference:** Updated `$schema` URL from `schemas/odgs/v4` → `schemas/odgs/v5` to reflect
  compatibility with the ODGS v5.0.x polymorphic execution engine.
- **Provenance Metadata:** `bridge_version` field in all generated ODGS schemas now correctly reports `0.2.0`.

### 🔗 Compatibility
- Requires `odgs>=5.1.0` — targets the ODGS v5.1.0 audit engine (S-Cert, LOG_ONLY, temporal bounds).

## [0.1.0] - 2026-03-07

### 🚀 Initial Release
- Collibra Business Glossary → ODGS Schema transformation engine.
- Converts Collibra assets (business terms, DQ rules) into ODGS-compliant JSON schemas.
- CLI: `odgs-collibra bridge` command for direct integration pipeline.
- SHA-256 content hashing for immutability verification.
- Supports `metrics` and `rules` output types.
