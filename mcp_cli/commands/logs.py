"""mcp logs — View MCP server logs."""
import os
from pathlib import Path

import typer
from rich import print as rprint
from rich.table import Table
from rich.text import Text

from mcp_cli.core.config import get_mcp_home


def logs_cmd(
    server_id: str = typer.Argument(None, help="Server ID to view logs"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Tail the log"),
):
    """View MCP server logs."""
    logs_dir = get_mcp_home() / "logs" / "servers"
    platform_log = get_mcp_home() / "logs" / "platform.log"

    if not logs_dir.exists() and not platform_log.exists():
        rprint("[yellow]No log files found[/yellow]")
        return

    if server_id:
        log_files = sorted(logs_dir.glob(f"{server_id}*.log"))
        if not log_files:
            rprint(f"[yellow]No logs found for '{server_id}'[/yellow]")
            return
        log_path = log_files[-1]
    else:
        log_path = platform_log

    if not log_path.exists():
        rprint(f"[yellow]Log file not found: {log_path}[/yellow]")
        return

    if follow:
        try:
            rprint(f"[dim]Tailing {log_path} (Ctrl+C to stop)...[/dim]")
            with open(log_path, "r", encoding="utf-8") as f:
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if line:
                        rprint(line.rstrip())
        except KeyboardInterrupt:
            pass
        return

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
    except Exception as e:
        rprint(f"[red]Failed to read log: {e}[/red]")
        return

    tail = all_lines[-lines:]
    rprint(f"[bold]Log: {log_path}[/bold]")
    rprint(f"[dim]Showing last {len(tail)} of {len(all_lines)} lines[/dim]\n")
    for line in tail:
        rprint(line.rstrip())
