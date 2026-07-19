"""MCP Platform CLI entry point."""

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from mcp_cli import __version__

app = typer.Typer(
    name="mcp",
    help="Personal AI Engineering Platform — Universal MCP Infrastructure",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool):
    if value:
        rprint(f"[bold]mcp-platform[/bold] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version", callback=version_callback
    ),
):
    """Personal AI Engineering Platform — Universal MCP CLI."""
    pass


# ── Lazy command registration ──────────────────────────────────────

def _register_commands():
    """Register all CLI commands with lazy imports to avoid hard crashes."""
    commands = [
        ("install", "mcp_cli.commands.install", "install_cmd"),
        ("start", "mcp_cli.commands.start_stop", "start_cmd"),
        ("stop", "mcp_cli.commands.start_stop", "stop_cmd"),
        ("restart", "mcp_cli.commands.start_stop", "restart_cmd"),
        ("status", "mcp_cli.commands.start_stop", "status_cmd"),
        ("emergency", "mcp_cli.commands.start_stop", "emergency_stop_cmd"),
        ("update", "mcp_cli.commands.update", "update_cmd"),
        ("profile", "mcp_cli.commands.profile", "profile_cmd"),
        ("generate", "mcp_cli.commands.generate", "generate_cmd"),
        ("health", "mcp_cli.commands.health", "health_cmd"),
        ("registry", "mcp_cli.commands.registry_cmd", "registry_cmd"),
        ("discover", "mcp_cli.commands.discover", "discover_cmd"),
        ("config", "mcp_cli.commands.config", "config_cmd"),
        ("benchmark", "mcp_cli.commands.benchmark", "benchmark_cmd"),
        ("project", "mcp_cli.commands.project", "project_cmd"),
        ("secrets", "mcp_cli.commands.secrets", "secrets_cmd"),
        ("logs", "mcp_cli.commands.logs", "logs_cmd"),
        ("compose", "mcp_cli.commands.compose", "compose_cmd"),
    ]
    for name, module_path, attr in commands:
        try:
            import importlib
            mod = importlib.import_module(module_path)
            cmd_fn = getattr(mod, attr)
            app.command(name=name)(cmd_fn)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load '{name}' command: {e}[/yellow]")


_register_commands()


if __name__ == "__main__":
    app()
