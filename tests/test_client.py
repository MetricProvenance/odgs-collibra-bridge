"""
Tests for the CollibraClient — specifically the null-safety of chained
.get() lookups when Collibra returns an explicit JSON `null` for a field
(not just a missing key), e.g. an asset with no domain/status assigned yet.
"""

from unittest.mock import patch

from odgs_collibra.client import CollibraClient


def make_client():
    return CollibraClient(base_url="https://example.collibra.com", api_token="test-token")


class TestListAssetsNullSafety:
    def test_null_type_domain_status_do_not_crash(self):
        """Regression test: chained raw.get('type', {}).get('name', ...) crashed
        with AttributeError when Collibra returns an explicit `null` (not a missing
        key) for type/domain/status. This should resolve to defaults instead."""
        client = make_client()
        with patch.object(client, "_get") as mock_get:
            mock_get.return_value = {
                "results": [
                    {
                        "id": "asset-001",
                        "name": "Unassigned Term",
                        "type": None,
                        "domain": None,
                        "status": None,
                        "description": "",
                    }
                ]
            }
            assets = client.list_assets()

        assert len(assets) == 1
        asset = assets[0]
        assert asset.asset_type == "Unknown"
        assert asset.domain_name == ""
        assert asset.community_name == ""
        assert asset.status == ""

    def test_null_domain_with_present_community_key_does_not_crash(self):
        """domain present but community nested inside it is null."""
        client = make_client()
        with patch.object(client, "_get") as mock_get:
            mock_get.return_value = {
                "results": [
                    {
                        "id": "asset-002",
                        "name": "Partial Term",
                        "type": {"name": "Business Term"},
                        "domain": {"name": "Finance", "community": None},
                        "status": {"name": "Approved"},
                    }
                ]
            }
            assets = client.list_assets()

        assert assets[0].domain_name == "Finance"
        assert assets[0].community_name == ""

    def test_normal_fully_populated_asset_still_works(self):
        """Non-null happy path — make sure the null-safety fix didn't change
        behavior for well-formed responses."""
        client = make_client()
        with patch.object(client, "_get") as mock_get:
            mock_get.return_value = {
                "results": [
                    {
                        "id": "asset-003",
                        "name": "Net Revenue",
                        "type": {"name": "Business Term"},
                        "domain": {"name": "Financial Metrics", "community": {"name": "Finance"}},
                        "status": {"name": "Approved"},
                        "description": "Revenue after returns.",
                    }
                ]
            }
            assets = client.list_assets()

        asset = assets[0]
        assert asset.asset_type == "Business Term"
        assert asset.domain_name == "Financial Metrics"
        assert asset.community_name == "Finance"
        assert asset.status == "Approved"


class TestGetAssetAttributesNullSafety:
    def test_null_attribute_type_does_not_crash(self):
        client = make_client()
        with patch.object(client, "_get") as mock_get:
            mock_get.return_value = {
                "results": [
                    {"type": None, "value": "some value"},
                ]
            }
            attrs = client.get_asset_attributes("asset-001")

        assert attrs == {"unknown": "some value"}
