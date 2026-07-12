# Personal AI Engineering Platform — MCP

> Universal MCP Infrastructure for AI-Assisted Development.
> Reusable across every software project you develop.
>
> Works with: Claude Code • OpenCode • Antigravity • Cursor • VS Code AI

---

## Quick Start

```bash
# 1. Install the CLI
cd C:\workspace\Extras\personal-mcp-platform
pip install -e .

# 2. Install Tier 1 MCP servers
mcp install --tier 1

# 3. Generate config for your AI agent
mcp generate claude-code    # or: opencode, vscode, cursor, antigravity

# 4. Start the servers
mcp start --profile full-stack

# 5. Verify everything is running
mcp status
```

---

## What is This?

A **Personal AI Engineering Platform** based on the Model Context Protocol (MCP). It provides a shared, reusable set of MCP servers that any MCP-compatible AI agent can use — across **every project you develop**.

Instead of configuring MCP servers independently for each project, you maintain a single, version-controlled platform that all your AI agents consume.

---

## Key Features

- **Universal** — Works with Claude Code, OpenCode, Antigravity, Cursor, VS Code
- **Portable** — Single config used across K.A.O.S, Wakanda, and all future projects
- **Versioned** — Full Git history of every configuration change
- **Cross-platform** — Windows, macOS, Linux, WSL
- **Secure** — Multi-dimensional permissions, secrets encryption, audit logging
- **Profiles** — 9 engineering profiles with auto-detection
- **Self-healing** — Automatic health monitoring and restart
- **Updatable** — `mcp update check/apply/rollback` with backup snapshots

---

## Engineering Profiles

| Profile | Focus | Servers | When to Use |
|---------|-------|---------|-------------|
| `full-stack` | All disciplines (default) | 11 | General development |
| `backend` | APIs, databases, containers | 8 | Backend/API work |
| `frontend` | UI, browser, design | 7 | Frontend work |
| `devops` | Cloud, CI/CD, infra | 6 | Infrastructure |
| `ai-llm` | AI models, RAG, LLMs | 7 | AI development |
| `security` | Security audits | 5 | Security review |
| `documentation` | Technical writing | 4 | Writing docs |
| `data-engineering` | Data pipelines | 5 | Data work |
| `minimal` | Lightweight (low memory) | 3 | Quick edits |

---

## MCP Servers

### Tier 1 — Core (Install First)
| Server | Version | Purpose | Risk |
|--------|---------|---------|------|
| Context7 | 3.2.3 | Live documentation | Low |
| Serena | 1.10.0 | Semantic code understanding | Low |
| GitHub | 2025.4.8 | Issues, PRs, code search | Medium |
| Playwright | 0.0.78 | Browser automation | High |
| Filesystem | 2026.7.10 | Safe file operations | High |
| Sequential Thinking | 2026.7.4 | Structured reasoning | None |

### Tier 2 — Enhanced (Install on Demand)
| Server | Version | Purpose | Risk |
|--------|---------|---------|------|
| PostgreSQL | 0.6.2 | Database management | High |
| Docker | 2026.7.4 | Container management | Critical |
| Fetch | 0.0.78 | Web research | Low |
| Memory | 2026.7.4 | Persistent memory | Low |

### Tier 3 — Expert
| Server | Version | Purpose | Risk |
|--------|---------|---------|------|
| Tavily | 1.0.0 | Production web research | Low |

---

## CLI Commands

```
mcp install [server]          Install MCP servers from the registry
mcp start [--profile]         Start servers with active profile
mcp stop [server]             Stop server(s)
mcp restart <server>          Restart a server
mcp status                    Show server status
mcp emergency stop            Stop all servers immediately
mcp update [check|apply|rollback|history]
mcp profile [list|set|current|show]
mcp generate <agent>          Generate config for AI agents
mcp health [check|metrics|summary]
mcp registry [list|search|info]
mcp config [show|path|edit]
mcp benchmark [server]
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_HOME` | OS-specific | Override platform root directory |
| `MCP_PROFILE` | `full-stack` | Override active profile |
| `MCP_DEBUG` | `false` | Enable debug logging |

### Default Platform Root

| OS | Path |
|----|------|
| Linux | `~/.config/mcp/` |
| macOS | `~/Library/Application Support/mcp/` |
| Windows | `%APPDATA%/mcp/` |

---

## Project Structure

```
personal-mcp-platform/
├── registry.yaml              # Server catalog (versioned, 11 servers)
├── config/config.yaml         # User preferences
├── active_profile.yaml        # Current active profile
├── profiles/                  # 9 engineering profiles
├── mcp_cli/                   # Python CLI (core + commands)
├── docker/                    # Docker Compose stack
├── scripts/install.ps1        # Cross-platform installer
├── docs/                      # Documentation
├── secrets/                   # Encrypted secrets
├── cache/                     # Runtime caches
├── logs/                      # Platform logs
├── downloads/                 # Downloaded binaries
├── templates/                 # Agent config templates
├── backups/                   # Update snapshots
└── .gitignore
```

---

## Security Model

- **Multi-dimensional authorization**: agent × profile × tool risk × server trust × workspace boundaries × approval policy
- **Secrets management**: environment variables → encrypted files (age) → OS keychain → interactive prompt
- **Audit logging**: every tool call logged with decision, agent, server, args, timestamp
- **Workspace boundaries**: filesystem MCP restricted to project directory
- **Deny by default**: high-risk tools require explicit approval

---

## Updating

```bash
# Check for updates
mcp update check

# Apply updates (backup is automatic)
mcp update apply

# Rollback a failed update
mcp update rollback github

# View update history
mcp update history
```

---

## License

MIT — Free for personal and commercial use.
