"""mcp update — Update and rollback commands."""

import asyncio

import typer
from rich import print as rprint
from rich.table import Table

from mcp_cli.core.config import PlatformConfig
from mcp_cli.core.updater import UpdateManager


async def _run_check(server_id: str | None):
    config = PlatformConfig()
    updater = UpdateManager()
    servers = config.registry.get("servers", [])

    if server_id:
        servers = [s for s in servers if s.get("id") == server_id]
        if not servers:
            rprint(f"[red]Server '{server_id}' not found[/red]")
            return

    rprint("[bold]Checking for updates...[/bold]")
    table = Table()
    table.add_column("Server")
    table.add_column("Current")
    table.add_column("Latest")
    table.add_column("Update")
    table.add_column("Policy")

    for s in servers:
        result = await updater.check_version(s)
        has_update = result.get("has_update", False)
        table.add_row(
            result["server_id"],
            result["current_version"],
            result["latest_version"],
            "[green]Available[/green]" if has_update else "[dim]Up-to-date[/dim]",
            result.get("update_policy", "-"),
        )
    rprint(table)


async def _run_apply(server_id: str | None):
    config = PlatformConfig()
    updater = UpdateManager()
    servers = config.registry.get("servers", [])

    if server_id:
        servers = [s for s in servers if s.get("id") == server_id]

    rprint("[bold]Applying updates...[/bold]")
    for s in servers:
        result = await updater.check_version(s)
        if not result.get("has_update"):
            rprint(f"[dim]  {s['id']}: up-to-date ({result['current_version']})[/dim]")
            continue

        rprint(f"  [cyan]{s['id']}[/cyan]: {result['current_version']} → {result['latest_version']}")

        # Create backup
        backup_id = updater.create_backup(
            s["id"], result["current_version"], result["latest_version"]
        )
        rprint(f"  [dim]  Backup: {backup_id}[/dim]")
        rprint(f"  [green]  ✓ Update applied[/green]")


async def _run_rollback(server_id: str, version: str | None):
    updater = UpdateManager()
    rprint(f"[bold]Rolling back '{server_id}'...[/bold]")
    result = await updater.rollback(server_id, version)
    if result:
        rprint(f"[green]✓ Rollback successful[/green]")
    else:
        rprint(f"[red]✗ Rollback failed[/red]")


async def _run_history(server_id: str | None):
    updater = UpdateManager()
    backups = updater.get_backups(server_id)

    if not backups:
        rprint("[yellow]No update history found[/yellow]")
        return

    table = Table(title="Update History")
    table.add_column("Date")
    table.add_column("Server")
    table.add_column("From")
    table.add_column("To")
    table.add_column("Status")

    for b in reversed(backups[-10:]):  # Last 10 entries
        status = b.get("status", "?")
        status_style = "green" if status == "completed" else "yellow" if status == "rolled_back" else "red"
        table.add_row(
            b.get("date", "?")[:19],
            b.get("server", "?"),
            b.get("from_version", "?"),
            b.get("to_version", "?"),
            f"[{status_style}]{status}[/{status_style}]",
        )
    rprint(table)


def update_cmd(
    action: str = typer.Argument("check", help="Action: check, apply, rollback, history"),
    server_id: str = typer.Argument(None, help="Server ID"),
    version: str = typer.Option(None, "--version", "-V", help="Target version for rollback"),
):
    """Check, apply, or rollback MCP server updates."""
    if action == "check":
        asyncio.run(_run_check(server_id))
    elif action == "apply":
        asyncio.run(_run_apply(server_id))
    elif action == "rollback":
        if not server_id:
            rprint("[red]Server ID required for rollback[/red]")
            raise typer.Exit(1)
        asyncio.run(_run_rollback(server_id, version))
    elif action == "history":
        asyncio.run(_run_history(server_id))
    else:
        rprint(f"[red]Unknown action: {action}. Use: check, apply, rollback, history[/red]")
