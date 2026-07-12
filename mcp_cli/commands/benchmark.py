"""mcp benchmark — Benchmark MCP server performance."""

import asyncio
import time

import typer
from rich import print as rprint
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from mcp_cli.core.config import PlatformConfig
from mcp_cli.core.server_manager import ManagedServer


async def _benchmark_server(server_entry: dict) -> dict:
    """Run benchmarks on a single MCP server."""
    server_id = server_entry.get("id", "unknown")
    result = {
        "server_id": server_id,
        "startup_ms": 0,
        "tools_list_ms": 0,
        "latency_ms": 0,
        "tool_count": 0,
        "error": None,
    }

    server = ManagedServer(server_id, server_entry)

    # Measure startup time
    t0 = time.monotonic()
    success = await server.initialize()
    startup_ms = (time.monotonic() - t0) * 1000
    result["startup_ms"] = round(startup_ms, 1)

    if not success:
        result["error"] = "Failed to start"
        return result

    # Measure tools/list
    t0 = time.monotonic()
    tools = server.get_tools()
    tools_list_ms = (time.monotonic() - t0) * 1000
    result["tools_list_ms"] = round(tools_list_ms, 1)
    result["tool_count"] = len(tools)

    # Measure latency (send a health check)
    t0 = time.monotonic()
    health = await server.health_check()
    latency_ms = (time.monotonic() - t0) * 1000
    result["latency_ms"] = round(latency_ms, 1)

    # Cleanup
    await server.shutdown()

    return result


async def _run_benchmark(server_id: str | None):
    config = PlatformConfig()
    servers = config.registry.get("servers", [])

    if server_id:
        servers = [s for s in servers if s.get("id") == server_id]
        if not servers:
            rprint(f"[red]Server '{server_id}' not found[/red]")
            return

    rprint(f"[bold]Benchmarking {len(servers)} server(s)...[/bold]")

    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        for s in servers:
            task = progress.add_task(f"  Testing {s['id']}...", total=None)
            result = await _benchmark_server(s)
            progress.update(task, completed=True)
            results.append(result)

    # Display results
    table = Table(title="Benchmark Results")
    table.add_column("Server", style="cyan")
    table.add_column("Startup", justify="right")
    table.add_column("tools/list", justify="right")
    table.add_column("Latency", justify="right")
    table.add_column("Tools", justify="right")
    table.add_column("Status")

    for r in results:
        if r.get("error"):
            table.add_row(r["server_id"], "—", "—", "—", "—", f"[red]{r['error']}[/red]")
        else:
            table.add_row(
                r["server_id"],
                f"{r['startup_ms']:.0f}ms",
                f"{r['tools_list_ms']:.0f}ms",
                f"{r['latency_ms']:.0f}ms",
                str(r["tool_count"]),
                "[green]OK[/green]",
            )
    rprint(table)

    # Summary stats
    if results:
        avg_startup = sum(r.get("startup_ms", 0) for r in results if not r.get("error")) / max(
            sum(1 for r in results if not r.get("error")), 1
        )
        rprint(f"\n[dim]Average startup: {avg_startup:.0f}ms[/dim]")


def benchmark_cmd(
    server_id: str = typer.Argument(None, help="Server ID to benchmark (omit for all)"),
):
    """Benchmark MCP server performance metrics."""
    asyncio.run(_run_benchmark(server_id))
