# Upgrade & Rollback Guide — Personal AI Engineering Platform (MCP)

---

## Overview

The platform includes an automated update system that handles:

- **Version checking** — queries npm/pypi registry for latest versions
- **Compatibility validation** — verifies the new version works before committing
- **Automatic backups** — snapshots config before every update
- **Safe rollback** — reverts to previous version if update fails
- **Update history** — full audit trail of all version changes

---

## Update Policies

Each server has an `update_policy` that controls how aggressively updates are applied:

| Policy | Behavior | Example |
|--------|----------|---------|
| `patch` | Auto-apply patch versions (1.0.x) | Bug fixes, security patches |
| `minor` | Auto-apply minor versions (1.x.0) | New features, non-breaking |
| `major` | Require confirmation for major (x.0.0) | Breaking changes |
| `manual` | Never auto-update | Critical servers requiring validation |
| `pinned` | Version is locked, never update | Servers with incompatible dependencies |

---

## Checking for Updates

```bash
# Check all servers for available updates
mcp update check
```

**Output:**
```
Checking for updates...
┌─────────────────────────────────────────────────┐
│ Server   │ Current   │ Latest   │ Update   │Policy│
├──────────┼───────────┼──────────┼──────────┼─────┤
│ context7 │ 3.2.3     │ 3.3.0    │ Available│minor│
│ github   │ 2025.4.8  │ 2025.4.8│ Up-to-d. │minor│
│ filesys. │ 2026.7.10 │2026.7.10│ Up-to-d. │patch│
│ seq-thk  │ 2026.7.4  │ 2026.7.5│ Available│minor│
└──────────┴───────────┴──────────┴──────────┴─────┘
```

```bash
# Check a specific server
mcp update check github
```

---

## Applying Updates

```bash
# Apply all pending updates (auto-backup before each)
mcp update apply
```

### What happens during an update:

1. **Backup** — Creates a snapshot of the current server config and version
2. **Stop** — Gracefully stops the running server
3. **Install** — Downloads and installs the new version
4. **Validate** — Verifies:
   - `tools/list` responds correctly
   - Health check passes
   - Previously known tools still exist
   - Performance metrics within acceptable range
5. **Update Registry** — Records the new version in `registry.yaml`
6. **Start** — Restarts the server with the new version
7. **Generate Configs** — Updates agent configuration files

```bash
# Apply update for a single server
mcp update apply github
```

---

## Rollback

If an update causes issues, rollback is straightforward:

```bash
# Rollback the most recent update
mcp update rollback github

# Rollback to a specific version
mcp update rollback github --version 2025.4.8
```

### What happens during a rollback:

1. **Find Backup** — Locates the backup snapshot for the target version
2. **Stop** — Stops the current (broken) server
3. **Restore** — Restores config files from backup
4. **Reinstall** — Installs the previous version
5. **Validate** — Verifies health and tool availability
6. **Start** — Restarts with the previous version

### If rollback fails:

```bash
# If rollback itself fails, the system automatically
# restores the new version (pre-rollback state)

# Then try a clean reinstall:
mcp stop github
mcp install github
mcp start github
```

---

## Update History

```bash
# View full update history
mcp update history

# View history for a specific server
mcp update history
```

**Output:**
```
┌────────────────────────────────────────────────────────────┐
│                     Update History                          │
├──────────────────────┬─────────┬──────┬──────┬────────────┤
│ Date                 │ Server  │ From │ To   │ Status     │
├──────────────────────┼─────────┼──────┼──────┼────────────┤
│ 2026-07-12T14:30:00  │ github  │1.5.2 │1.6.0 │ completed  │
│ 2026-07-10T09:15:00  │ context7│3.2.0 │3.2.3 │ rolled_back│
│ 2026-07-08T16:45:00  │ context7│3.1.0 │3.2.0 │ completed  │
└──────────────────────┴─────────┴──────┴──────┴────────────┘
```

---

## Backup Management

Backups are stored in `$MCP_HOME/backups/`:

```
$MCP_HOME/backups/
├── manifest.yaml                 # Backup index
├── bk_20260712_143000_github/   # Snapshot for github update
│   └── github.yaml
└── bk_20260710_091500_context7/
    └── context7.yaml
```

### Backup retention:

- Last 3 backups per server are kept
- Older backups are automatically pruned
- Manual backups can be preserved indefinitely

```bash
# Prune old backups (keeps last 3 per server)
# This happens automatically during updates
```

---

## Version Pinning

If a specific version is working well and you don't want it updated:

```yaml
# In config.yaml
permissions:
  overrides:
    - server: "github"
      property: "update_policy"
      value: "pinned"
```

Or modify the registry entry directly:

```yaml
# registry.yaml
- id: github
  install:
    update_policy: pinned   # Never auto-update
```

---

## Emergency Procedures

### Rollback All Servers

```bash
# If a mass update causes system-wide issues:
mcp emergency stop
mcp update rollback context7
mcp update rollback github
mcp update rollback filesystem
mcp start
```

### Restore from Scratch

```bash
# If the platform itself is corrupted:
# 1. Backup your config
Copy-Item -Recurse $env:APPDATA\mcp\* C:\backups\mcp-backup\

# 2. Reinstall the CLI
pip install -e C:\workspace\Extras\personal-mcp-platform

# 3. Restore config from backup
Copy-Item -Recurse C:\backups\mcp-backup\* $env:APPDATA\mcp\

# 4. Restart
mcp start
```

### Factory Reset

```bash
# Reset the platform to factory defaults
Remove-Item -Recurse $env:APPDATA\mcp\
mcp start
```

---

## Updating the Platform CLI

```bash
# Update the platform itself (not MCP servers — those use mcp update)
cd C:\workspace\Extras\personal-mcp-platform
git pull
pip install -e .

# Or if distributed via pip:
pip install --upgrade mcp-platform
```

---

## Best Practices

1. **Check for updates regularly**: `mcp update check` (or enable auto-check in config)
2. **Review changelogs** before applying major updates
3. **Test critical servers first** in a non-production context
4. **Keep backups** — the platform auto-creates them, but periodic manual backups are recommended
5. **Pin critical servers** — if a server is essential to your workflow, pin its version
6. **Rollback immediately** if you notice any issues after an update
