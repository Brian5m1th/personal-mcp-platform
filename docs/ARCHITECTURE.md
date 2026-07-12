# Architecture — Personal AI Engineering Platform (MCP)

> System architecture documentation for the MCP Platform.
> See also: `docs/adr/` (in the K.A.O.S repo) for detailed ADRs.

---

## 1. System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI CODING AGENTS                               │
│  Claude Code · OpenCode · Antigravity · Cursor · VS Code AI      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ STDIO / HTTP / SSE
┌──────────────────────────▼──────────────────────────────────────┐
│                    MCP PLATFORM CLI (mcp)                        │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    Core Library (libmcp)                   │    │
│  │  ServerManager · TransportLayer · AuthorizationEngine    │    │
│  │  RegistryManager · ProfileManager · SecretsManager       │    │
│  │  UpdateManager · HealthMonitor · AgentConfigGenerator    │    │
│  │  AuditLogger                                             │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ manages
┌──────────────────────────▼──────────────────────────────────────┐
│                    MCP SERVER PROCESSES                           │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐  │
│  │ Context7 │ │  Serena  │ │  GitHub  │ │Playwright│ │Filesys│  │
│  │ (stdio)  │ │ (stdio)  │ │ (stdio)  │ │ (stdio)  │ │(stdio)│  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐  │
│  │  SeqThink│ │ Postgres │ │  Docker  │ │  Fetch   │ │Memory │  │
│  │ (stdio)  │ │ (stdio)  │ │ (stdio)  │ │ (stdio)  │ │(stdio)│  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Transport Abstraction

```
Agent/Client
     │
     ▼
┌─────────────────────────────────────────────┐
│           Transport Abstraction Layer        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  STDIO   │  │   SSE    │  │   HTTP   │  │
│  │ Transport│  │ Transport│  │ Transport│  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼──────────────┼──────────────┼───────┘
        │              │              │
        ▼              ▼              ▼
┌─────────────────────────────────────────────┐
│              MCP Server (JSON-RPC 2.0)        │
│  tools/list · tools/call · initialize        │
└─────────────────────────────────────────────┘
```

The transport layer is **pluggable** — new transports can be added via `TransportFactory` without modifying any business logic.

---

## 3. Permission Model (6 Dimensions)

```
Agent Identity ──► Permission Profile ──► Authorization Engine ──► Decision
                          ▲                       ▲
                          │                       │
                  Tool Risk Level ─────── Server Trust Level
                          │                       │
                          ▼                       ▼
                Workspace Context ──────── Approval Policy
```

### Decision Matrix

| Trust \ Risk | None | Low | Medium | High | Critical |
|-------------|------|-----|--------|------|----------|
| **High** | ALLOW | ALLOW | ALLOW | APPROVAL | DENY |
| **Medium** | ALLOW | ALLOW | APPROVAL | DENY | DENY |
| **Low** | DENY | DENY | DENY | DENY | DENY |
| **Untrusted** | DENY | DENY | DENY | DENY | DENY |

---

## 4. Configuration Hierarchy

```
1. Environment Variables          (MCP_HOME, MCP_PROFILE, GITHUB_TOKEN...)
2. Per-Project Local Config       ($PROJECT/.mcp/config.yaml)
3. Active Profile                 ($MCP_HOME/profiles/<name>.yaml)
4. Global User Config             ($MCP_HOME/config.yaml)
5. Platform Defaults              (compiled into the CLI)
```

---

## 5. Server Lifecycle

```
REGISTERED → INSTALLING → INSTALLED → STARTING → RUNNING → HEALTHY
                                                          ↓
                                                    DEGRADED
                                                          ↓
                                                    STOPPING → STOPPED
                                                                 ↓
                                                           UNINSTALLED
```

Automatic restart on failure (up to 3 attempts with exponential backoff).

---

## 6. Update/Rollback Flow

```
mcp update apply
  → Check versions against npm/pypi registry
  → Create backup snapshot (config files + version metadata)
  → Download and install new version
  → Validate: tools/list responds, health check passes
  → Update registry.yaml version
  → Generate updated agent configs

mcp update rollback <server>
  → Load backup snapshot
  → Stop current server
  → Restore previous version files
  → Restart server
  → Verify health
```

---

## 7. Secrets Resolution

```
1. Environment variable         (e.g., GITHUB_TOKEN)
2. Encrypted file               ($MCP_HOME/secrets/<name>.yaml, encrypted with age)
3. OS keychain                  (future — macOS Keychain, Windows Credential Manager)
4. Interactive prompt            (fallback — asks user for value)
```

---

## 8. Directory Layout

```
$MCP_HOME/
├── registry.yaml           # Server catalog (single source of truth)
├── config.yaml             # User configuration
├── active_profile.yaml     # Current active profile
├── profiles/               # Engineering profile definitions
├── servers/                # Per-server runtime config
├── secrets/                # Encrypted secrets
├── cache/
│   ├── tools/              # Cached tool lists
│   ├── schemas/            # Cached input schemas
│   └── health/             # Health metrics (JSONL)
├── logs/
│   ├── platform.log        # Platform operations
│   ├── audit.log           # Authorization events
│   └── servers/            # Per-server logs
├── downloads/              # Downloaded binaries
├── templates/              # Agent config templates
├── backups/                # Update snapshots
│   └── manifest.yaml       # Backup index
└── disaster-recovery.yaml  # Recovery procedures
```

---

## 9. Technology Stack

| Component | Technology | Why |
|-----------|------------|-----|
| CLI | Python (Typer) | Cross-platform, rich ecosystem, consistent with K.A.O.S |
| Config | YAML | Human-readable, diffable, MCP ecosystem standard |
| Transport | stdlib asyncio + httpx | Async IO for concurrent server management |
| Secrets | age (age-n ago) | Simple cross-platform encryption |
| Container | Docker Compose | Consistent server environment |
| CLI distribution | pip / uv | Standard Python distribution |
| Health DB | JSONL (append-only) | Simple, no dependencies |
| Templates | Jinja2 (via Python) | Flexible agent config generation |
