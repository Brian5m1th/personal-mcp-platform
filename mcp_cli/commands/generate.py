"""mcp generate — Generate agent configuration files."""

from pathlib import Path

import typer
from rich import print as rprint

from mcp_cli.core.generator import AgentConfigGenerator


def generate_cmd(
    agent: str = typer.Argument("all", help="Agent: claude-code, opencode, vscode, cursor, antigravity, all"),
    output: str = typer.Option(None, "--output", "-o", help="Custom output path"),
):
    """Generate MCP configuration for AI agents."""
    gen = AgentConfigGenerator()

    agents = ["claude-code", "opencode", "vscode", "cursor", "antigravity"]
    if agent != "all":
        if agent not in agents:
            rprint(f"[red]Unknown agent: {agent}. Supported: {', '.join(agents)}[/red]")
            raise typer.Exit(1)
        agents = [agent]

    output_path = Path(output) if output else None

    for a in agents:
        try:
            path = gen.save(a, output_path)
            rprint(f"[green]✓ Generated [bold]{a}[/bold] config → {path}[/green]")
        except Exception as e:
            rprint(f"[red]✗ Failed to generate {a}: {e}[/red]")
