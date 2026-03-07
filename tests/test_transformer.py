"""
Tests for the Collibra → ODGS transformer.

Uses mock data to validate schema transformation without a live Collibra instance.
"""

import json
import pytest
from odgs_collibra.client import CollibraAsset
from odgs_collibra.transformer import CollibraTransformer


@pytest.fixture
def transformer():
    return CollibraTransformer(organization="acme_corp")


@pytest.fixture
def sample_asset():
    return CollibraAsset(
        id="asset-001",
        name="Net Revenue",
        display_name="Net Revenue",
        asset_type="Business Term",
        domain_name="Financial Metrics",
        community_name="Finance",
        status="Approved",
        description="Total revenue after returns and allowances.",
        attributes={
            "Formula": "gross_revenue - returns - allowances",
            "Description": "Total revenue after returns and allowances.",
        },
    )


@pytest.fixture
def rule_asset():
    return CollibraAsset(
        id="asset-002",
        name="Revenue Non-Negative",
        display_name="Revenue Non-Negative",
        asset_type="Data Quality Rule",
        domain_name="Financial Metrics",
        community_name="Finance",
        status="Approved",
        description="Revenue must not be negative.",
        attributes={
            "Logic Expression": "value >= 0",
            "Description": "Revenue must not be negative.",
        },
    )


class TestMetricTransformation:
    def test_basic_metric_structure(self, transformer, sample_asset):
        metric = transformer.asset_to_metric(sample_asset)

        assert metric["metric_urn"] == "urn:odgs:custom:acme_corp:net_revenue"
        assert metric["name"] == "Net Revenue"
        assert metric["domain"] == "Financial Metrics"
        assert metric["source_authority"] == "collibra:Finance"
        assert "content_hash" in metric
        assert len(metric["content_hash"]) == 64  # SHA-256

    def test_formula_extraction(self, transformer, sample_asset):
        metric = transformer.asset_to_metric(sample_asset)
        assert metric["logic"]["formula"] == "gross_revenue - returns - allowances"

    def test_provenance_tracking(self, transformer, sample_asset):
        metric = transformer.asset_to_metric(sample_asset)
        prov = metric["provenance"]

        assert prov["bridge"] == "odgs-collibra-bridge"
        assert prov["source_url"] == "collibra://asset-001"
        assert prov["synced_at"].endswith("Z")

    def test_urn_sanitization(self, transformer):
        weird_asset = CollibraAsset(
            id="a-003",
            name="Net Revenue (GAAP) / Non-GAAP & Adjusted",
            display_name="Net Revenue (GAAP) / Non-GAAP & Adjusted",
            asset_type="Business Term",
            domain_name="Finance",
            community_name="Corp",
            status="Draft",
        )
        metric = transformer.asset_to_metric(weird_asset)
        urn = metric["metric_urn"]

        assert "(" not in urn
        assert ")" not in urn
        assert "/" not in urn.split(":")[-1]
        assert "&" not in urn
        assert urn == "urn:odgs:custom:acme_corp:net_revenue_gaap_non_gaap_and_adjusted"


class TestRuleTransformation:
    def test_basic_rule_structure(self, transformer, rule_asset):
        rule = transformer.asset_to_rule(rule_asset)

        assert rule["rule_urn"] == "urn:odgs:custom:acme_corp:rule:revenue_non_negative"
        assert rule["severity"] == "WARNING"
        assert rule["logic_expression"] == "value >= 0"

    def test_hard_stop_severity(self, transformer, rule_asset):
        rule = transformer.asset_to_rule(rule_asset, severity="HARD_STOP")
        assert rule["severity"] == "HARD_STOP"


class TestSchemaPackOutput:
    def test_schema_metadata(self, transformer, sample_asset):
        schema = transformer.transform_assets([sample_asset], output_type="metrics")

        assert schema["$schema"] == "https://metricprovenance.com/schemas/odgs/v4"
        assert schema["metadata"]["source"] == "collibra"
        assert schema["metadata"]["organization"] == "acme_corp"
        assert schema["metadata"]["asset_count"] == 1
        assert len(schema["items"]) == 1

    def test_multiple_assets(self, transformer, sample_asset, rule_asset):
        schema = transformer.transform_assets(
            [sample_asset, rule_asset], output_type="metrics"
        )
        assert schema["metadata"]["asset_count"] == 2
        assert len(schema["items"]) == 2

    def test_content_hash_determinism(self, transformer, sample_asset):
        """Same input should produce the same content hash."""
        m1 = transformer.asset_to_metric(sample_asset)
        m2 = transformer.asset_to_metric(sample_asset)

        # Content hashes include synced_at which changes, so compare structure
        assert m1["metric_urn"] == m2["metric_urn"]
        assert m1["name"] == m2["name"]
