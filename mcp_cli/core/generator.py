"""
Agent configuration generators — generate configs for Claude Code, OpenCode, VS Code, etc.
"""

import json
from pathlib import Path

import yaml
from jinja2 import Environment, PackageLoader
from loguru import logger

from mcp_cli.core.config import PlatformConfig, get_mcp_home


class AgentConfigGenerator:
    """Generates MCP server configuration for various AI agents."""

    def __init__(self):
        self.config = PlatformConfig()
        self._templates_dir = get_mcp_home() / "templates"
        self._templates_dir.mkdir(parents=True, exist_ok=True)

    def _get_servers_for_agent(self) -> list[dict]:
        """Get the currently enabled servers in the format needed for agent configs."""
        servers = self.config.get_enabled_servers()
        result = []
        for s in servers:
            transport = s.get("protocol", {}).get("transports", [{}])[0]
            # Resolve placeholders in args
            args = []
            for arg in transport.get("args", []):
                arg = arg.replace("{{workspace}}", str(Path.cwd()))
                arg = arg.replace("{{mcp_home}}", str(get_mcp_home()))
                args.append(arg)
            # Resolve env vars
            env = {}
            for key, val in transport.get("env", {}).items():
                env[key] = val
            # Check availability
            available = True
            import os
            sid = s.get("id", "")
            if sid == "docker":
                # Check if Docker daemon is accessible
                available = os.system("docker ps >nul 2>&1") == 0 if os.name == "nt" else os.system("docker ps >/dev/null 2>&1") == 0
            elif sid == "postgres":
                # Check if DATABASE_URL is set
                available = bool(os.environ.get("DATABASE_URL"))
            elif sid == "github":
                # Check if GITHUB_TOKEN is set
                available = bool(os.environ.get("GITHUB_TOKEN"))
            result.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "command": transport.get("command"),
                "args": args,
                "env": env,
                "available": available,
            })
        return result

    def generate_claude_code(self) -> dict:
        """Generate ~/.claude.json configuration."""
        servers = self._get_servers_for_agent()
        config = {"mcpServers": {}}
        for s in servers:
            # Resolve env vars
            env = {}
            for key, val in s.get("env", {}).items():
                # Keep env var references as-is (Claude Code resolves them)
                env[key] = val

            config["mcpServers"][s["id"]] = {
                "command": s["command"],
                "args": s["args"],
                "env": env,
            }
        return config

    def generate_opencode(self) -> dict:
        """Generate .opencode.json configuration using OpenCode MCP format.

        OpenCode uses:
          mcp.<name>.type = "local"
          mcp.<name>.command = ["npx", "-y", "@package/name"]
          mcp.<name>.environment = { ... }
        """
        servers = self._get_servers_for_agent()
        config = {"mcp": {}}
        for s in servers:
            cmd = [s["command"]]
            cmd.extend(s["args"])
            entry = {
                "type": "local",
                "command": cmd,
            }
            # Disable servers that are not available (Docker not running, no DATABASE_URL, etc.)
            if not s.get("available", True):
                entry["enabled"] = False
            env = {}
            for key, val in s.get("env", {}).items():
                env[key] = val
            if env:
                entry["environment"] = env
            config["mcp"][s["id"]] = entry
        return config

    def generate_vscode(self) -> dict:
        """Generate VS Code settings.json MCP configuration."""
        servers = self._get_servers_for_agent()
        config = {
            "mcp": {
                "servers": {}
            }
        }
        for s in servers:
            config["mcp"]["servers"][s["id"]] = {
                "type": "stdio",
                "command": s["command"],
                "args": s["args"],
            }
        return config

    def generate_cursor(self) -> dict:
        """Generate Cursor MCP configuration (experimental feature flag format)."""
        servers = self._get_servers_for_agent()
        config = {"mcpServers": {}}
        for s in servers:
            config["mcpServers"][s["id"]] = {
                "command": s["command"],
                "args": s["args"],
            }
            env = {}
            for key, val in s.get("env", {}).items():
                env[key] = val
            if env:
                config["mcpServers"][s["id"]]["env"] = env
        return config

    def generate_antigravity(self) -> dict:
        """Generate Antigravity MCP configuration."""
        servers = self._get_servers_for_agent()
        return {"mcpServers": {s["id"]: {"command": s["command"], "args": s["args"]} for s in servers}}

    def save(self, agent: str, output_path: Path | None = None) -> str:
        """Generate and save agent configuration."""
        generators = {
            "claude-code": self.generate_claude_code,
            "opencode": self.generate_opencode,
            "vscode": self.generate_vscode,
            "cursor": self.generate_cursor,
            "antigravity": self.generate_antigravity,
        }

        generator = generators.get(agent)
        if generator is None:
            raise ValueError(f"Unknown agent: {agent}. Supported: {', '.join(generators.keys())}")

        config = generator()

        # Determine output path
        if output_path is None:
            home = Path.home()
            output_paths = {
                "claude-code": home / ".claude.json",
                "opencode": Path.cwd() / ".opencode" / "opencode.json",
                "vscode": home / ".config" / "Code" / "User" / "settings.json",
                "cursor": home / ".cursor" / "mcp.json",
                "antigravity": home / ".antigravity" / "mcp.json",
            }
            output_path = output_paths.get(agent, Path.cwd() / f".mcp.{agent}.json")

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write configuration
        with open(output_path, "w", encoding="utf-8") as f:
            if agent == "opencode":
                # OpenCode uses mcp.<name>.type = "local" + command array format
                # Preserve existing fields like $schema and plugin if present
                existing = {}
                if output_path.exists():
                    try:
                        existing = json.loads(output_path.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                # Remove old format keys if present
                existing.pop("mcpServers", None)
                existing.pop("mcp", None)
                # Merge: keep existing $schema, plugin; add MCP servers
                merged = dict(existing)
                # Ensure $schema and plugin if not present
                if "$schema" not in merged:
                    merged["$schema"] = "https://opencode.ai/config.json"
                if "plugin" not in merged:
                    merged["plugin"] = []
                # Add the new mcp config
                merged["mcp"] = config.get("mcp", {})
                json.dump(merged, f, indent=2, ensure_ascii=False)
            else:
                json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated {agent} config at {output_path}")
        return str(output_path)
