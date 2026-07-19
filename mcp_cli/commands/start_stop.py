"""mcp start/stop/restart/status/emergency — Server lifecycle commands.

Supports both in-process (interactive) and detached (background via PID files) modes.
"""

import asyncio
import json
import os
import signal
import subprocess
import sys

import typer
from rich import print as rprint
from rich.table import Table

from mcp_cli.core.server_manager import ServerManager


# ── PID File Helpers ───────────────────────────────────────────

def _get_pid_dir():
    from mcp_cli.core.config import get_mcp_home
    d = get_mcp_home() / "cache" / "pids"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_pid(server_id: str, pid: int):
    pid_file = _get_pid_dir() / f"{server_id}.pid"
    pid_file.write_text(json.dumps({"pid": pid, "server": server_id}), encoding="utf-8")


def _read_pid(server_id: str) -> int | None:
    pid_file = _get_pid_dir() / f"{server_id}.pid"
    if not pid_file.exists():
        return None
    try:
        data = json.loads(pid_file.read_text(encoding="utf-8"))
        return data.get("pid")
    except Exception:
        return None


def _remove_pid(server_id: str):
    pid_file = _get_pid_dir() / f"{server_id}.pid"
    pid_file.unlink(missing_ok=True)


def _is_pid_alive(pid: int) -> bool:
    """Check if a process is running by PID."""
    try:
        os.kill(pid, 0)  # signal 0 = check existence only
        return True
    except (OSError, ProcessLookupError):
        return False


def _list_pids() -> list[dict]:
    """List all servers with saved PIDs, filtering out dead ones."""
    results = []
    for pid_file in sorted(_get_pid_dir().glob("*.pid")):
        server_id = pid_file.stem
        pid = _read_pid(server_id)
        if pid is None:
            continue
        alive = _is_pid_alive(pid)
        results.append({
            "id": server_id,
            "pid": pid,
            "alive": alive,
        })
        if not alive:
            _remove_pid(server_id)  # Clean up dead PIDs
    return results


# ── Start (Detached Mode) ──────────────────────────────────────

def _start_detached(server_id: str):
    """Start a server as a detached background process using the mcp CLI itself."""
    python = sys.executable
    script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "__main__.py")
    cmd = [python, script, "start", server_id, "--detach-child"]

    if sys.platform == "win32":
        proc = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    _save_pid(server_id, proc.pid)
    return proc.pid


# ── Async Runner Functions ─────────────────────────────────────

async def _run_start(server_id: str | None, profile: str | None, detach: bool):
    if detach and server_id:
        pid = _start_detached(server_id)
        rprint(f"[green]v Started '{server_id}' in background (pid={pid})[/green]")
        return

    mgr = ServerManager()

    # Auto-detect profile if not specified
    if profile is None and server_id is None:
        from mcp_cli.core.profiles import ProfileManager
        pm = ProfileManager()
        detected = pm.auto_detect(os.getcwd())
        if detected:
            profile = detected
            rprint(f"[dim]Auto-detected profile: {profile}[/dim]")

    if profile:
        from mcp_cli.core.config import save_yaml, get_active_profile_path
        import time
        save_yaml(get_active_profile_path(), {
            "active_profiles": [profile],
            "set_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": "cli",
        })
        rprint(f"[dim]Profile set to: {profile}[/dim]")

    if server_id:
        result = await mgr.start_one(server_id)
        if result:
            rprint(f"[green]v Started '{server_id}'[/green]")
            # Save PID for detach tracking
            server = mgr.get_server(server_id)
            if server and server.transport:
                info = server.transport.get_server_info()
                if info.get("type") == "stdio" and info.get("pid"):
                    _save_pid(server_id, info["pid"])
        else:
            rprint(f"[red]x Failed to start '{server_id}'[/red]")
    else:
        count = await mgr.start_all()
        rprint(f"[green]v Started {count} server(s)[/green]")

    # Start periodic health checks
    await mgr.start_periodic_health_checks()

    statuses = mgr.get_status_all()
    _display_status(statuses)

    # If in-process, keep running for background mode
    if not detach and server_id is None:
        # Keep running if we started servers in-process
        try:
            rprint("\n[dim]Press Ctrl+C to stop all servers[/dim]")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            rprint("\n[yellow]Shutting down...[/yellow]")
            mgr.stop_periodic_health_checks()
            await mgr.stop_all()
            rprint("[green]All servers stopped.[/green]")


