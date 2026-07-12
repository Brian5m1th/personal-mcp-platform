# CLI Usage Guide — Personal AI Engineering Platform (MCP)

> Full reference for all `mcp` commands.

---

## Global Options

| Option | Description |
|--------|-------------|
| `--version`, `-V` | Show version |
| `--help` | Show help |

---

## `mcp install` — Install Servers

```bash
# Install all Tier 1 servers (Context7, GitHub, Filesystem, Sequential Thinking)
mcp install --tier 1

# Install a specific server
mcp install github

# Install multiple servers
mcp install context7
mcp install serena
mcp install playwright

# Check for missing secrets during install
mcp install --check-secrets
```

**Output:**
```
Installing github...
  ✓ Installed successfully
  ⚠ Requires secrets: GITHUB_TOKEN
  Set environment variable: GITHUB_TOKEN

Result: 1/1 installed successfully
```

---

## `mcp start` — Start Servers

```bash
# Start all servers in the active profile
mcp start

# Start with a specific profile
mcp start --profile backend

# Start a single server
mcp start github
```

---

## `mcp stop` — Stop Servers

```bash
# Stop all servers
mcp stop

# Stop a specific server
mcp stop github
```

---

## `mcp restart` — Restart Server

```bash
# Restart a single server
mcp restart github
```

---

## `mcp status` — Server Status

```bash
mcp status
```

**Output:**
```
┌──────────────────────────────────────────────────┐
│                  MCP Server Status                │
├──────────┬───────────┬───────┬─────────┬─────────┤
│ Server   │ State     │ Tools │ Health  │ Latency │
├──────────┼───────────┼───────┼─────────┼─────────┤
│ context7 │ healthy   │    12 │ healthy │  120ms  │
│ github   │ healthy   │     8 │ healthy │  800ms  │
│ filesys. │ healthy   │     6 │ healthy │   50ms  │
│ seq-thk  │ healthy   │     1 │ healthy │   10ms  │
└──────────┴───────────┴───────┴─────────┴─────────┘
```

---

## `mcp emergency stop` — Emergency Stop

```bash
# Immediately stop ALL server processes
mcp emergency stop
```

---

## `mcp profile` — Profile Management

```bash
# List all available profiles
mcp profile list

# Set active profile
mcp profile set backend

# Show current profile
mcp profile current

# Show profile details
mcp profile show ai-llm
```

**Profile List Output:**
```
┌──────────────────────────────────────────────┐
│           MCP Engineering Profiles            │
├──────────────┬──────────────────┬────────┬────┤
│ ID           │ Name             │ Servers│    │
├──────────────┼──────────────────┼────────┼────┤
│ backend      │ Backend Eng.     │      8 │    │
│ frontend     │ Frontend Eng.    │      7 │    │
│ devops       │ DevOps           │      6 │    │
│ ai-llm       │ AI / LLM Eng.    │      7 │    │
│ security     │ Security Eng.    │      5 │    │
│ documentat.  │ Documentation    │      4 │    │
│ data-engin.  │ Data Engineering │      5 │    │
│ full-stack   │ Full Stack       │     11 │    │
│ minimal      │ Minimal          │      3 │    │
└──────────────┴──────────────────┴────────┴────┘
```

---

## `mcp generate` — Generate Agent Configurations

```bash
# Generate for all agents
mcp generate all

# Generate for a specific agent
mcp generate claude-code
mcp generate opencode
mcp generate vscode
mcp generate cursor
mcp generate antigravity

# Custom output path
mcp generate claude-code --output C:\Users\brian\.claude.json
```

**Generated files:**
| Agent | Default Path |
|-------|-------------|
| Claude Code | `~/.claude.json` |
| OpenCode | `.opencode.json` (current directory) |
| VS Code | `~/.config/Code/User/settings.json` |
| Cursor | `~/.cursor/mcp.json` |
| Antigravity | `~/.antigravity/mcp.json` |

---

## `mcp health` — Health Monitoring

```bash
# Quick health check of all servers
mcp health check

# View detailed metrics
mcp health metrics

# View metrics for a specific server
mcp health metrics --server github

# View health summary
mcp health summary

# View summary for specific server
mcp health summary --server context7
```

**Health Check Output:**
```
┌────────────────────────────────────────┐
│           MCP Server Health            │
├──────────┬──────────┬─────────┬────────┤
│ Server   │ Status   │ Latency │ Tools  │
├──────────┼──────────┼─────────┼────────┤
│ context7 │ healthy  │  120ms  │     12 │
│ github   │ healthy  │  800ms  │      8 │
│ filesys. │ healthy  │   50ms  │      6 │
│ seq-thk  │ healthy  │   10ms  │      1 │
└──────────┴──────────┴─────────┴────────┘
```

---

## `mcp registry` — Registry Queries

```bash
# List all servers by category
mcp registry list

# Search for servers
mcp registry search github
mcp registry search database
mcp registry search browser

# Show detailed server info
mcp registry info github
mcp registry info context7
```

**Server Info Output:**
```
Server: github
  Name: GitHub MCP
  Version: 2025.4.8
  Category: source-control
  Maturity: stable
  License: MIT
  Description: Complete GitHub integration...
  Permissions:
    Filesystem: none
    Network: https-outbound
    Shell: false
    Risks:
      • [medium] GitHub API access...
  Install:
    Method: npx
    Command: npx @modelcontextprotocol/server-github
  Compatibility:
    Agents: claude-code, opencode, antigravity, cursor, vscode
    Platforms: linux, macos, windows, wsl
```

---

## `mcp update` — Updates

```bash
# Check for available updates
mcp update check

# Check specific server
mcp update check github

# Apply all pending updates
mcp update apply

# Apply specific server update
mcp update apply github

# View update history
mcp update history

# Rollback last update
mcp update rollback github

# Rollback to specific version
mcp update rollback github --version 2025.4.8
```

---

## `mcp config` — Configuration

```bash
# Show current configuration and paths
mcp config show

# Show only the MCP_HOME path
mcp config path

# Open config file in default editor
mcp config edit
```

---

## `mcp benchmark` — Performance Testing

```bash
# Benchmark all servers
mcp benchmark

# Benchmark a specific server
mcp benchmark github
mcp benchmark context7
```

**Benchmark Output:**
```
┌──────────────────────────────────────────────────┐
│               Benchmark Results                  │
├──────────┬──────────┬──────────┬─────────┬───────┤
│ Server   │ Startup  │ tools/li │ Latency  │ Tools│
├──────────┼──────────┼──────────┼─────────┼───────┤
│ context7 │   800ms  │   30ms   │  120ms  │    12 │
│ github   │  2000ms  │  100ms   │  800ms  │     8 │
│ filesys. │  1000ms  │   10ms   │   50ms  │     6 │
│ seq-thk  │   800ms  │    5ms   │   10ms  │     1 │
└──────────┴──────────┴──────────┴─────────┴───────┘

Average startup: 1150ms
```
