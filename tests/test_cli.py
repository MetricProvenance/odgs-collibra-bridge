import os
import tempfile
import json
import pytest
from unittest.mock import patch
from typer.testing import CliRunner
from odgs_collibra.cli import app

runner = CliRunner()

def test_write_back_cli():
    # Create a mock audit log with both formatted and raw JSON lines
    log_content = [
        "2026-03-11 09:50:40 - " + json.dumps({
            "event_id": "test-123",
            "execution_result": "BLOCKED",
            "applied_metadata": {"rule_1": {"collibra_asset_id": "asset-123"}},
            "tri_partite_binding": {"payload_hash": "hash-abc"}
        }),
        json.dumps({
            "event_id": "test-456",
            "execution_result": "APPROVED",
            "applied_metadata": {"rule_2": {"collibra_asset_id": "asset-456"}},
            "tri_partite_binding": {"payload_hash": "hash-def"}
        })
    ]
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("\n".join(log_content))
        log_path = f.name
        
    try:
        with patch("odgs_collibra.client.CollibraClient") as MockClient:
            mock_instance = MockClient.return_value
            
            result = runner.invoke(app, [
                "write-back",
                "--log-path", log_path,
                "--url", "https://mock.collibra.com",
                "--token", "mock-token"
            ])
            
            assert result.exit_code == 0
            assert "Bi-Directional Sync Complete" in result.stdout
            # Ensure the client's add_asset_comment was called twice since there are 2 valid entries.
            assert mock_instance.add_asset_comment.call_count == 2
    finally:
        os.remove(log_path)
