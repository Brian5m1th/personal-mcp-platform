"""mcp install — Install MCP servers from the registry."""

import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

import typer
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_cli.core.config import PlatformConfig, get_server_config_path, save_yaml
from mcp_cli.core.secrets import SecretsManager


async def _install_server(server_entry: dict) -> bool:
    """Install a single MCP server."""
    server_id = server_entry.get("id", "unknown")
    install = server_entry.get("install", {})
    method = install.get("method", "npx")
    command = install.get("command", "")

    rprint(f"\n[bold]Installing [cyan]{server_id}[/cyan]...")

    if method == "npx":
        # npm/npx-based install
        package = command.replace("npx ", "").strip()
        cmd = ["npx", "-y", package]
    elif method == "uvx":
        cmd = ["uvx", command.replace("uvx ", "").strip()]
    elif method == "pip":
        cmd = [sys.executable, "-m", "pip", "install", command.replace("pip install ", "").strip()]
    elif method == "npm":
        cmd = ["npm", "install", "-g", command.replace("npm install -g ", "").strip()]
    elif method == "docker":
        rprint(f"[yellow]  Docker-based install: {command}")
        return True
    else:
        rprint(f"[red]  Unknown install method: {method}")
        return False

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode == 0:
            rprint(f"[green]  ✓ Installed successfully[/green]")

            # Save server config
            config_path = get_server_config_path(server_id)
            save_yaml(config_path, {
                "id": server_id,
                "version": server_entry.get("version", "0.0.0"),
                "installed": True,
                "install_method": method,
            })
            return True
        else:
            rprint(f"[red]  ✗ Install failed: {proc.stderr[:200]}[/red]")
            return False
    except subprocess.TimeoutExpired:
        rprint(f"[red]  ✗ Install timed out after 120s[/red]")
        return False
    except FileNotFoundError:
        rprint(f"[red]  ✗ Command not found. Is Node.js/npm installed?[/red]")
        return False


def install_cmd(
    server_id: str = typer.Argument(None, help="Server ID to install (omit for all Tier 1)"),
    tier: str = typer.Option("1", "--tier", "-t", help="Install all servers in a tier (1, 2, 3)"),
    check_secrets: bool = typer.Option(True, "--check-secrets/--no-check-secrets", help="Check for missing secrets"),
):
    """Install MCP servers from the registry."""
    config = PlatformConfig()
    secrets = SecretsManager()

    servers_to_install = []

    if server_id:
        entry = config.get_server(server_id)
        if entry is None:
            rprint(f"[red]Server '{server_id}' not found in registry.[/red]")
            raise typer.Exit(1)
        servers_to_install.append(entry)
    else:
        # Install by tier
        all_servers = config.registry.get("servers", [])
        for s in all_servers:
            if s.get("plan") == f"phase-{tier}" or (not s.get("plan") and tier == "1"):
                servers_to_install.append(s)

    if not servers_to_install:
        rprint(f"[yellow]No servers found to install.[/yellow]")
        return

    rprint(f"[bold]Installing [cyan]{len(servers_to_install)}[/cyan] server(s)...[/bold]")

    # Check for missing secrets
    if check_secrets:
        for s in servers_to_install:
            missing = secrets.check_all_required(s)
            if missing:
                rprint(f"[yellow]  ⚠ Server '{s['id']}' requires secrets: {', '.join(missing)}[/yellow]")
                rprint(f"  [dim]  Set environment variables or run: [bold]mcp secrets set {s['id']}[/bold][/dim]")

    # Install
    results = asyncio.run(_install_all(servers_to_install))

    success = sum(1 for r in results if r)
    rprint(f"\n[bold]Result: {success}/{len(results)} installed successfully[/bold]")


async def _install_all(servers: list[dict]) -> list[bool]:
    results = []
    for s in servers:
        result = await _install_server(s)
        results.append(result)
    return results
