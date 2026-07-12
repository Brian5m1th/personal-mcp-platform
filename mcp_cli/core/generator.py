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
            result.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "command": transport.get("command"),
                "args": transport.get("args", []),
                "env": transport.get("env", {}),
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
        """Generate .opencode.json configuration."""
        servers = self._get_servers_for_agent()
        config = {"mcpServers": {}}
        for s in servers:
            config["mcpServers"][s["id"]] = {
                "command": s["command"],
                "args": s["args"],
            }
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
        """Generate Cursor MCP configuration."""
        # Cursor uses the same format as VS Code
        return self.generate_vscode()

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
                "opencode": Path.cwd() / ".opencode.json",
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
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated {agent} config at {output_path}")
        return str(output_path)
