"""mcp registry — Registry query, sync, and import commands."""

import asyncio
from datetime import datetime

import typer
from rich import print as rprint
from rich.table import Table

from mcp_cli.core.config import PlatformConfig, get_registry_path, load_yaml, save_yaml
from mcp_cli.core.discovery import DiscoveryEngine


def _server_age_days(registry: dict) -> int:
    updated = registry.get("updated", "")
    if not updated:
        return -1
    try:
        dt = datetime.fromisoformat(updated)
        return (datetime.utcnow() - dt).days
    except Exception:
        return -1


def registry_cmd(
    action: str = typer.Argument("list", help="Action: list, search, info, sync, import"),
    query: str = typer.Argument(None, help="Search query or server ID"),
):
    """Query, sync, and manage the MCP server registry."""
    config = PlatformConfig()
    servers = config.registry.get("servers", [])

    if action == "list":
        age_days = _server_age_days(config.registry)
        if age_days > 30:
            rprint(f"[yellow]Registry data is {age_days} days old. Run 'mcp registry sync' to refresh.[/yellow]\n")

        if not servers:
            rprint("[yellow]Registry is empty[/yellow]")
            return

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

        install = s.get("install", {})
        rprint(f"  [bold]Install:[/bold]")
        rprint(f"    Method: {install.get('method')}")
        rprint(f"    Command: {install.get('command')}")
        rprint(f"    Auto-update: {install.get('auto_update', False)}")

        rprint(f"  [bold]Compatibility:[/bold]")
        rprint(f"    Agents: {', '.join(s.get('agents', []))}")
        rprint(f"    Platforms: {', '.join(s.get('platforms', []))}")
        rprint(f"    Tags: {', '.join(s.get('tags', []))}")

    elif action == "sync":
        asyncio.run(_run_sync())

    elif action == "import":
        if not query:
            rprint("[yellow]Server ID required. Usage: mcp registry import <server-id>[/yellow]")
            return
        asyncio.run(_run_import(query))

    else:
        rprint(f"[red]Unknown action: {action}. Use: list, search, info, sync, import[/red]")


async def _run_sync():
    rprint("[bold]Syncing registry with internet sources...[/bold]")
    engine = DiscoveryEngine()
    discovered = await engine.search()

    if not discovered:
        rprint("[yellow]No servers discovered from internet sources[/yellow]")
        return

    registry_path = get_registry_path()
    registry = load_yaml(registry_path)
    existing = {s.get("id"): s for s in registry.get("servers", [])}

    added = 0
    updated = 0

    for server in discovered:
        sid = server.id
        entry = {
            "id": sid,
            "name": server.name,
            "description": server.description[:200],
            "version": server.version,
            "source": server.source,
            "install": {
                "method": server.install_method,
                "command": f"{server.install_method} {server.package}",
                "auto_update": True,
                "update_policy": "minor",
            },
            "plan": "discovered",
            "maturity": "unknown",
        }

        if sid in existing:
            old_version = existing[sid].get("version", "")
            if server.version != "0.0.0" and server.version != old_version:
                existing[sid]["version"] = server.version
                existing[sid]["source"] = server.source
                existing[sid]["updated"] = datetime.utcnow().isoformat()
                updated += 1
        else:
            existing[sid] = entry
            added += 1

    registry["servers"] = list(existing.values())
    registry["updated"] = datetime.utcnow().strftime("%Y-%m-%d")
    registry["auto_sync"] = registry.get("auto_sync", {})
    registry["auto_sync"]["last_sync"] = datetime.utcnow().isoformat()
    registry["auto_sync"]["servers_found"] = len(discovered)

    save_yaml(registry_path, registry)
    rprint(f"[green]v Sync complete: {added} added, {updated} updated, {len(existing)} total[/green]")


async def _run_import(server_id: str):
    engine = DiscoveryEngine()
    cached = engine.get_cached_results()

    match = None
    for s in cached:
        if s.get("id") == server_id or s.get("name") == server_id or s.get("package") == server_id:
            match = s
            break

    if not match:
        rprint(f"[yellow]Server '{server_id}' not found in cache. Run 'mcp discover search {server_id}' first.[/yellow]")
        return

    registry_path = get_registry_path()
    registry = load_yaml(registry_path)
    existing_ids = [s.get("id") for s in registry.get("servers", [])]

    sid = match.get("id", server_id)
    if sid in existing_ids:
        rprint(f"[yellow]Server '{sid}' already exists in registry[/yellow]")
        return

    entry = {
        "id": sid,
        "name": match.get("name", sid),
        "description": match.get("description", "")[:200],
        "version": match.get("version", "0.0.0"),
        "source": match.get("source", "discovered"),
        "install": {
            "method": match.get("install_method", "npx"),
            "command": f"{match.get('install_method', 'npx')} {match.get('package', sid)}",
            "auto_update": True,
            "update_policy": "minor",
        },
        "plan": "imported",
        "maturity": "unknown",
        "tags": match.get("tags", []),
        "imported_at": datetime.utcnow().isoformat(),
    }

    servers = registry.get("servers", [])
    servers.append(entry)
    registry["servers"] = servers
    registry["updated"] = datetime.utcnow().strftime("%Y-%m-%d")
    save_yaml(registry_path, registry)

    rprint(f"[green]v Imported '{sid}' into registry[/green]")
    rprint(f"  Name: {entry['name']}")
    rprint(f"  Install: {entry['install']['command']}")
    rprint(f"  Source: {entry['source']}")
