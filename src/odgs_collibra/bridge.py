"""
ODGS Collibra Bridge — Orchestrator
====================================

High-level interface for syncing Collibra glossary data
into ODGS schemas on the local filesystem.
"""

import json
import os
import logging
from typing import Optional

from odgs_collibra.client import CollibraClient
from odgs_collibra.transformer import CollibraTransformer

logger = logging.getLogger("odgs_collibra.bridge")


class CollibraBridge:
    """
    High-level orchestrator that syncs Collibra business glossary
    assets into ODGS-compliant JSON schema files.

    Usage:
        bridge = CollibraBridge(
            base_url="https://your-org.collibra.com",
            api_token="your-token",
            organization="acme_corp",
        )
        bridge.sync(community="Finance", output_dir="./schemas/custom/")

    Args:
        base_url: Collibra instance URL
        api_token: Bearer token for authentication
        username: Username for Basic Auth (alternative to api_token)
        password: Password for Basic Auth
        organization: URN namespace for generated schemas
    """

    def __init__(
        self,
        base_url: str,
        organization: str,
        api_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.client = CollibraClient(
            base_url=base_url,
            api_token=api_token,
            username=username,
            password=password,
        )
        self.transformer = CollibraTransformer(organization=organization)

    def sync(
        self,
        community: Optional[str] = None,
        domain_id: Optional[str] = None,
        output_dir: str = "./schemas/custom/",
        output_type: str = "metrics",
        include_attributes: bool = True,
        severity: str = "WARNING",
    ) -> str:
        """
        Sync Collibra assets to ODGS JSON schemas on disk.

        Args:
            community: Filter by Collibra community name
            domain_id: Filter by specific domain ID
            output_dir: Directory to write ODGS JSON files
            output_type: "metrics" or "rules"
            include_attributes: Fetch detailed attributes per asset
            severity: Rule severity level (HARD_STOP, WARNING, INFO)

        Returns:
            Absolute path to the generated schema file.
        """
        community_id = None

        if community:
            communities = self.client.list_communities(name=community)
            if not communities:
                raise ValueError(f"Community '{community}' not found in Collibra.")
            community_id = communities[0].get("id")
            logger.info(f"Found community: {community} ({community_id})")

        # Fetch assets with attributes
        assets = self.client.get_enriched_assets(
            domain_id=domain_id,
            community_id=community_id,
            include_attributes=include_attributes,
        )

        if not assets:
            logger.warning("No assets found matching the given filters.")
            return ""

        logger.info(f"Transforming {len(assets)} Collibra assets → ODGS {output_type}")

        # Transform to ODGS schema
        schema = self.transformer.transform_assets(
            assets=assets,
            output_type=output_type,
            severity=severity,
        )

        # Write to disk
        os.makedirs(output_dir, exist_ok=True)
        filename = f"collibra_{self.transformer.organization}_{output_type}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

        abs_path = os.path.abspath(filepath)
        logger.info(f"✅ Written ODGS schema: {abs_path} ({len(assets)} {output_type})")
        return abs_path
