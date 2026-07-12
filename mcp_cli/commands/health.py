"""mcp health — Health monitoring commands."""

import asyncio

import typer
from rich import print as rprint
from rich.table import Table

from mcp_cli.core.health import HealthMonitor


def health_cmd(
    action: str = typer.Argument("check", help="Action: check, metrics, summary"),
    server_id: str = typer.Option(None, "--server", "-s", help="Server ID filter"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of metrics to show"),
):
    """Check MCP server health and view metrics."""
    monitor = HealthMonitor()

    if action == "check":
        from mcp_cli.core.server_manager import ServerManager
        statuses = asyncio.run(_run_health_check())
        if not statuses:
            rprint("[yellow]No servers running[/yellow]")
            return

        table = Table(title="MCP Server Health")
        table.add_column("Server", style="cyan")
        table.add_column("Status")
        table.add_column("Latency")
        table.add_column("Tools")

        for s in statuses:
            status = s.get("status", "?")
            style = "green" if status == "healthy" else "yellow" if status == "degraded" else "red"
            table.add_row(
                s.get("id", "?"),
                f"[{style}]{status}[/{style}]",
                f"{s.get('latency_ms', 0)}ms",
                str(s.get("tools_count", 0)),
            )
        rprint(table)

    elif action == "metrics":
        metrics = monitor.get_recent_metrics(server_id, limit)
        if not metrics:
            rprint("[yellow]No metrics available[/yellow]")
            return

        table = Table(title="Health Metrics")
        table.add_column("Timestamp")
        table.add_column("Server")
        table.add_column("Status")
        table.add_column("Latency")
        table.add_column("Error")

        for m in metrics:
            status = m.get("status", "?")
            style = "green" if status == "healthy" else "red"
            table.add_row(
                m.get("timestamp", "?")[:19],
                m.get("server_id", "?"),
                f"[{style}]{status}[/{style}]",
                f"{m.get('latency_ms', 0)}ms",
                m.get("error", "") or "-",
            )
        rprint(table)

    elif action == "summary":
        if server_id:
            summaries = [monitor.get_summary(server_id)]
        else:
            summaries = monitor.get_all_summaries()

        if not summaries:
            rprint("[yellow]No health data available[/yellow]")
            return

        table = Table(title="Health Summary")
        table.add_column("Server")
        table.add_column("Status")
        table.add_column("Avg Latency")
        table.add_column("Uptime")
        table.add_column("Samples")

        for s in summaries:
            status = s.get("status", "?")
            style = "green" if status == "healthy" else "yellow" if status == "degraded" else "red"
            table.add_row(
                s.get("server_id", "?"),
                f"[{style}]{status}[/{style}]",
                f"{s.get('avg_latency_ms', 0):.0f}ms",
                f"{s.get('uptime', 0)*100:.0f}%",
                str(s.get("samples", 0)),
            )
        rprint(table)

    else:
        rprint(f"[red]Unknown action: {action}. Use: check, metrics, summary[/red]")


async def _run_health_check() -> list[dict]:
    from mcp_cli.core.server_manager import ServerManager
    mgr = ServerManager()
    results = await mgr.health_check_all()
    statuses = mgr.get_status_all()
    # Merge health data
    for s in statuses:
        health = s.get("health", {})
        s["status"] = health.get("status", "?")
        s["latency_ms"] = health.get("latency_ms", 0)
    return statuses
