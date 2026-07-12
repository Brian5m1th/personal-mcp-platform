# Development Guide — Personal AI Engineering Platform (MCP)

> Guide for contributors and developers extending the platform.

---

## Repository Structure

```
personal-mcp-platform/
├── mcp_cli/                    # Python package
│   ├── __init__.py             # Package metadata
│   ├── __main__.py             # Typer CLI entry point
│   ├── core/                   # Core library (libmcp)
│   │   ├── config.py           # Path resolution, YAML load/save, PlatformConfig
│   │   ├── transport.py        # STDIO/HTTP/SSE/WebSocket transports + Factory
│   │   ├── server_manager.py   # Server lifecycle state machine
│   │   ├── permissions.py      # Multi-dimensional authorization engine
│   │   ├── profiles.py         # Profile management + 9 built-in profiles
│   │   ├── secrets.py          # Secrets resolution (env → file → prompt)
│   │   ├── health.py           # Health monitoring + metrics (JSONL)
│   │   ├── updater.py          # Version check, backup, rollback
│   │   └── generator.py        # Agent config generation (Claude, OpenCode, etc.)
│   └── commands/               # CLI command handlers
│       ├── install.py          # mcp install
│       ├── start_stop.py       # mcp start/stop/restart/status/emergency
│       ├── update.py           # mcp update check/apply/rollback/history
│       ├── profile.py          # mcp profile list/set/current/show
│       ├── generate.py         # mcp generate <agent>
│       ├── health.py           # mcp health check/metrics/summary
│       ├── registry_cmd.py     # mcp registry list/search/info
│       ├── config.py           # mcp config show/path/edit
│       └── benchmark.py        # mcp benchmark [server]
├── registry.yaml               # Master server catalog
├── profiles/                    # Engineering profile definitions
├── config/config.yaml           # Default user configuration
├── docker/                      # Docker Compose stack
│   ├── docker-compose.yml       # 12 services
│   └── nginx.conf               # HTTP/SSE proxy
├── scripts/install.ps1          # Cross-platform installer
├── docs/                        # Documentation
├── pyproject.toml               # Python package definition
└── .gitignore
```

---

## Development Setup

### Prerequisites

- Python ≥ 3.11
- Node.js ≥ 18 (for running MCP servers)
- Git

### Clone and Install

```powershell
cd C:\workspace\Extras\personal-mcp-platform

# Install in editable mode (changes take effect immediately)
pip install -e .

# Verify
mcp --version
```

### Run Tests

```powershell
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests (when implemented)
pytest tests/
```

---

## Architecture Overview

### Core Library Components

```
mcp_cli/core/
├── config.py              # Central configuration management
├── transport.py           # Transport abstraction (STDIO, HTTP, SSE, WS)
├── server_manager.py      # Server lifecycle + state machine
├── permissions.py         # Authorization engine
├── profiles.py            # Profile management
├── secrets.py             # Secrets resolution
├── health.py              # Health monitoring
├── updater.py             # Update management
└── generator.py           # Agent config generation
```

### Key Design Patterns

**Singleton (MCPManager):** Single point of control for all server processes.

**Strategy (Transport Layer):** Pluggable transport implementations via `TransportFactory`.

**State Machine (Server Lifecycle):** Formal state transitions with guard conditions.

**Multi-dimensional Authorization:** 6 factors evaluated for every tool call.

**Single Source of Truth (registry.yaml):** All server metadata in one versioned file.

---

## Adding a New MCP Server to the Registry

1. **Verify the server** — Check npm/pypi for the package, verify it works:

```powershell
npm view <package-name> version
npx -y <package-name>
```

2. **Add entry to `registry.yaml`**:

