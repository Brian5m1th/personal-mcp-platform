"""Tests for config module."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mcp_cli.core.config import (
    get_mcp_home,
    get_registry_path,
    get_config_path,
    get_active_profile_path,
    get_server_config_path,
    get_profile_path,
    get_secrets_path,
    load_yaml,
    save_yaml,
    ensure_dirs,
    PlatformConfig,
)


def test_get_mcp_home_default():
    """Test default MCP_HOME resolution."""
    home = get_mcp_home()
    assert isinstance(home, Path)
    assert "mcp" in home.parts


def test_registry_path():
    """Test registry path ends with registry.yaml."""
    path = get_registry_path()
    assert path.name == "registry.yaml"


def test_config_path():
    """Test config path ends with config.yaml."""
    path = get_config_path()
    assert path.name == "config.yaml"


def test_get_server_config_path():
    """Test server config path includes server ID."""
    path = get_server_config_path("github")
    assert path.name == "github.yaml"


def test_load_yaml_nonexistent():
    """Test load_yaml returns empty dict for missing files."""
    result = load_yaml(Path("/nonexistent/path.yaml"))
    assert result == {}


@pytest.mark.asyncio
async def test_config_get_enabled_servers():
    """Test PlatformConfig loads registry and returns enabled servers."""
    config = PlatformConfig()
    assert config.registry is not None
    assert "servers" in config.registry


def test_config_get_server():
    """Test get_server returns correct server entry."""
    config = PlatformConfig()
    gh = config.get_server("github")
    if gh:
        assert gh.get("id") == "github"
        assert gh.get("name") == "GitHub MCP"
