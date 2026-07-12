"""mcp secrets — Manage MCP secrets."""
import typer
from rich import print as rprint
from rich.table import Table

from mcp_cli.core.secrets import SecretsManager
from mcp_cli.core.config import PlatformConfig


def secrets_cmd(
    action: str = typer.Argument("list", help="Action: list, set, show, check"),
    server_id: str = typer.Argument(None, help="Server ID (for set/show/check)"),
    key: str = typer.Option(None, "--key", "-k", help="Secret key name"),
    value: str = typer.Option(None, "--value", "-v", help="Secret value"),
):
    """Manage MCP secrets (env vars, tokens, connection strings)."""
    secrets = SecretsManager()
    config = PlatformConfig()

    if action == "list":
        servers = config.registry.get("servers", [])
        table = Table(title="Required Secrets")
        table.add_column("Server", style="cyan")
        table.add_column("Secret")
        table.add_column("Required")
        table.add_column("Status")

        for s in servers:
            req_secrets = s.get("requirements", {}).get("secrets", {})
            if not req_secrets:
                continue
            for secret_name, secret_info in req_secrets.items():
                resolved = secrets.resolve(secret_name)
                env_var = secret_info.get("env_var", secret_name)
                status = "[green]v Set[/green]" if resolved else "[red]x Missing[/red]"
                table.add_row(
                    s.get("id", "?"),
                    f"{secret_name} ({env_var})",
                    str(secret_info.get("required", True)),
                    status,
                )
        if not table.rows:
            rprint("[yellow]No servers require secrets[/yellow]")
        else:
            rprint(table)

    elif action == "set":
        if not server_id or not key:
            rprint("[red]Usage: mcp secrets set <server_id> --key <name> --value <value>[/red]")
            raise typer.Exit(1)
        secrets.set_env(key, value)
        rprint(f"[green]v Secret '{key}' stored for '{server_id}'[/green]")

    elif action == "show":
        if not server_id:
            rprint("[red]Server ID required[/red]")
            raise typer.Exit(1)
        entry = config.get_server(server_id)
        if entry is None:
            rprint(f"[red]Server '{server_id}' not found[/red]")
            raise typer.Exit(1)
        missing = secrets.check_all_required(entry)
        if not missing:
            rprint(f"[green]All secrets for '{server_id}' are set[/green]")
        else:
            rprint(f"[yellow]Missing secrets for '{server_id}':[/yellow]")
            for m in missing:
                rprint(f"  [red]x {m}[/red]")

    elif action == "check":
        servers = config.registry.get("servers", [])
        any_missing = False
        for s in servers:
            missing = secrets.check_all_required(s)
            if missing:
                any_missing = True
                rprint(f"[yellow]{s['id']}: missing {', '.join(missing)}[/yellow]")
        if not any_missing:
            rprint("[green]All secrets are set[/green]")

    else:
        rprint(f"[red]Unknown action: {action}. Use: list, set, show, check[/red]")
