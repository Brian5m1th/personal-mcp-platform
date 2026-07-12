"""mcp project — Link/unlink MCP platform to/from a project."""

import json
from pathlib import Path

import typer
from rich import print as rprint

from mcp_cli.core.generator import AgentConfigGenerator


def _get_project_root() -> Path:
    """Detect project root (current directory or parent with .git)."""
    cwd = Path.cwd()
    # Check for .git in current or parent directories
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").exists() or (parent / ".git").is_dir():
            return parent
    return cwd


def _get_project_name(project_root: Path) -> str:
    """Get project name from dir name or package files."""
    name = project_root.name

    # Try package.json
    pkg = project_root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            return data.get("name", name)
        except Exception:
            pass

    # Try pyproject.toml
    pyproj = project_root / "pyproject.toml"
    if pyproj.exists():
        for line in pyproj.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("name ="):
                return line.split("=")[1].strip().strip('"').strip("'")

    # Try Cargo.toml
    cargo = project_root / "Cargo.toml"
    if cargo.exists():
        for line in cargo.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("name ="):
                return line.split("=")[1].strip().strip('"').strip("'")

    return name


def _generate_project_env(project_root: Path) -> dict:
    """Generate environment variable overrides for a project."""
    return {
        "MCP_PROJECT": project_root.name,
        "MCP_WORKSPACE": str(project_root),
    }


def _generate_project_config(agent: str, project_root: Path) -> dict:
    """Generate agent-specific MCP config for a project."""
    gen = AgentConfigGenerator()
    servers = gen._get_servers_for_agent()
    config = {"mcpServers": {}}
    for s in servers:
        env = {}
        for key, val in s.get("env", {}).items():
            env[key] = val
        config["mcpServers"][s["id"]] = {
            "command": s["command"],
            "args": s["args"],
            "env": env,
        }
    return config


def project_cmd(
    action: str = typer.Argument("status", help="Action: add, remove, status, list"),
    agent: str = typer.Option("opencode", "--agent", "-a", help="Agent to configure (opencode, claude-code, cursor, vscode, antigravity)"),
    path: str = typer.Option(None, "--path", "-p", help="Project path (default: current directory)"),
    profile: str = typer.Option(None, "--profile", help="Profile to use for this project"),
):
    """Link or unlink the MCP platform to/from a project.

    Use 'mcp project add' in your project directory to enable MCP there.
    Use 'mcp project remove' to disable it.
    Use 'mcp project list' to see all projects with MCP enabled.
    """
    from mcp_cli.core.config import get_mcp_home, load_yaml, save_yaml
    import yaml

    projects_file = get_mcp_home() / "projects.yaml"
    projects = load_yaml(projects_file)
    if "projects" not in projects:
        projects["projects"] = {}

    project_root = Path(path).resolve() if path else _get_project_root()
    project_name = _get_project_name(project_root)

    if action == "add":
        # Create project config files
        config = _generate_project_config(agent, project_root)
        env = _generate_project_env(project_root)

        if agent == "opencode":
            config_path = project_root / ".opencode.json"
            # Merge with existing .opencode.json (preserve $schema, plugin, etc.)
            existing = {}
            if config_path.exists():
                try:
                    existing = json.loads(config_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            merged = dict(existing)
            merged.pop("mcpServers", None)  # Remove old servers
            merged["mcpServers"] = config["mcpServers"]
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)

        elif agent == "claude-code":
            config_path = project_root / ".claude.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        elif agent == "cursor":
            cursor_dir = project_root / ".cursor"
            cursor_dir.mkdir(parents=True, exist_ok=True)
            config_path = cursor_dir / "mcp.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        elif agent == "vscode":
            vscode_dir = project_root / ".vscode"
            vscode_dir.mkdir(parents=True, exist_ok=True)
            config_path = vscode_dir / "settings.json"
            # Merge with existing settings if any
            existing = {}
            if config_path.exists():
                try:
                    existing = json.loads(config_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            existing["mcp"] = {"servers": config["mcpServers"]}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
        else:
            rprint(f"[red]Unknown agent: {agent}. Use: opencode, claude-code, cursor, vscode[/red]")
            raise typer.Exit(1)

        # Register in projects registry
        projects["projects"][project_name] = {
            "path": str(project_root),
            "agent": agent,
            "config_file": str(config_path),
            "profile": profile or "full-stack",
            "env": env,
        }
        save_yaml(projects_file, projects)

        rprint(f"[green]v MCP linked to project [bold]{project_name}[/bold][/green]")
        rprint(f"  Config: {config_path}")
        rprint(f"  Agent: {agent}")
        rprint(f"  Profile: {profile or 'full-stack'}")
        rprint(f"\n  [dim]Run [bold]mcp start[/bold] to start the servers.[/dim]")

    elif action == "remove":
        if project_name in projects["projects"]:
            entry = projects["projects"][project_name]
            config_path = Path(entry["config_file"])
            if config_path.exists():
                config_path.unlink()
                rprint(f"[yellow]Removed: {config_path}[/yellow]")
            del projects["projects"][project_name]
            save_yaml(projects_file, projects)
            rprint(f"[yellow]v MCP unlinked from [bold]{project_name}[/bold][/yellow]")
        else:
            rprint(f"[yellow]Project '{project_name}' is not linked to MCP.[/yellow]")

    elif action == "status":
        if project_name in projects["projects"]:
            entry = projects["projects"][project_name]
            rprint(f"[bold]MCP Status for [cyan]{project_name}[/cyan][/bold]")
            rprint(f"  Path: {entry['path']}")
            rprint(f"  Agent: {entry['agent']}")
            rprint(f"  Config: {entry['config_file']}")
            rprint(f"  Profile: {entry.get('profile', 'full-stack')}")
            config_path = Path(entry["config_file"])
            if config_path.exists():
                rprint(f"  [green]v Config file exists[/green]")
            else:
                rprint(f"  [red]x Config file missing[/red]")
        else:
            rprint(f"[yellow]Project '{project_name}' is not linked to MCP.[/yellow]")
            rprint(f"  Run [bold]mcp project add[/bold] in the project directory to link it.")

    elif action == "list":
        if not projects["projects"]:
            rprint("[yellow]No projects linked to MCP.[/yellow]")
            rprint(f"  Run [bold]mcp project add[/bold] in a project directory to link it.")
            return

        from rich.table import Table
        table = Table(title="Projects with MCP Enabled")
        table.add_column("Project", style="cyan")
        table.add_column("Path")
        table.add_column("Agent")
        table.add_column("Profile")
        table.add_column("Config")

        for name, entry in sorted(projects["projects"].items()):
            config_path = Path(entry["config_file"])
            status = "[green]v[/green]" if config_path.exists() else "[red]x[/red]"
            table.add_row(
                name,
                entry["path"],
                entry.get("agent", "?"),
                entry.get("profile", "full-stack"),
                status,
            )
        rprint(table)

    else:
        rprint(f"[red]Unknown action: {action}. Use: add, remove, status, list[/red]")
