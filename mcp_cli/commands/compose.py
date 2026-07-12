"""mcp compose — Docker Compose management for MCP servers."""
import os
import subprocess
import sys
from pathlib import Path

import typer
from rich import print as rprint
from rich.table import Table


def _get_compose_file() -> Path:
    """Find the docker-compose.yml relative to the package root."""
    pkg_dir = Path(__file__).resolve().parent.parent.parent
    compose = pkg_dir / "docker" / "docker-compose.yml"
    if not compose.exists():
        compose = pkg_dir / "docker-compose.yml"
    return compose


def _run_compose(args: list[str]) -> bool:
    """Run a docker compose command."""
    compose_file = _get_compose_file()
    if not compose_file.exists():
        rprint(f"[red]docker-compose.yml not found at {compose_file}[/red]")
        return False

    cmd = ["docker", "compose", "-f", str(compose_file), *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.stdout:
            rprint(proc.stdout)
        if proc.stderr:
            rprint(f"[yellow]{proc.stderr}[/yellow]")
        if proc.returncode != 0:
            rprint(f"[red]Command failed with code {proc.returncode}[/red]")
            return False
        return True
    except FileNotFoundError:
        rprint("[red]Docker not found. Install Docker Desktop or Docker Engine.[/red]")
        return False


def compose_cmd(
    action: str = typer.Argument("status", help="Action: up, down, status, ps, logs, restart"),
    profile: str = typer.Option(None, "--profile", "-p", help="Docker Compose profile (full, backend, etc)"),
):
    """Manage MCP servers via Docker Compose."""
    if action == "up":
        compose_args = ["up", "-d"]
        if profile:
            compose_args.extend(["--profile", profile])
        rprint(f"[bold]Starting MCP stack via Docker Compose...[/bold]")
        if _run_compose(compose_args):
            rprint("[green]v MCP stack started[/green]")

    elif action == "down":
        rprint("[bold]Stopping MCP stack...[/bold]")
        if _run_compose(["down"]):
            rprint("[green]v MCP stack stopped[/green]")

    elif action == "status":
        _run_compose(["ps"])

    elif action == "ps":
        _run_compose(["ps"])

    elif action == "logs":
        compose_args = ["logs", "--tail", "50"]
        if profile:
            compose_args.append(profile)
        _run_compose(compose_args)

    elif action == "restart":
        compose_args = ["restart"]
        if profile:
            compose_args.append(profile)
        rprint("[bold]Restarting MCP stack...[/bold]")
        if _run_compose(compose_args):
            rprint("[green]v MCP stack restarted[/green]")

    else:
        rprint(f"[red]Unknown action: {action}. Use: up, down, status, ps, logs, restart[/red]")
