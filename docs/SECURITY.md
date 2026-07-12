# Security Model — Personal AI Engineering Platform (MCP)

---

## Overview

The MCP Platform uses a defense-in-depth security strategy with multiple layers of protection:

1. Multi-dimensional authorization
2. Secret encryption at rest
3. Workspace boundaries
4. Audit logging
5. Trust-based server classification
6. Deny-by-default policy

---

## Authorization Engine

Every tool call is evaluated across 6 dimensions:

| Dimension | Description | Example Values |
|-----------|-------------|----------------|
| **Agent Identity** | Which AI agent is making the call | Claude Code, OpenCode, Antigravity |
| **Permission Profile** | Which profile is active | backend, frontend, devops |
| **Tool Risk Level** | How dangerous is the tool | none, low, medium, high, critical |
| **Server Trust Level** | How trusted is the server | high, medium, low, untrusted |
| **Workspace** | Which project directory | `C:\workspace\KAOS`, `C:\workspace\Wakanda` |
| **Approval Policy** | Does the tool require user approval | auto, confirm, deny |

### Decision Matrix

| Trust \ Risk | None | Low | Medium | High | Critical |
|-------------|------|-----|--------|------|----------|
| **High** | ALLOW | ALLOW | ALLOW | APPROVAL | DENY |
| **Medium** | ALLOW | ALLOW | APPROVAL | DENY | DENY |
| **Low** | DENY | DENY | DENY | DENY | DENY |
| **Untrusted** | DENY | DENY | DENY | DENY | DENY |

### Approval Levels

| Level | Behavior | Example |
|-------|----------|---------|
| **auto** | Automatically allowed | `filesystem_search` |
| **confirm** | User must confirm via CLI | `filesystem_write` to new path |
| **deny** | Never allowed | `docker_destroy_all` |

---

## Server Trust Classification

| Trust Level | Description | Examples |
|-------------|-------------|----------|
| **High** | Official, audited, well-maintained | Context7, GitHub, Filesystem, Docker (official MCP) |
| **Medium** | Community, stable but not audited | Serena, Qdrant, Obsidian |
| **Low** | Unverified, experimental | Custom scripts, third-party servers |
| **Untrusted** | Known security risks | None (always denied) |

---

## Secrets Management

### Resolution Order

```
1. Environment variable           (highest priority, recommended)
2. Encrypted file                 ($MCP_HOME/secrets/<name>.yaml)
3. OS keychain                    (future: Windows Credential Manager, macOS Keychain)
4. Interactive prompt             (fallback, only if terminal is available)
```

### Required Secrets by Server

| Server | Secret | Required | Source |
|--------|--------|----------|--------|
| GitHub | `GITHUB_TOKEN` | Yes | Environment variable |
| PostgreSQL | `DATABASE_URL` | Yes | Environment variable |
| Tavily | `TAVILY_API_KEY` | Yes | Environment variable |

### Secret Storage

Secrets are **never** stored in plaintext configuration files. Instead, configuration files contain references:

```yaml
# In registry.yaml
env:
  GITHUB_TOKEN: "${env.GITHUB_TOKEN}"
```

The platform resolves `"${env.GITHUB_TOKEN}"` to the `GITHUB_TOKEN` environment variable at runtime.

---

## Workspace Boundaries

Filesystem servers are restricted to specific directories:

```yaml
# Per-server filesystem boundaries
allowed_paths:
  - "{{workspace}}/**"                     # Current project
  - "{{workspace}}/../shared/**"           # Adjacent shared directory
denied_paths:
  - "{{workspace}}/.git/**"                # Never expose .git
  - "{{workspace}}/node_modules/**"        # Never expose node_modules
  - "/etc/**"                               # Never expose system files
  - "~/.ssh/**"                             # Never expose SSH keys
```

---

## Audit Logging

Every authorization decision is logged:

```yaml
# $MCP_HOME/logs/audit.log
- timestamp: "2026-07-12T14:30:00.123Z"
  event: tool_call
  server_id: github
  tool: github_create_pr
  args: { title: "Fix bug", repo: "user/repo" }
  agent: claude-code
  decision: ALLOW
  decision_id: "auth_a1b2c3d4"
```

---

## Security Best Practices

### DO
- ✅ Set secrets via environment variables
- ✅ Use the most restrictive profile for your current task
- ✅ Review approval prompts carefully before confirming
- ✅ Keep the platform updated: `mcp update check`
- ✅ Use workspace-bound filesystem access

### DON'T
- ❌ Never store secrets in plaintext config files
- ❌ Never approve high-risk tools without understanding the operation
- ❌ Never run untrusted MCP servers
- ❌ Never expose MCP servers to the public internet

---

## Incident Response

### Severity Levels

| Severity | Example | Action |
|----------|---------|--------|
| **Critical** | Active breach, data exfiltration | `mcp emergency stop` |
| **High** | Suspicious activity, unauthorized access | `mcp stop <server>` + investigate |
| **Medium** | Policy violation | `mcp server disable <server>` + review config |
| **Low** | Failed permission attempt | Log only |

### Quick Reference

```bash
# Emergency stop all servers
mcp emergency stop

# Disable a compromised server
mcp stop docker

# Rollback a suspicious update
mcp update rollback github

# Rotate secrets
# Set new environment variables and restart
mcp restart github
```
