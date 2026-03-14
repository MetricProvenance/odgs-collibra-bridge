"""
Collibra REST API Client
========================

Lightweight client for reading business glossary assets from Collibra.
Supports both Basic Auth and API Token authentication.

Reference: https://developer.collibra.com/rest/
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

import requests

logger = logging.getLogger("odgs_collibra.client")


@dataclass
class CollibraAsset:
    """Represents a single Collibra asset (business term, metric, data element)."""
    id: str
    name: str
    display_name: str
    asset_type: str
    domain_name: str
    community_name: str
    status: str
    description: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    relations: List[Dict[str, Any]] = field(default_factory=list)


class CollibraClient:
    """
    REST API client for Collibra Data Intelligence Platform.

    Reads business glossary assets, domains, and communities
    for transformation into ODGS schemas.

    Args:
        base_url: Collibra instance URL (e.g., https://your-org.collibra.com)
        api_token: Bearer token for API authentication
        username: Username for Basic Auth (alternative to api_token)
        password: Password for Basic Auth (alternative to api_token)
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        base_url: str,
        api_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()

        if api_token:
            self._session.headers["Authorization"] = f"Bearer {api_token}"
        elif username and password:
            self._session.auth = (username, password)
        else:
            raise ValueError(
                "Either 'api_token' or 'username'+'password' must be provided."
            )

        self._session.headers["Accept"] = "application/json"
        self._session.headers["Content-Type"] = "application/json"

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Execute a GET request against the Collibra REST API."""
        url = f"{self.base_url}/rest/2.0/{endpoint}"
        logger.debug(f"GET {url} params={params}")

        response = self._session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, json_data: Dict) -> Dict:
        """Execute a POST request against the Collibra REST API."""
        url = f"{self.base_url}/rest/2.0/{endpoint}"
        logger.debug(f"POST {url} data={json_data}")

        response = self._session.post(url, json=json_data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def add_asset_comment(self, asset_id: str, content: str) -> Dict:
        """Add a comment to a specific Collibra asset (used for ODGS write-backs)."""
        payload = {
            "baseResourceId": asset_id,
            "baseResourceType": "Asset",
            "content": content
        }
        return self._post("comments", json_data=payload)

    def list_communities(self, name: Optional[str] = None) -> List[Dict]:
        """List all communities, optionally filtered by name."""
        params = {"limit": 100}
        if name:
            params["name"] = name
        result = self._get("communities", params=params)
        return result.get("results", [])

    def list_domains(self, community_id: str) -> List[Dict]:
        """List all domains within a community."""
        params = {"communityId": community_id, "limit": 100}
        result = self._get("domains", params=params)
        return result.get("results", [])

    def list_assets(
        self,
        domain_id: Optional[str] = None,
        community_id: Optional[str] = None,
        asset_type: Optional[str] = None,
        limit: int = 500,
    ) -> List[CollibraAsset]:
        """
        List assets from Collibra, optionally filtered by domain, community, or type.

        Returns a list of CollibraAsset objects with basic metadata.
        """
        params: Dict[str, Any] = {"limit": limit}
        if domain_id:
            params["domainId"] = domain_id
        if community_id:
            params["communityId"] = community_id
        if asset_type:
            params["typeId"] = asset_type

        result = self._get("assets", params=params)
        raw_assets = result.get("results", [])

        assets = []
        for raw in raw_assets:
            asset = CollibraAsset(
                id=raw.get("id", ""),
                name=raw.get("name", ""),
                display_name=raw.get("displayName", raw.get("name", "")),
                asset_type=raw.get("type", {}).get("name", "Unknown"),
                domain_name=raw.get("domain", {}).get("name", ""),
                community_name=raw.get("domain", {}).get("community", {}).get("name", ""),
                status=raw.get("status", {}).get("name", ""),
                description=raw.get("description", ""),
            )
            assets.append(asset)

        logger.info(f"Fetched {len(assets)} assets from Collibra")
        return assets

    def get_asset_attributes(self, asset_id: str) -> Dict[str, Any]:
        """Fetch all attributes for a specific asset."""
        params = {"assetId": asset_id, "limit": 100}
        result = self._get("attributes", params=params)
        raw_attrs = result.get("results", [])

        attributes = {}
        for attr in raw_attrs:
            attr_name = attr.get("type", {}).get("name", "unknown")
            attr_value = attr.get("value", "")
            attributes[attr_name] = attr_value

        return attributes

    def get_asset_relations(self, asset_id: str) -> List[Dict[str, Any]]:
        """Fetch all relations for a specific asset."""
        params = {"sourceId": asset_id, "limit": 100}
        result = self._get("relations", params=params)
        return result.get("results", [])

    def get_enriched_assets(
        self,
        domain_id: Optional[str] = None,
        community_id: Optional[str] = None,
        asset_type: Optional[str] = None,
        include_attributes: bool = True,
        include_relations: bool = False,
    ) -> List[CollibraAsset]:
        """
        Fetch assets with their attributes and optionally relations.

        This makes additional API calls per asset, so use with care on large domains.
        """
        assets = self.list_assets(
            domain_id=domain_id,
            community_id=community_id,
            asset_type=asset_type,
        )

        for asset in assets:
            if include_attributes:
                asset.attributes = self.get_asset_attributes(asset.id)
            if include_relations:
                asset.relations = self.get_asset_relations(asset.id)

        return assets
