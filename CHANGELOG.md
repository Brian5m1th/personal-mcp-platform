# Changelog

## v0.1.0 (2026-07-12)

### Added
- Initial release: MCP Platform CLI (`mcp`)
- Server installation via npx, npm, pip, uvx
- Server lifecycle management (start/stop/restart/status/emergency)
- 9 engineering profiles (full-stack, backend, frontend, devops, ai-llm, security, documentation, data-engineering, minimal)
- Agent config generation (Claude Code, OpenCode, Cursor, VS Code, Antigravity)
- Project linking (`mcp project add/remove/status/list`)
- Health monitoring with metrics storage
- Update management with backup and rollback
- Server registry with 15+ MCP servers
- Docker Compose stack with 11 containerized servers
- Cross-platform installers (PowerShell + Bash)
- Comprehensive documentation suite (8 docs)

## v0.1.1 (unreleased)

### Fixed
- `mcp update apply` now actually runs npm/pip install instead of just creating backup
- Removed dead code in transport.py (sync subprocess in async context)
- Migrated transport.py to fully async subprocess (asyncio.create_subprocess_exec)
- Migrated install.py to async subprocess
- Added timeout to STDIO request reads (30s)
- Fixed nginx.conf health endpoint (add_header before return)

### Added
- `mcp secrets` command (list/set/show/check)
- `mcp logs` command (view/tail server logs)
- `mcp compose` command (up/down/status/logs/restart for Docker stack)
- Periodic health checks with configurable interval
- Health metrics recording now works (record_health wired to health_check_all)
- Interactive approval for high-risk tool operations
- Profile auto-detection on `mcp start`
- Antigravity support in `mcp project add`
- Real Cursor config format (separate from VS Code)
- Tavily MCP server in registry
- Health/benchmark metadata for phase-2 servers (qdrant, obsidian, n8n, cloudflare)
- Fixed Serena requirements (uv→npm)
- Proper tier filtering (Tier 1/2/3)
- Missing `__init__.py` files
- pytest configuration with asyncio support
- ruff, black, mypy configuration

### Changed
- OpenCode config format: `mcpServers` → `mcp.<id>.type="local"` + flat command array
- OpenCode config path: `.opencode.json` → `.opencode/opencode.json`
- Serena install: `uvx serena-mcp` → `npx serena-slim`
