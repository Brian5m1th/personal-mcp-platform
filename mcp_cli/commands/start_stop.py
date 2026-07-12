"""mcp start/stop/restart/status/emergency — Server lifecycle commands."""

import asyncio

import typer
from rich import print as rprint
from rich.table import Table

from mcp_cli.core.server_manager import ServerManager


async def _run_start(server_id: str | None, profile: str | None):
    mgr = ServerManager()
    if profile:
        from mcp_cli.core.config import save_yaml, get_active_profile_path
        import time
        save_yaml(get_active_profile_path(), {
            "active_profiles": [profile],
            "set_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": "cli",
        })
        rprint(f"[dim]Profile set to: {profile}[/dim]")

    if server_id:
        result = await mgr.start_one(server_id)
        if result:
            rprint(f"[green]✓ Started '{server_id}'[/green]")
        else:
            rprint(f"[red]✗ Failed to start '{server_id}'[/red]")
    else:
        count = await mgr.start_all()
        rprint(f"[green]✓ Started {count} server(s)[/green]")

    statuses = mgr.get_status_all()
    _display_status(statuses)


async def _run_stop(server_id: str | None):
    mgr = ServerManager()
    if server_id:
        result = await mgr.stop_one(server_id)
        if result:
            rprint(f"[green]✓ Stopped '{server_id}'[/green]")
        else:
            rprint(f"[red]✗ Server '{server_id}' not running[/red]")
    else:
        count = await mgr.stop_all()
        rprint(f"[green]✓ Stopped {count} server(s)[/green]")


async def _run_restart(server_id: str):
    mgr = ServerManager()
    result = await mgr.restart_one(server_id)
    if result:
        rprint(f"[green]✓ Restarted '{server_id}'[/green]")
    else:
        rprint(f"[red]✗ Failed to restart '{server_id}'[/red]")


async def _run_status():
    mgr = ServerManager()
    statuses = mgr.get_status_all()
    if not statuses:
        rprint("[yellow]No servers running. Use 'mcp start' to start servers.[/yellow]")
        return
    _display_status(statuses)


def _display_status(statuses: list[dict]):
    if not statuses:
        return
    table = Table(title="MCP Server Status")
    table.add_column("Server", style="cyan")
    table.add_column("State", style="bold")
    table.add_column("Tools", justify="right")
    table.add_column("Health")
    table.add_column("Latency")

    for s in statuses:
        health = s.get("health", {})
        state = s.get("state", "unknown")
        state_style = {
            "healthy": "green",
            "running": "green",
            "degraded": "yellow",
            "failed": "red",
            "stopped": "dim",
        }.get(state, "white")
        health_str = health.get("status", "?")
        health_style = "green" if health_str == "healthy" else "red"
        table.add_row(
            s.get("id", "?"),
            f"[{state_style}]{state}[/{state_style}]",
            str(s.get("tools_count", 0)),
            f"[{health_style}]{health_str}[/{health_style}]",
            f"{health.get('latency_ms', 0)}ms",
        )
    rprint(table)


async def _run_emergency_stop():
    mgr = ServerManager()
    rprint("[bold red]EMERGENCY STOP — Stopping all servers...[/bold red]")
    await mgr.emergency_stop()
    rprint("[green]All servers stopped.[/green]")


def start_cmd(
    server_id: str = typer.Argument(None, help="Server ID to start (omit for all)"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to activate"),
):
    """Start MCP server(s)."""
    asyncio.run(_run_start(server_id, profile))


def stop_cmd(
    server_id: str = typer.Argument(None, help="Server ID to stop (omit for all)"),
):
    """Stop MCP server(s)."""
    asyncio.run(_run_stop(server_id))


def restart_cmd(
    server_id: str = typer.Argument(..., help="Server ID to restart"),
):
    """Restart a single MCP server."""
    asyncio.run(_run_restart(server_id))


def status_cmd():
    """Show status of all MCP servers."""
    asyncio.run(_run_status())


def emergency_stop_cmd(
    action: str = typer.Argument("stop", help="Action: stop"),
):
    """Emergency stop all MCP servers."""
    if action == "stop":
        asyncio.run(_run_emergency_stop())
    else:
        rprint(f"[red]Unknown action: {action}")
