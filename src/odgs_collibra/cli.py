"""
ODGS Collibra Bridge — CLI
===========================

Command-line interface for syncing Collibra business glossary
assets into ODGS enforcement schemas.

Usage:
    odgs-collibra sync \
        --url https://your-org.collibra.com \
        --token YOUR_API_TOKEN \
        --org acme_corp \
        --community "Finance" \
        --output ./schemas/custom/
"""

import os
import sys
import logging

try:
    import typer
except ImportError:
    # typer is part of odgs core dep, but guard anyway
    print("Error: typer is required. Install with: pip install typer>=0.9.0")
    sys.exit(1)

from odgs_collibra.bridge import CollibraBridge

app = typer.Typer(
    name="odgs-collibra",
    help="Bridge: Collibra Business Glossary → ODGS Runtime Enforcement Schemas",
    no_args_is_help=True,
)


@app.command()
def sync(
    url: str = typer.Option(..., "--url", "-u", help="Collibra instance URL"),
    token: str = typer.Option(
        None, "--token", "-t", help="API Bearer token", envvar="COLLIBRA_API_TOKEN"
    ),
    username: str = typer.Option(None, "--username", help="Basic Auth username"),
    password: str = typer.Option(None, "--password", help="Basic Auth password"),
    org: str = typer.Option(
        ..., "--org", "-o", help="Organization name for URN namespace"
    ),
    community: str = typer.Option(
        None, "--community", "-c", help="Filter by Collibra community name"
    ),
    domain_id: str = typer.Option(
        None, "--domain-id", "-d", help="Filter by specific domain ID"
    ),
    output: str = typer.Option(
        "./schemas/custom/", "--output", help="Output directory for ODGS schemas"
    ),
    output_type: str = typer.Option(
        "metrics",
        "--type",
        help="Output type: 'metrics' or 'rules'",
    ),
    severity: str = typer.Option(
        "WARNING",
        "--severity",
        help="Rule severity (HARD_STOP, WARNING, INFO)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    """Sync Collibra business glossary assets into ODGS JSON schemas."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s  %(message)s",
    )

    if not token and not (username and password):
        token = os.environ.get("COLLIBRA_API_TOKEN")
        if not token:
            typer.echo(
                "Error: Provide --token or set COLLIBRA_API_TOKEN environment variable.",
                err=True,
            )
            raise typer.Exit(1)

    try:
        bridge = CollibraBridge(
            base_url=url,
            organization=org,
            api_token=token,
            username=username,
            password=password,
        )
        filepath = bridge.sync(
            community=community,
            domain_id=domain_id,
            output_dir=output,
            output_type=output_type,
            severity=severity,
        )

        if filepath:
            typer.echo(f"\n✅ ODGS schema written to: {filepath}")
        else:
            typer.echo("\n⚠️  No assets found matching the given filters.", err=True)
            raise typer.Exit(1)

    except ValueError as e:
        typer.echo(f"\n❌ Configuration Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"\n❌ Bridge Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def version():
    """Show the bridge version."""
    from odgs_collibra import __version__
    typer.echo(f"odgs-collibra-bridge v{__version__}")


if __name__ == "__main__":
    app()
