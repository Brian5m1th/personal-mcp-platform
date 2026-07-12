# Installation Guide — Personal AI Engineering Platform (MCP)

---

## Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| **Python** | ≥ 3.11 | `python --version` |
| **Node.js** | ≥ 18 | `node --version` |
| **npm** | ≥ 9 | `npm --version` |
| **Git** | ≥ 2.0 | `git --version` |
| **Docker** (optional) | ≥ 24 | `docker --version` |

---

## Method 1: Automated Installer (Recommended)

### Windows (PowerShell)

```powershell
# Open PowerShell as Administrator and run:
cd C:\workspace\Extras\personal-mcp-platform
.\scripts\install.ps1
```

The installer will:
1. Verify prerequisites
2. Create `%APPDATA%/mcp/` directory structure
3. Initialize all 9 engineering profiles
4. Install Tier 1 MCP servers (Context7, GitHub, Filesystem, Sequential Thinking)
5. Generate Claude Code and OpenCode configurations
6. Verify the installation

### Options

```powershell
# Install a specific server only
.\scripts\install.ps1 -ServerId github

# Set a specific profile
.\scripts\install.ps1 -Profile minimal

# Preview without installing
.\scripts\install.ps1 -DryRun
```

---

## Method 2: Manual Installation

### Step 1: Install the CLI

```bash
cd C:\workspace\Extras\personal-mcp-platform
pip install -e .

# Verify installation
mcp --version
```

### Step 2: Initialize Platform Directories

```bash
# The directories are created automatically on first use.
# Or run any command to trigger initialization:
mcp config show
```

### Step 3: Create Profiles

```bash
# Profiles are created automatically. Verify with:
mcp profile list
```

### Step 4: Install MCP Servers

```bash
# Install all Tier 1 servers
mcp install --tier 1

# Or install a specific server
mcp install github
mcp install context7
```

### Step 5: Set Environment Variables

```powershell
# Required for GitHub MCP
$env:GITHUB_TOKEN = "ghp_your_token_here"

# Optional: Override platform root
$env:MCP_HOME = "C:\Users\brian\.config\mcp"

# Optional: Set active profile
$env:MCP_PROFILE = "backend"
```

### Step 6: Generate Agent Configuration

```bash
# For Claude Code
mcp generate claude-code

# For OpenCode (generates .opencode.json in current directory)
mcp generate opencode

# For all agents
mcp generate all
```

### Step 7: Start the Servers

```bash
# Start all servers with default profile
mcp start

# Start with specific profile
mcp start --profile ai-llm

# Start a single server
mcp start github
```

### Step 8: Verify

```bash
# Check server status
mcp status

# Run health check
mcp health check

# Run benchmark
mcp benchmark
```

---

## Method 3: Docker (Containerized)

```bash
cd C:\workspace\Extras\personal-mcp-platform

# Start all Tier 1 servers
docker compose -f docker/docker-compose.yml --profile full up -d

# Start only specific profiles
docker compose -f docker/docker-compose.yml --profile ai-llm up -d
```

---

## Post-Installation Checklist

- [ ] `mcp config show` — Configuration loaded
- [ ] `mcp registry list` — Servers visible in registry
- [ ] `mcp profile list` — All 9 profiles available
- [ ] `mcp status` — Servers running
- [ ] `mcp health check` — All servers healthy
- [ ] `~/.claude.json` or `.opencode.json` generated
- [ ] `GITHUB_TOKEN` environment variable set

---

## Troubleshooting

### "Command not found" after pip install
```bash
# Ensure Python Scripts directory is in PATH
pip show mcp-platform | Select-String "Location"
# Add the Scripts directory from your Python installation to PATH
```

### Server fails to start
```bash
# Check server logs
mcp update rollback <server>
mcp server reset <server>
mcp install <server>
```

### Permission errors
```bash
# Ensure MCP_HOME directory is writable
# On Windows, check %APPDATA%/mcp/ permissions
```

### Port conflicts
```bash
# Docker stack uses port 8080 for the nginx proxy
# Change in docker/nginx.conf if needed
```
