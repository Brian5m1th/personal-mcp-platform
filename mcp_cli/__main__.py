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


# ── Import and register commands ───────────────────────────────────

from mcp_cli.commands.install import install_cmd
from mcp_cli.commands.start_stop import start_cmd, stop_cmd, restart_cmd, status_cmd, emergency_stop_cmd
from mcp_cli.commands.update import update_cmd
from mcp_cli.commands.profile import profile_cmd
from mcp_cli.commands.generate import generate_cmd
from mcp_cli.commands.health import health_cmd
from mcp_cli.commands.registry_cmd import registry_cmd
from mcp_cli.commands.config import config_cmd
from mcp_cli.commands.benchmark import benchmark_cmd

app.command(name="install")(install_cmd)
app.command(name="start")(start_cmd)
app.command(name="stop")(stop_cmd)
app.command(name="restart")(restart_cmd)
app.command(name="status")(status_cmd)
app.command(name="emergency")(emergency_stop_cmd)
app.command(name="update")(update_cmd)
app.command(name="profile")(profile_cmd)
app.command(name="generate")(generate_cmd)
app.command(name="health")(health_cmd)
app.command(name="registry")(registry_cmd)
app.command(name="config")(config_cmd)
app.command(name="benchmark")(benchmark_cmd)


if __name__ == "__main__":
    app()
