"""mcp discover — Search for MCP servers from internet sources."""

import asyncio

import typer
from rich import print as rprint
from rich.table import Table

from mcp_cli.core.discovery import DiscoveryEngine, asdict


async def _run_search(query: str, sources: list[str] | None, limit: int):
    engine = DiscoveryEngine()
    rprint(f"[bold]Searching {sources or 'all sources'} for '[cyan]{query}[/cyan]'...[/bold]")
    results = await engine.search(query, sources)

    if not results:
        rprint("[yellow]No MCP servers found matching your query[/yellow]")
        return

    results = results[:limit]
    table = Table(title=f"Discovered MCP Servers ({len(results)} found)")
    table.add_column("Server", style="cyan")
    table.add_column("Source")
    table.add_column("Install")
    table.add_column("Confidence")
    table.add_column("Description")

    for s in results:
        conf_pct = f"{s.confidence * 100:.0f}%"
        conf_style = "green" if s.confidence >= 0.8 else "yellow" if s.confidence >= 0.5 else "dim"
        table.add_row(
            s.name,
            s.source,
            s.install_method,
            f"[{conf_style}]{conf_pct}[/{conf_style}]",
            s.description[:80] + ("..." if len(s.description) > 80 else ""),
        )
    rprint(table)
    rprint(f"\n[dim]Run [bold]mcp registry import <id>[/bold] to add a server to your registry[/dim]")


async def _run_list():
    engine = DiscoveryEngine()
    results = engine.get_cached_results()
    age_hours = engine.get_cache_age_hours()

    if not results:
        rprint("[yellow]No cached discovery results. Run 'mcp discover search <query>' first.[/yellow]")
        return

    age_str = f"{age_hours:.1f}h" if age_hours >= 0 else "unknown"
    table = Table(title=f"Cached Discovery Results ({len(results)} servers, age: {age_str})")
    table.add_column("Server", style="cyan")
    table.add_column("Source")
    table.add_column("Install")
    table.add_column("Confidence")
    table.add_column("Package")

    for s in results:
        conf = s.get("confidence", 0)
        conf_pct = f"{conf * 100:.0f}%"
        conf_style = "green" if conf >= 0.8 else "yellow" if conf >= 0.5 else "dim"
        table.add_row(
            s.get("name", "?"),
            s.get("source", "?"),
            s.get("install_method", "?"),
            f"[{conf_style}]{conf_pct}[/{conf_style}]",
            s.get("package", ""),
        )
    rprint(table)


async def _run_sources():
    sources = [
        ("npm", "npm registry", "Packages with 'mcp-server' keyword"),
        ("github", "GitHub API", "Repositories with 'mcp-server' topic"),
        ("pypi", "PyPI", "Python packages (requires beautifulsoup4)"),
        ("smithery", "Smithery.ai", "MCP server directory"),
        ("awesome", "Awesome Lists", "Curated MCP server lists on GitHub"),
    ]
    table = Table(title="Discovery Sources")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Description")
    for sid, name, desc in sources:
        table.add_row(sid, name, desc)
    rprint(table)


async def _run_clear():
    engine = DiscoveryEngine()
    engine.clear_cache()
    rprint("[green]v Discovery cache cleared[/green]")


def discover_cmd(
    action: str = typer.Argument("search", help="Action: search, list, sources, clear"),
    query: str = typer.Argument("", help="Search query"),
    source: list[str] = typer.Option(None, "--source", "-s", help="Filter by source (npm, github, pypi, smithery, awesome)"),
    limit: int = typer.Option(30, "--limit", "-l", help="Max results to show"),
):
    """Search for MCP servers from internet sources."""
    if action == "search":
        if not query:
            rprint("[yellow]Search query required. Usage: mcp discover search <query>[/yellow]")
            return
        asyncio.run(_run_search(query, source, limit))
    elif action == "list":
        asyncio.run(_run_list())
    elif action == "sources":
        asyncio.run(_run_sources())
    elif action == "clear":
        asyncio.run(_run_clear())
    else:
        rprint(f"[red]Unknown action: {action}. Use: search, list, sources, clear[/red]")
