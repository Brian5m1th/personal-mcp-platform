"""mcp profile — Profile management commands."""

import typer
from rich import print as rprint
from rich.table import Table

from mcp_cli.core.profiles import ProfileManager


def profile_cmd(
    action: str = typer.Argument("list", help="Action: list, set, current, show"),
    name: str = typer.Argument(None, help="Profile name (for set/show)"),
):
    """Manage MCP engineering profiles."""
    mgr = ProfileManager()
    mgr.initialize_builtins()

    if action == "list":
        profiles = mgr.list_profiles()
        if not profiles:
            rprint("[yellow]No profiles found[/yellow]")
            return

        table = Table(title="MCP Engineering Profiles")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Servers", justify="right")
        table.add_column("Description")

        for p in profiles:
            table.add_row(p["id"], p["name"], str(p["server_count"]), p.get("description", ""))
        rprint(table)

    elif action == "set":
        if not name:
            rprint("[red]Profile name required[/red]")
            return
        if mgr.set_active(name):
            info = mgr.get_profile_info(name)
            if info:
                rprint(f"[green]Active profile: [bold]{name}[/bold][/green]")
                rprint(f"  Servers: {', '.join(info.get('enabled_servers', []))}")

    elif action == "current":
        active = mgr.get_active()
        rprint(f"[bold]Active profile(s):[/bold] {', '.join(active)}")
        for a in active:
            info = mgr.get_profile_info(a)
            if info:
                rprint(f"  [dim]{info.get('description', '')}[/dim]")
                rprint(f"  Enabled servers: {', '.join(info.get('enabled_servers', []))}")

    elif action == "show":
        if not name:
            rprint("[red]Profile name required[/red]")
            return
        info = mgr.get_profile_info(name)
        if info is None:
            rprint(f"[red]Profile '{name}' not found[/red]")
            return
        rprint(f"[bold]Profile: [cyan]{name}[/cyan][/bold]")
        rprint(f"  Name: {info.get('name', name)}")
        rprint(f"  Description: {info.get('description', '')}")
        rprint(f"  Enabled servers ({len(info.get('enabled_servers', []))}):")
        for s in info.get("enabled_servers", []):
            rprint(f"    • {s}")
        if info.get("disabled_servers"):
            rprint(f"  Disabled servers:")
            for s in info["disabled_servers"]:
                rprint(f"    • {s}")

    else:
        rprint(f"[red]Unknown action: {action}. Use: list, set, current, show[/red]")
