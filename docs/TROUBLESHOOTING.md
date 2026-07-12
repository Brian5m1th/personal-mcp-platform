# Troubleshooting Guide — Personal AI Engineering Platform (MCP)

---

## Installation Issues

### "npx: command not found"

**Cause:** Node.js/npm not installed or not in PATH.

**Solution:**
```powershell
# Install Node.js from https://nodejs.org (v18+)
# Verify installation:
node --version
npm --version
```

### "pip: command not found"

**Cause:** Python/pip not installed or not in PATH.

**Solution:**
```powershell
# Install Python from https://python.org (3.11+)
# Verify installation:
python --version
```

### "mcp: command not found"

**Cause:** Package not installed or Scripts directory not in PATH.

**Solution:**
```powershell
# Install the package
cd C:\workspace\Extras\personal-mcp-platform
pip install -e .

# Verify installation location
pip show mcp-platform

# Add Python Scripts to PATH (if needed)
$env:Path += ";$(python -c 'import site; print(site.USER_SITE)')/Scripts"
```

---

## Runtime Issues

### Server fails to start

```bash
# Check server status
mcp status

# Check logs
mcp health check

# Restart the server
mcp restart github

# If still failing, reinstall
mcp stop github
mcp install github
mcp start github
```

### "Server not found in registry"

**Cause:** Server ID does not exist in `registry.yaml`.

**Solution:**
```bash
# List all available servers
mcp registry list

# Search for similar servers
mcp registry search github
```

### Profile not found

**Cause:** Profile name is incorrect or doesn't exist.

**Solution:**
```bash
# List all available profiles
mcp profile list

# Set a valid profile
mcp profile set full-stack
```

### Permission denied errors

**Cause:** The authorization engine denied the tool call.

**Solution:**
```bash
# Check which profile is active
mcp profile current

# Switch to a less restrictive profile if needed
mcp profile set full-stack

# Add permission override in config.yaml
# See docs/SECURITY.md for details
```

### High latency or slow responses

```bash
# Run benchmark to identify bottlenecks
mcp benchmark

# Check health metrics
mcp health metrics

# Switch to minimal profile (fewer servers = less overhead)
mcp profile set minimal
```

---

## Update Issues

### Update fails

**Cause:** Network issues, incompatible version, or missing permissions.

**Solution:**
```bash
# Check if the server is still running
mcp status

# Rollback to previous version
mcp update rollback github

# Try update again
mcp update apply github
```

### Rollback fails

**Cause:** Backup snapshot is corrupted or missing.

**Solution:**
```bash
# Check available backups
mcp update history

# If backup is missing, reinstall from scratch
mcp stop github
mcp install github
mcp start github
```

---

## Docker Issues

### Container fails to start

**Cause:** Port conflict, missing image, or Docker not running.

**Solution:**
```bash
# Check Docker status
docker ps

# Rebuild containers
docker compose -f docker/docker-compose.yml build

# Check logs
docker compose -f docker/docker-compose.yml logs
```

### nginx proxy not responding on port 8080

**Cause:** Port 8080 already in use.

**Solution:**
```powershell
# Find what's using port 8080
netstat -ano | findstr :8080

# Change port in docker/nginx.conf and docker-compose.yml
```

---

## Logs & Diagnostics

### Viewing Logs

```bash
# Platform logs
type "$env:APPDATA\mcp\logs\platform.log"

# Audit logs
type "$env:APPDATA\mcp\logs\audit.log"

# Server logs (if saved)
type "$env:APPDATA\mcp\logs\servers\github.log"
```

### Health Metrics Database

```bash
# Health metrics are stored in JSONL format
type "$env:APPDATA\mcp\cache\health\metrics.jsonl"

# View via CLI
mcp health metrics --limit 50
```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Executable not found in PATH` | Server binary not installed | Run `mcp install <server>` |
| `Connection closed by server` | Server process crashed | Run `mcp restart <server>` |
| `Permission denied` | Authorization engine blocked the call | Check profile or add override |
| `No servers running` | No servers started | Run `mcp start` |
| `Registry file not found` | Platform not initialized | Run `mcp config show` to initialize |
| `Profile not found` | Invalid profile name | Run `mcp profile list` |

---

## Support

If you encounter issues not covered here:

1. Check the logs: `mcp config show`
2. Run diagnostics: `mcp health check`
3. Open an issue in the repository

---

## Recovery Commands

```bash
# Emergency stop all servers
mcp emergency stop

# Rollback a server update
mcp update rollback <server>

# Reinstall a server from scratch
mcp stop <server>
mcp install <server> --force
mcp start <server>

# Factory reset platform config
# (backup your config first!)
Remove-Item -Recurse $env:APPDATA\mcp
mcp start
```