async def _run_stop(server_id: str | None):
    # First, try to stop in-process servers
    mgr = ServerManager()
    if server_id:
        result = await mgr.stop_one(server_id)
        if result:
            rprint(f"[green]v Stopped '{server_id}'[/green]")
            _remove_pid(server_id)
            return

    # If not in-process, try PID-based stop
    pids = _list_pids()
    if server_id:
        pids = [p for p in pids if p["id"] == server_id]

    if not pids:
        if server_id:
            rprint(f"[yellow]No running process found for '{server_id}'[/yellow]")
        else:
            rprint("[yellow]No servers running.[/yellow]")
        return

    for entry in pids:
        try:
            if sys.platform == "win32":
                try:
                    os.kill(entry["pid"], signal.CTRL_BREAK_EVENT)
                except Exception:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(entry["pid"])],
                        capture_output=True, timeout=5
                    )
            else:
                os.kill(entry["pid"], signal.SIGTERM)
            _remove_pid(entry["id"])
            rprint(f"[green]v Stopped '{entry['id']}' (pid={entry['pid']})[/green]")
        except Exception as e:
            rprint(f"[red]x Failed to stop '{entry['id']}': {e}[/red]")
            _remove_pid(entry["id"])


async def _run_restart(server_id: str):
    await _run_stop(server_id)
    await _run_start(server_id, None, False)


async def _run_status():
    # Check in-process servers
    mgr = ServerManager()
    statuses = mgr.get_status_all()

    # Also check PID-based servers
    pids = _list_pids()
    for p in pids:
        # Don't duplicate if already in in-process list
        if not any(s.get("id") == p["id"] for s in statuses):
            statuses.append({
                "id": p["id"],
                "state": "running (background)" if p["alive"] else "stopped",
                "tools_count": "?",
                "health": {"status": "background" if p["alive"] else "stopped", "latency_ms": 0, "error": None},
                "pid": p["pid"],
            })

    if not statuses:
        rprint("[yellow]No servers running. Use 'mcp start' to start servers.[/yellow]")
        return
    _display_status(statuses)


def _display_status(statuses: list[dict]):
    if not statuses:
        return
    table = Table(title="MCP Server Status")
    table.add_column("Server", style="cyan")
    table.add_column("State", style="bold")
    table.add_column("Tools", justify="right")
    table.add_column("Health")
    table.add_column("Latency")

    for s in statuses:
        health = s.get("health", {})
        state = s.get("state", "unknown")
        state_style = {
            "healthy": "green",
            "running": "green",
            "running (background)": "blue",
            "degraded": "yellow",
            "failed": "red",
            "stopped": "dim",
        }.get(state, "white")
        health_str = health.get("status", "?")
        health_style = "green" if health_str == "healthy" else "blue" if health_str == "background" else "red"
        table.add_row(
            s.get("id", "?"),
            f"[{state_style}]{state}[/{state_style}]",
            str(s.get("tools_count", 0)),
            f"[{health_style}]{health_str}[/{health_style}]",
            f"{health.get('latency_ms', 0)}ms",
        )
    rprint(table)


async def _run_emergency_stop():
    # Stop in-process
    mgr = ServerManager()
    rprint("[bold red]EMERGENCY STOP — Stopping all servers...[/bold red]")
    await mgr.emergency_stop()

    # Also kill all PIDs
    for entry in _list_pids():
        try:
            os.kill(entry["pid"], signal.SIGKILL if sys.platform != "win32" else signal.CTRL_BREAK_EVENT)
            _remove_pid(entry["id"])
        except Exception:
            _remove_pid(entry["id"])

    rprint("[green]All servers stopped.[/green]")


# ── Typer Command Handlers ─────────────────────────────────────

def start_cmd(
    server_id: str = typer.Argument(None, help="Server ID to start (omit for all)"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to activate"),
    detach: bool = typer.Option(False, "--detach", "-d", help="Run in background"),
):
    """Start MCP server(s).

    Use --detach to start servers in the background (persists after CLI exits).
    Without --detach, servers stop when you press Ctrl+C.
    """
    asyncio.run(_run_start(server_id, profile, detach))


def stop_cmd(
    server_id: str = typer.Argument(None, help="Server ID to stop (omit for all)"),
):
    """Stop MCP server(s). Stops both in-process and background servers."""
    asyncio.run(_run_stop(server_id))


def restart_cmd(
    server_id: str = typer.Argument(..., help="Server ID to restart"),
):
    """Restart a single MCP server."""
    asyncio.run(_run_restart(server_id))


def status_cmd():
    """Show status of all MCP servers (in-process and background)."""
    asyncio.run(_run_status())


def emergency_stop_cmd(
    action: str = typer.Argument("stop", help="Action: stop"),
):
    """Emergency stop all MCP servers."""
    if action == "stop":
        asyncio.run(_run_emergency_stop())
    else:
        rprint(f"[red]Unknown action: {action}")
