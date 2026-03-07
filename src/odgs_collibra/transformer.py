"""
Collibra → ODGS Schema Transformer
===================================

Transforms Collibra business glossary assets (terms, metrics, data elements)
into ODGS-compliant JSON schemas for runtime enforcement.
"""

import hashlib
import json
import re
import datetime
from typing import Any, Dict, List, Optional

from odgs_collibra.client import CollibraAsset


def _content_hash(data: Dict) -> str:
    """Generate SHA-256 content hash for immutability verification."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sanitize_urn(name: str) -> str:
    """Convert a display name into a URN-safe identifier."""
    result = (
        name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace("&", "and")
    )
    # Collapse consecutive underscores and strip leading/trailing
    result = re.sub(r"_+", "_", result).strip("_")
    return result


class CollibraTransformer:
    """
    Transforms Collibra assets into ODGS JSON schemas.

    Supports two output types:
    - **Metric definitions** (for business terms / KPIs)
    - **Enforcement rules** (for data quality / governance policies)

    Args:
        organization: Organization identifier for URN namespace
            (e.g., "acme_corp" → urn:odgs:custom:acme_corp:*)
    """

    def __init__(self, organization: str):
        self.organization = _sanitize_urn(organization)

    def asset_to_metric(self, asset: CollibraAsset) -> Dict[str, Any]:
        """
        Transform a Collibra business term / metric asset into an ODGS metric definition.

        Returns an ODGS-compliant metric JSON object.
        """
        metric_id = _sanitize_urn(asset.name)
        urn = f"urn:odgs:custom:{self.organization}:{metric_id}"

        # Extract formula from attributes if present
        formula = (
            asset.attributes.get("Formula", "")
            or asset.attributes.get("Calculation Logic", "")
            or asset.attributes.get("Definition", "")
        )

        metric = {
            "metric_id": metric_id,
            "metric_urn": urn,
            "name": asset.display_name,
            "description": asset.description or asset.attributes.get("Description", ""),
            "domain": asset.domain_name,
            "source_authority": f"collibra:{asset.community_name}",
            "logic": {
                "formula": formula,
                "source_system": "collibra",
                "source_asset_id": asset.id,
            },
            "compliance": {
                "collibra_status": asset.status,
                "governance_domain": asset.domain_name,
            },
            "provenance": {
                "bridge": "odgs-collibra-bridge",
                "bridge_version": "0.1.0",
                "synced_at": datetime.datetime.utcnow().isoformat() + "Z",
                "source_url": f"collibra://{asset.id}",
            },
        }

        metric["content_hash"] = _content_hash(metric)
        return metric

    def asset_to_rule(
        self,
        asset: CollibraAsset,
        severity: str = "WARNING",
    ) -> Dict[str, Any]:
        """
        Transform a Collibra data quality rule / policy into an ODGS enforcement rule.

        Args:
            asset: The Collibra asset representing a DQ rule or policy
            severity: ODGS severity level (HARD_STOP, WARNING, INFO)
        """
        rule_id = _sanitize_urn(asset.name)
        urn = f"urn:odgs:custom:{self.organization}:rule:{rule_id}"

        # Try to extract logic expression from attributes
        logic_expr = (
            asset.attributes.get("Logic Expression", "")
            or asset.attributes.get("Validation Rule", "")
            or asset.attributes.get("Business Rule", "")
        )

        rule = {
            "rule_id": rule_id,
            "rule_urn": urn,
            "name": asset.display_name,
            "description": asset.description or asset.attributes.get("Description", ""),
            "domain": asset.domain_name,
            "severity": severity,
            "logic_expression": logic_expr,
            "source_authority": f"collibra:{asset.community_name}",
            "provenance": {
                "bridge": "odgs-collibra-bridge",
                "bridge_version": "0.1.0",
                "synced_at": datetime.datetime.utcnow().isoformat() + "Z",
                "source_url": f"collibra://{asset.id}",
            },
        }

        rule["content_hash"] = _content_hash(rule)
        return rule

    def transform_assets(
        self,
        assets: List[CollibraAsset],
        output_type: str = "metrics",
        severity: str = "WARNING",
    ) -> Dict[str, Any]:
        """
        Transform a list of Collibra assets into an ODGS schema pack.

        Args:
            assets: List of CollibraAsset objects
            output_type: "metrics" or "rules"
            severity: Severity for rule output (HARD_STOP, WARNING, INFO)

        Returns:
            ODGS-compliant schema dictionary ready for JSON serialization.
        """
        items = []
        for asset in assets:
            if output_type == "metrics":
                items.append(self.asset_to_metric(asset))
            elif output_type == "rules":
                items.append(self.asset_to_rule(asset, severity=severity))

        schema = {
            "$schema": "https://metricprovenance.com/schemas/odgs/v4",
            "metadata": {
                "source": "collibra",
                "organization": self.organization,
                "bridge": "odgs-collibra-bridge",
                "bridge_version": "0.1.0",
                "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "asset_count": len(items),
            },
            "items": items,
        }

        return schema