```yaml
- id: my-server
  name: "My Server MCP"
  version: "1.0.0"
  category: custom
  description: "Description of what this server does"
  maintainer:
    name: "Author Name"
    github: "author/mcp-server"
  license: "MIT"
  maturity: experimental            # experimental | stable | deprecated
  protocol:
    default: stdio
    transports:
      - type: stdio
        command: "npx"
        args: ["-y", "my-mcp-server"]
        env: {}
  permissions:
    filesystem: none                # none | read | write | full
    network: none                   # none | https-outbound | full
    shell: false
    secrets: []
    risks:
      - level: low
        description: "What does this server access?"
  requirements:
    node: ">=18"
    npm: true
  agents:
    - claude-code
    - opencode
  platforms:
    - linux
    - macos
    - windows
    - wsl
  tags:
    - custom
    - my-tag
  install:
    method: npx
    command: "npx my-mcp-server"
    auto_update: true
    update_policy: minor
  health:
    check_method: tools/list
    expected_startup_ms: 5000
    expected_latency_ms: 500
    expected_ram_mb: 50
  benchmark:
    startup_ms: 2000
    ram_mb: 30
    latency_ms: 200
    stability: 0.95
```

3. **Add to profile(s)** — Add the server ID to relevant profiles:

```yaml
# profiles/full-stack.yaml
enabled_servers:
  - id: my-server
    tools: "*"
```

4. **Test the server**:

```bash
mcp install my-server
mcp start my-server
mcp status
mcp benchmark my-server
```

---

## Adding a New Profile

1. **Create profile file**:

```yaml
# profiles/my-specialty.yaml
name: "My Specialty Engineering"
description: "Servers relevant for my specific workflow"
icon: "star"
priority: 50

enabled_servers:
  - id: context7
    tools: "*"
  - id: github
    tools: "*"
  - id: filesystem
    workspace_bound: true

disabled_servers: []

agent_config_overrides:
  max_tools_per_server: 8
  max_total_tools: 25
```

2. **Activate it**:

```bash
mcp profile set my-specialty
mcp start
```

---

## Adding a New Command to the CLI

1. **Create the command handler** in `mcp_cli/commands/`:

```python
"""mcp mycommand — Description of the new command."""

import typer
from rich import print as rprint


def my_command_cmd(
    arg1: str = typer.Argument(..., help="Required argument"),
    flag: bool = typer.Option(False, "--flag", help="Optional flag"),
):
    """Description shown in --help."""
    rprint(f"[green]Executing my command with {arg1}, flag={flag}[/green]")
```

2. **Register in `__main__.py`**:

```python
from mcp_cli.commands.my_command import my_command_cmd

app.command(name="mycommand")(my_command_cmd)
```

3. **Test**:

```bash
mcp mycommand test --flag
```

---

## Adding a New Transport

1. **Create transport class** in `mcp_cli/core/transport.py`:

```python
class WebSocketTransport(MCPTransport):
    """WebSocket-based transport for MCP communication."""

    def __init__(self, config: dict):
        self._url = config.get("url", "")
        # ...

    async def connect(self) -> bool:
        # Implement WebSocket connection
        pass

    async def send_request(self, method: str, params: dict) -> dict:
        # Send JSON-RPC over WebSocket
        pass
    # ... implement remaining abstract methods
```

2. **Register in `TransportFactory`**:

```python
@staticmethod
def create(transport_config: dict) -> MCPTransport:
    transport_type = transport_config.get("type", "stdio")
    if transport_type == "websocket":
        return WebSocketTransport(transport_config)
    # ... existing cases
```

---

## Running Tests

```powershell
# Unit tests (when implemented)
pytest tests/unit/

# Integration tests (require running servers)
pytest tests/integration/

# With coverage
pytest --cov=mcp_cli tests/
```

---

## Code Style

This project follows:

- **Python:** PEP 8, with type hints for all functions
- **YAML:** 2-space indentation, no tab characters
- **Documentation:** Markdown, with code examples for every feature
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, etc.)

```bash
# Format code
pip install black
black mcp_cli/

# Check types
pip install mypy
mypy mcp_cli/

# Lint
pip install ruff
ruff check mcp_cli/
```

---

## Release Process

1. Update version in `pyproject.toml` and `mcp_cli/__init__.py`
2. Update `registry.yaml` with any new/changed versions
3. Run full test suite
4. Update `CHANGELOG.md`
5. Tag release: `git tag v0.2.0`
6. Push: `git push && git push --tags`
