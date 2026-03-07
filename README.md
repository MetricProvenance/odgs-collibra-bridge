# ODGS Collibra Bridge

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![ODGS](https://img.shields.io/badge/ODGS-v4.0.1-0055AA)](https://github.com/MetricProvenance/odgs-protocol)

**Transform your Collibra Business Glossary into active ODGS runtime enforcement schemas.**

> Collibra documents your data. ODGS enforces it.

---

## What It Does

The ODGS Collibra Bridge connects to your Collibra Data Intelligence Platform and transforms passive business glossary assets (terms, metrics, data quality rules) into ODGS-compliant JSON schemas that the [Universal Interceptor](https://github.com/MetricProvenance/odgs-protocol) can enforce at runtime.

```
Collibra REST API                 ODGS
┌──────────────┐     Bridge      ┌──────────────┐
│ Business     │ ──────────────→ │ JSON Schema  │
│ Glossary     │   reads terms,  │ + Interceptor│
│ + Data Dict. │   outputs ODGS  │ = Enforcement│
└──────────────┘                 └──────────────┘
```

## Install

```bash
pip install odgs-collibra-bridge
```

## Quick Start

### Python API

```python
from odgs_collibra import CollibraBridge

bridge = CollibraBridge(
    base_url="https://your-org.collibra.com",
    api_token="your-api-token",
    organization="acme_corp",
)

# Sync Finance community → ODGS metric schemas
bridge.sync(
    community="Finance",
    output_dir="./schemas/custom/",
    output_type="metrics",
)

# Sync DQ rules → ODGS enforcement rules
bridge.sync(
    community="Data Quality",
    output_dir="./schemas/custom/",
    output_type="rules",
    severity="HARD_STOP",
)
```

### CLI

```bash
# Sync using API token
odgs-collibra sync \
    --url https://your-org.collibra.com \
    --token YOUR_API_TOKEN \
    --org acme_corp \
    --community "Finance" \
    --output ./schemas/custom/ \
    --type metrics

# Or use environment variable
export COLLIBRA_API_TOKEN=your-token
odgs-collibra sync \
    --url https://your-org.collibra.com \
    --org acme_corp \
    --community "Finance"
```

### Output

The bridge generates ODGS-compliant JSON schemas:

```json
{
  "$schema": "https://metricprovenance.com/schemas/odgs/v4",
  "metadata": {
    "source": "collibra",
    "organization": "acme_corp",
    "bridge": "odgs-collibra-bridge",
    "asset_count": 42
  },
  "items": [
    {
      "metric_urn": "urn:odgs:custom:acme_corp:net_revenue",
      "name": "Net Revenue",
      "logic": { "formula": "gross_revenue - returns" },
      "content_hash": "a1b2c3..."
    }
  ]
}
```

These schemas can be loaded directly by the [ODGS Interceptor](https://github.com/MetricProvenance/odgs-protocol) for runtime enforcement.

## Authentication

The bridge supports two authentication methods:

| Method | Flag | Environment Variable |
|---|---|---|
| API Token (recommended) | `--token` | `COLLIBRA_API_TOKEN` |
| Basic Auth | `--username` + `--password` | — |

## URN Namespace

All generated schemas use the `urn:odgs:custom:<org>:*` namespace, ensuring clean separation from Sovereign URNs (`urn:odgs:sov:*`) and other organizations.

## Requirements

- Python ≥ 3.9
- `odgs` ≥ 4.0.0 (core protocol)
- Collibra Data Intelligence Platform (any version with REST API v2)

## Related

- [ODGS Protocol](https://github.com/MetricProvenance/odgs-protocol) — The core enforcement engine
- [ODGS Databricks Bridge](https://github.com/MetricProvenance/odgs-databricks-bridge) — Unity Catalog integration (planned)
- [ODGS Snowflake Bridge](https://github.com/MetricProvenance/odgs-snowflake-bridge) — Snowflake integration (planned)

---

## License

Apache 2.0 — [Metric Provenance](https://metricprovenance.com) | The Hague, NL 🇳🇱
