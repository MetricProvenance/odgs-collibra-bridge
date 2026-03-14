"""
ODGS Collibra Bridge
====================

Transforms Collibra Business Glossary assets into ODGS JSON schemas
for runtime enforcement via the Universal Interceptor.

Usage:
    from odgs_collibra import CollibraBridge

    bridge = CollibraBridge(base_url="https://your-org.collibra.com", api_token="...")
    bridge.sync(community="Finance", output_dir="./schemas/custom/")
"""

__version__ = "1.0.0"

from odgs_collibra.bridge import CollibraBridge
from odgs_collibra.client import CollibraClient
from odgs_collibra.transformer import CollibraTransformer

__all__ = ["CollibraBridge", "CollibraClient", "CollibraTransformer"]
