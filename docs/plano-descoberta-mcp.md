# Plano: Descoberta e Sincronização de Servidores MCP

## Problema

O `registry.yaml` local contém ~20 servidores fixos. Novos servidores MCP são criados semanalmente. O usuário não tem como:
- Descobrir servidores novos que não estão no registry
- Saber se versões do registry estão desatualizadas
- Atualizar o registry automaticamente

---

## Arquitetura Proposta

### 1. Módulo `mcp_cli/core/discovery.py` (novo)

Motor de descoberta multi-fonte com pontuação e cache.

```
DiscoveryEngine
├── NpmSource       — busca no npm registry
├── GitHubSource    — busca no GitHub (repos + topics)
├── PyPISource      — busca no PyPI
├── SmitherySource  — API do smithery.ai (maior diretório público de MCP)
└── AwesomeSource   — parse de awesome lists do GitHub
```

Cada fonte retorna `list[DiscoveredServer]` com schema normalizado:

```python
@dataclass
class DiscoveredServer:
    id: str
    name: str
    description: str
    source: str           # "npm" | "github" | "pypi" | "smithery" | "awesome"
    source_url: str       # URL direta do pacote/repo
    package: str          # nome do pacote (ex: "@scope/package")
    install_method: str   # "npx" | "uvx" | "pip"
    version: str
    confidence: float     # 0.0 a 1.0 — quão certo é que é um MCP server
    tags: list[str]
```

### 2. Comando `mcp discover` (novo comando)

```
mcp discover search <query>     → busca em todas as fontes
mcp discover list                → lista servidores descobertos (cacheados localmente)
mcp discover sources             → mostra fontes disponíveis e status
mcp discover cache clear         → limpa cache de descoberta
```

### 3. Extensão do `mcp registry`

```
mcp registry sync               → sincroniza registry.yaml com fontes externas
mcp registry update             → verifica versões e atualiza metadados
mcp registry import <id>        → importa servidor descoberto para o registry
```

### 4. Auto-Update do Registry

Mecanismo para detectar que o registry está desatualizado:

```yaml
# registry.yaml
registry_version: '1.0'
updated: '2026-07-12'
auto_sync:
  enabled: true
  sources: ["npm", "github"]
  interval_days: 7
  last_sync: '2026-07-12'
```

Quando `mcp registry list` ou `mcp discover` for executado:
- Se `updated` + `interval_days` < hoje, avisar: `"Registry data is X days old. Run 'mcp registry sync' to update."`
- Opcionalmente, sync automático silencioso em background

---

## Implementação

### Fase 1 — Motor de Descoberta (`discovery.py`)

| Fonte | API | Implementação |
|-------|-----|---------------|
| **npm** | `registry.npmjs.org/-/v1/search?text=keywords:mcp-server&size=250` | `httpx` GET, filtra pacotes com `mcp` no description/keywords |
| **GitHub** | `api.github.com/search/repositories?q=topic:mcp-server&sort=updated` | `httpx` GET com token opcional, filtra por linguagem Node/Python |
| **Smithery** | `registry.smithery.ai/api/v1/packages` | `httpx` GET, parse do JSON |
| **PyPI** | `pypi.org/simple/?q=mcp` | `httpx` GET, parse HTML/JSON |
| **Awesome List** | `raw.githubusercontent.com/.../awesome-mcp-servers/README.md` | Parse de links em markdown |

Pipeline de confiança:
```
Cada fonte → parse → normalização → merge/dedup → scoring → resultado
```

Algoritmo de scoring:
- NPM pacote com description contendo "MCP server" = 0.9
- GitHub repo com topic `mcp-server` + readme mentioning MCP = 0.8
- Smithery verified = 1.0
- Awesome list listed = 0.7

### Fase 2 — Sincronização com Registry

```
mcp registry sync
  ├── 1. Fetch de todas as fontes
  ├── 2. Merge com registry.yaml existente
  │    ├── server novo → adiciona com plan: "discovered"
  │    ├── server existente → atualiza version, updated
  │    └── server removido → marca como "deprecated"
  └── 3. Salva registry.yaml + backup
```

### Fase 3 — CLI Commands

```python
# mcp_cli/commands/discover.py
@app.command()
def discover_cmd(action, query):
    ...
```

```python
# mcp_cli/commands/registry_cmd.py — extensão
def registry_cmd(action, query):
    ...
    elif action == "sync":
        asyncio.run(_run_sync())
    elif action == "import":
        asyncio.run(_run_import(query))
```

### Fase 4 — Testes

| Teste | Descrição |
|-------|-----------|
| `test_npm_search` | Mock HTTP, verifica parse de resposta npm |
| `test_github_search` | Mock HTTP, verifica parse de resposta GitHub |
| `test_discovery_merge` | Merge de descoberta com registry existente |
| `test_scoring` | Verifica confidence scores |
| `test_auto_update_check` | Verifica detecção de registry desatualizado |
| `test_cli_discover` | Teste de integração do comando discover |

---

## Dependências Externas

- `httpx` — já existe no projeto
- Nenhuma dependência nova necessária

## Arquivos a Criar/Modificar

| Arquivo | Tipo |
|---------|------|
| `mcp_cli/core/discovery.py` | Novo — motor de descoberta |
| `mcp_cli/commands/discover.py` | Novo — comando CLI `mcp discover` |
| `mcp_cli/commands/registry_cmd.py` | Modificar — adicionar `sync`, `import` |
| `mcp_cli/__main__.py` | Modificar — registrar `discover` |
| `mcp_cli/core/updater.py` | Modificar — adicionar auto-update check |
| `registry.yaml` | Modificar — adicionar `auto_sync` field |
| `tests/unit/test_discovery.py` | Novo — testes do discovery |
| `tests/unit/test_updater.py` | Novo — testes do auto-update |

---

## Exemplos de Uso Futuro

```bash
# Buscar servidores MCP relacionados a banco de dados
mcp discover search database

# Sincronizar registry com internet
mcp registry sync

# Importar servidor descoberto para o registry local
mcp registry import supabase

# Verificar servidores que têm atualização disponível
mcp registry update
```
