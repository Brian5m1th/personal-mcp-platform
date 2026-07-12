# Engineering Profiles — Personal AI Engineering Platform (MCP)

> Each profile enables only the MCP servers relevant to a specific workflow.
> This reduces memory usage, improves AI agent response quality, and minimizes attack surface.

---

## Profile Management

```bash
# List all profiles
mcp profile list

# Set active profile
mcp profile set backend

# Show current profile details
mcp profile current

# Show specific profile details
mcp profile show devops
```

Profiles are automatically detected based on workspace contents:
- `Cargo.toml` → backend profile
- `package.json` → frontend profile
- `Dockerfile` / `docker-compose.yml` → devops profile
- `*.md` / `docs/` → documentation profile
- `pyproject.toml` → ai-llm profile (if AI-related deps detected)

---

## Full Stack (Default)

**ID:** `full-stack`
**Servers:** 11
**Icon:** layers
**Priority:** 10 (lowest — always overridable)

All servers enabled with sensible limits. Safe for general development.

| Server | Allowed Tools | Denied Tools |
|--------|---------------|--------------|
| Context7 | All | — |
| Serena | All | — |
| GitHub | All | — |
| Playwright | All | — |
| Filesystem | Workspace-bound | `.git`, `node_modules` |
| Sequential Thinking | All | — |
| PostgreSQL | Query only | DROP, DDL |
| Docker | List, logs, compose ps | Destroy |
| Fetch | All | — |
| Memory | All | — |
| Tavily | All | — |

---

## Backend Engineering

**ID:** `backend`
**Servers:** 8
**Icon:** server
**Priority:** 50

Optimized for server-side development, APIs, databases, and containers.

| Server | Allowed Tools | Denied Tools |
|--------|---------------|--------------|
| Context7 | All | — |
| GitHub | All | — |
| PostgreSQL | All | — |
| Docker | List, logs, compose, inspect | Destroy |
| Sequential Thinking | All | — |
| Filesystem | Workspace-bound | `.git` |
| Fetch | All | — |
| Memory | All | — |

**Disabled:** Playwright, Serena

---

## Frontend Engineering

**ID:** `frontend`
**Servers:** 7
**Icon:** layout
**Priority:** 50

Optimized for UI development, browser automation, and design systems.

| Server | Allowed Tools | Denied Tools |
|--------|---------------|--------------|
| Context7 | All | — |
| GitHub | All | — |
| Playwright | All | — |
| Filesystem | Workspace-bound | `.git`, `node_modules` |
| Sequential Thinking | All | — |
| Fetch | All | — |
| Memory | All | — |

**Disabled:** PostgreSQL, Docker, Serena

---

## Infrastructure & DevOps

**ID:** `devops`
**Servers:** 6
**Icon:** cloud
**Priority:** 50

Optimized for cloud, containers, CI/CD, and infrastructure as code.

| Server | Allowed Tools | Denied Tools |
|--------|---------------|--------------|
| GitHub | All | — |
| Docker | List, logs, compose, inspect, images, restart | Destroy all, Prune |
| Sequential Thinking | All | — |
| Filesystem | Workspace + adjacent infra/ | — |
| Fetch | All | — |
| Memory | All | — |

**Disabled:** Playwright, Serena, Context7, PostgreSQL

---

## AI / LLM Engineering

**ID:** `ai-llm`
**Servers:** 7
**Icon:** brain
**Priority:** 50

Optimized for AI model development, RAG, embeddings, and LLM engineering.

| Server | Allowed Tools | Denied Tools |
|--------|---------------|--------------|
| Context7 | All | — |
| Serena | All | — |
| GitHub | All | — |
| Sequential Thinking | All | — |
| Memory | All | — |
| Fetch | All | — |
| Filesystem | Workspace-bound | — |

**Disabled:** Playwright, Docker, PostgreSQL

---

## Security Engineering

**ID:** `security`
**Servers:** 5
**Icon:** shield
**Priority:** 50

Optimized for security auditing, compliance scanning, and code review.
Requires approval for all high-risk operations.

| Server | Allowed Tools | Denied Tools |
|--------|---------------|--------------|
| GitHub | Issues, repos, search, commits only | PR creation, write ops |
| Filesystem | Workspace-bound | — |
| Sequential Thinking | All | — |
| Docker | List, inspect, logs | Restart, stop, compose |
| Fetch | All | — |

**Disabled:** Playwright, Serena, Context7, PostgreSQL, Memory

---

## Documentation Engineering

**ID:** `documentation`
**Servers:** 4
**Icon:** file-text
**Priority:** 50

Optimized for technical writing, documentation generation, and knowledge management.

| Server | Allowed Tools | Denied Tools |
|--------|---------------|--------------|
| Context7 | All | — |
| Filesystem | Restricted to `docs/` and `*.md` | Source code, .git |
| GitHub | Search, read only | PRs, issues |
| Memory | All | — |

**Disabled:** Serena, Playwright, Docker, PostgreSQL, Sequential Thinking, Fetch

---

## Data Engineering

**ID:** `data-engineering`
**Servers:** 5
**Icon:** database
**Priority:** 50

Optimized for data pipelines, ETL, analytics, and database management.

| Server | Allowed Tools | Denied Tools |
|--------|---------------|--------------|
| PostgreSQL | All | — |
| Docker | List, logs, compose ps | — |
| GitHub | All | — |
| Fetch | All | — |
| Filesystem | Workspace-bound | `.git` |

**Disabled:** Serena, Playwright, Context7, Sequential Thinking, Memory

---

## Minimal / Lightweight

**ID:** `minimal`
**Servers:** 3
**Icon:** zap
**Priority:** 90 (highest — overrides all others when selected)

Minimal memory footprint for quick coding sessions and low-resource environments.

| Server | Allowed Tools |
|--------|---------------|
| Filesystem | Workspace-bound |
| GitHub | All |
| Sequential Thinking | All |

**Disabled:** All other servers
