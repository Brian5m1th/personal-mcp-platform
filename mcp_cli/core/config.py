"""
Configuration management — platform paths, file resolution, and schema.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger


def get_mcp_home() -> Path:
    """Resolve the MCP platform root directory.

    Resolution order:
    1. MCP_HOME environment variable
    2. OS-specific default:
       - Linux: ~/.config/mcp/
       - macOS: ~/Library/Application Support/mcp/
       - Windows: %APPDATA%/mcp/
    """
    env_home = os.environ.get("MCP_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()

    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "mcp"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "mcp"
    else:
        # Linux and everything else (including WSL)
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return Path(xdg) / "mcp"
        return Path.home() / ".config" / "mcp"


def ensure_dirs() -> Path:
    """Ensure all required platform directories exist. Returns MCP_HOME."""
    home = get_mcp_home()
    dirs = [
        home,
        home / "profiles",
        home / "servers",
        home / "secrets",
        home / "cache" / "tools",
        home / "cache" / "schemas",
        home / "cache" / "health",
        home / "logs" / "servers",
        home / "downloads",
        home / "templates",
        home / "backups",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.debug(f"MCP_HOME resolved to: {home}")
    return home


def get_registry_path() -> Path:
    return get_mcp_home() / "registry.yaml"


def get_config_path() -> Path:
    return get_mcp_home() / "config.yaml"


def get_active_profile_path() -> Path:
    return get_mcp_home() / "active_profile.yaml"


def get_server_config_path(server_id: str) -> Path:
    return get_mcp_home() / "servers" / f"{server_id}.yaml"


def get_profile_path(name: str) -> Path:
    return get_mcp_home() / "profiles" / f"{name}.yaml"


def get_secrets_path(name: str) -> Path:
    return get_mcp_home() / "secrets" / f"{name}.yaml"


def load_yaml(path: Path) -> dict:
    """Load a YAML file, returning empty dict if not found."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load {path}: {e}")
        return {}


def save_yaml(path: Path, data: dict) -> None:
    """Save a dict as YAML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    logger.debug(f"Saved {path}")


class PlatformConfig:
    """Central configuration for the MCP platform."""

    def __init__(self):
        self.mcp_home = ensure_dirs()
        self.registry = load_yaml(get_registry_path())
        self.config = load_yaml(get_config_path())
        self.active_profile = load_yaml(get_active_profile_path())

    def get_enabled_servers(self) -> list[dict]:
        """Resolve the list of enabled servers based on active profile."""
        profile_name = self.active_profile.get("active_profiles", ["full-stack"])[0]
        profile = load_yaml(get_profile_path(profile_name))
        enabled_ids = profile.get("enabled_servers", [])
        if not enabled_ids:
            # Fallback: all servers in registry
            return self.registry.get("servers", [])
        return [
            s for s in self.registry.get("servers", [])
            if s.get("id") in enabled_ids
        ]

    def get_server(self, server_id: str) -> dict | None:
        """Look up a server by ID in the registry."""
        for s in self.registry.get("servers", []):
            if s.get("id") == server_id:
                return s
        return None

    def get_installed_servers(self) -> list[str]:
        """List server IDs that have local config files."""
        servers_dir = self.mcp_home / "servers"
        if not servers_dir.exists():
            return []
        return [f.stem for f in sorted(servers_dir.glob("*.yaml"))]
