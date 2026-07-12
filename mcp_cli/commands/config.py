"""mcp config — Configuration commands."""

import os
from pathlib import Path

import typer
from rich import print as rprint

from mcp_cli.core.config import get_mcp_home, get_config_path, get_registry_path


def config_cmd(
    action: str = typer.Argument("show", help="Action: show, path, edit"),
):
    """View and edit MCP platform configuration."""
    home = get_mcp_home()
    config_path = get_config_path()
    registry_path = get_registry_path()

    if action == "show":
        rprint(f"[bold]MCP Platform Configuration[/bold]")
        rprint(f"  [cyan]MCP_HOME:[/cyan] {home}")
        rprint(f"  [cyan]Config:[/cyan] {config_path}")
        rprint(f"  [cyan]Registry:[/cyan] {registry_path}")
        rprint(f"  [cyan]Profiles:[/cyan] {home / 'profiles'}")
        rprint(f"  [cyan]Servers:[/cyan] {home / 'servers'}")
        rprint(f"  [cyan]Secrets:[/cyan] {home / 'secrets'}")
        rprint(f"  [cyan]Cache:[/cyan] {home / 'cache'}")

        # Check if files exist
        rprint(f"\n[bold]File Status:[/bold]")
        rprint(f"  Config: {'[green]exists[/green]' if config_path.exists() else '[yellow]not found[/yellow]'}")
        rprint(f"  Registry: {'[green]exists[/green]' if registry_path.exists() else '[yellow]not found[/yellow]'}")

    elif action == "path":
        rprint(home)

    elif action == "edit":
        if config_path.exists():
            rprint(f"Edit: {config_path}")
            # Try to open in default editor
            editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "notepad" if os.name == "nt" else "nano"))
            os.system(f"{editor} {config_path}")
        else:
            rprint(f"[yellow]Config file not found at {config_path}[/yellow]")
            rprint("Create one with defaults by running: [bold]mcp registry list[/bold]")

    else:
        rprint(f"[red]Unknown action: {action}. Use: show, path, edit[/red]")
