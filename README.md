# Personal AI Engineering Platform — MCP

> Universal MCP Infrastructure for AI-Assisted Development.
> Reusable across **every software project** you develop.

## Quick Start

```bash
# Install the platform
.\scripts\install.ps1

# Or using the CLI after pip install
pip install -e .
mcp install --tier 1
mcp generate opencode
mcp start
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `mcp install [server]` | Install MCP servers from the registry |
| `mcp start [--profile]` | Start servers with active profile |
| `mcp stop [server]` | Stop server(s) |
| `mcp restart <server>` | Restart a server |
| `mcp status` | Show server status |
| `mcp emergency stop` | Stop all servers immediately |
| `mcp update [check/apply/rollback]` | Manage updates |
| `mcp profile [list/set/current/show]` | Manage engineering profiles |
| `mcp generate <agent>` | Generate config for AI agents |
| `mcp health [check/metrics/summary]` | Health monitoring |
| `mcp registry [list/search/info]` | Query server catalog |
| `mcp config [show/path/edit]` | View/edit platform config |
| `mcp benchmark [server]` | Benchmark server performance |

## Engineering Profiles

| Profile | Focus | Servers |
|---------|-------|---------|
| `backend` | Backend APIs, databases | 8 |
| `frontend` | UI, browser, design | 7 |
| `devops` | Cloud, containers, CI/CD | 6 |
| `ai-llm` | AI models, RAG, LLMs | 7 |
| `security` | Security audits | 5 |
| `documentation` | Technical writing | 4 |
| `data-engineering` | Data pipelines | 5 |
| `full-stack` | All disciplines (default) | 11 |
| `minimal` | Lightweight coding | 3 |

## Supported AI Agents

- Claude Code
- OpenCode
- Antigravity
- Cursor
- VS Code AI Extensions

## MCP Servers (Registry)

### Tier 1 — Core
| Server | Version | Purpose |
|--------|---------|---------|
| Context7 | 3.2.3 | Live documentation |
| Serena | 1.10.0 | Semantic code understanding |
| GitHub | 2025.4.8 | Issues, PRs, code search |
| Playwright | 0.0.78 | Browser automation |
| Filesystem | 2026.7.10 | Safe file operations |
| Sequential Thinking | 2026.7.4 | Structured reasoning |

### Tier 2 — Enhanced
| Server | Version | Purpose |
|--------|---------|---------|
| PostgreSQL | 0.6.2 | Database management |
| Docker | 2026.7.4 | Container management |
| Fetch | 0.0.78 | Web research |
| Memory | 2026.7.4 | Persistent memory |

### Tier 3 — Expert
| Server | Version | Purpose |
|--------|---------|---------|
| Tavily | 1.0.0 | Production web research |

## Configuration

Platform root: `~/.config/mcp/` (Linux) | `~/Library/Application Support/mcp/` (macOS) | `%APPDATA%/mcp/` (Windows)

Override: `$env:MCP_HOME`

## Architecture

```
~/.config/mcp/
├── registry.yaml        # Server catalog (versioned)
├── config.yaml          # User preferences
├── profiles/            # Engineering profiles
├── servers/             # Server configurations
├── secrets/             # Encrypted secrets
├── cache/               # Runtime caches
├── logs/                # Platform logs
├── downloads/           # Downloaded binaries
├── templates/           # Agent config templates
└── backups/             # Update snapshots
```

## Security

- Multi-dimensional permission model (agent × profile × tool risk × server trust)
- Secrets encrypted at rest (age encryption)
- All tool calls audited
- Workspace boundaries enforced
- Deny by default — explicit approval required for high-risk operations

## License

MIT — Free for personal and commercial use.
