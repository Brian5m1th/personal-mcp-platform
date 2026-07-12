"""mcp registry — Registry query commands."""

import typer
from rich import print as rprint
from rich.table import Table

from mcp_cli.core.config import PlatformConfig


def registry_cmd(
    action: str = typer.Argument("list", help="Action: list, search, info"),
    query: str = typer.Argument(None, help="Search query or server ID"),
):
    """Query the MCP server registry."""
    config = PlatformConfig()
    servers = config.registry.get("servers", [])

    if action == "list":
        if not servers:
            rprint("[yellow]Registry is empty[/yellow]")
            return

        # Group by category
        from collections import defaultdict
        by_category = defaultdict(list)
        for s in servers:
            cat = s.get("category", "uncategorized")
            by_category[cat].append(s)

        for cat, cat_servers in sorted(by_category.items()):
            table = Table(title=f"[bold]{cat.upper()}[/bold]")
            table.add_column("ID", style="cyan")
            table.add_column("Name")
            table.add_column("Version")
            table.add_column("Maturity")
            table.add_column("Risk")

            for s in sorted(cat_servers, key=lambda x: x.get("id", "")):
                risks = s.get("permissions", {}).get("risks", [])
                max_risk = max((r.get("level", "low") for r in risks), default="none") if risks else "none"
                risk_style = {
                    "none": "dim", "low": "green", "medium": "yellow",
                    "high": "red", "critical": "bold red",
                }.get(max_risk, "white")

                # Only show Tier 1 (no plan field) and Tier 2 (plan: phase-2) if marked
                plan = s.get("plan", "")
                if plan:
                    plan_str = f"[dim]({plan})[/dim]"
                else:
                    plan_str = ""

                table.add_row(
                    s.get("id", "?"),
                    f"{s.get('name', '?')} {plan_str}",
                    s.get("version", "?"),
                    s.get("maturity", "?"),
                    f"[{risk_style}]{max_risk}[/{risk_style}]",
                )
            rprint(table)
            rprint("")

    elif action == "search":
        if not query:
            rprint("[yellow]Search query required[/yellow]")
            return

        q = query.lower()
        results = [
            s for s in servers
            if q in s.get("id", "").lower()
            or q in s.get("name", "").lower()
            or q in s.get("description", "").lower()
            or q in s.get("category", "").lower()
            or q in s.get("tags", [])
        ]

        if not results:
            rprint(f"[yellow]No servers matching '{query}'[/yellow]")
            return

        rprint(f"[bold]Found {len(results)} server(s) matching '[cyan]{query}[/cyan]':[/bold]")
        for s in results:
            risk = s.get("permissions", {}).get("risks", [{}])[0].get("level", "?")
            rprint(f"  [cyan]{s['id']}[/cyan] — {s.get('name', '?')} [dim]({s.get('category', '?')}, risk: {risk})[/dim]")

    elif action == "info":
        if not query:
            rprint("[yellow]Server ID required[/yellow]")
            return

        s = config.get_server(query)
        if s is None:
            rprint(f"[red]Server '{query}' not found[/red]")
            return

        rprint(f"[bold]Server: [cyan]{s.get('id')}[/cyan][/bold]")
        rprint(f"  Name: {s.get('name')}")
        rprint(f"  Version: {s.get('version')}")
        rprint(f"  Category: {s.get('category')}")
        rprint(f"  Maturity: {s.get('maturity')}")
        rprint(f"  License: {s.get('license')}")
        rprint(f"  Description: {s.get('description')}")

        # Permissions
        perms = s.get("permissions", {})
        rprint(f"  [bold]Permissions:[/bold]")
        rprint(f"    Filesystem: {perms.get('filesystem', '?')}")
        rprint(f"    Network: {perms.get('network', '?')}")
        rprint(f"    Shell: {perms.get('shell', '?')}")
        risks = perms.get("risks", [])
        if risks:
            rprint(f"    Risks:")
            for r in risks:
                rprint(f"      • [{r.get('level')}] {r.get('description')}")

        # Install
        install = s.get("install", {})
        rprint(f"  [bold]Install:[/bold]")
        rprint(f"    Method: {install.get('method')}")
        rprint(f"    Command: {install.get('command')}")
        rprint(f"    Auto-update: {install.get('auto_update', False)}")

        # Compatibility
        rprint(f"  [bold]Compatibility:[/bold]")
        rprint(f"    Agents: {', '.join(s.get('agents', []))}")
        rprint(f"    Platforms: {', '.join(s.get('platforms', []))}")
        rprint(f"    Tags: {', '.join(s.get('tags', []))}")

    else:
        rprint(f"[red]Unknown action: {action}. Use: list, search, info[/red]")
