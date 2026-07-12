# Personal AI Engineering Platform — MCP

> **Universal MCP Infrastructure** for AI-Assisted Development.
> Works with Claude Code, OpenCode, Antigravity, Cursor, VS Code AI.
> Reusable across every software project you develop.

---

## 📋 Índice

- [O que é?](#o-que-é)
- [Quick Start](#quick-start)
- [Para Usuários](#para-usuários)
  - [Instalação](#instalação)
  - [Comandos](#comandos)
  - [Perfis](#perfis)
  - [Vincular a um Projeto](#vincular-a-um-projeto)
  - [Adicionar Servidor Customizado](#adicionar-servidor-customizado)
- [Para Desenvolvedores](#para-desenvolvedores)
  - [Arquitetura](#arquitetura)
  - [Repositório](#repositório)
  - [Adicionar Servidor ao Registry](#adicionar-servidor-ao-registry)
  - [Testes](#testes)
- [Servidores Disponíveis](#servidores-disponíveis)
- [Solução de Problemas](#solução-de-problemas)
- [Documentação](#documentação)

---

## O que é?

Esta plataforma gerencia **servidores MCP** (Context7, GitHub, Filesystem, Playwright, PostgreSQL, Docker, etc.)
e disponibiliza as ferramentas deles para **qualquer agente de IA compatível com MCP**.

| Agente | Arquivo de Config |
|--------|-------------------|
| **OpenCode** | `.opencode/opencode.json` no projeto |
| **Claude Code** | `~/.claude.json` |
| **Cursor** | `~/.cursor/mcp.json` |
| **VS Code AI** | `.vscode/settings.json` no projeto |
| **Antigravity** | `~/.antigravity/mcp.json` |

### Como funciona

```
Voce executa:  mcp start
                   │
          Servidores MCP rodando
          (GitHub, Filesystem, etc.)
                   │
     OpenCode / Claude Code / Cursor
          usam as ferramentas
                   │
         Codigo mais inteligente,
         documentacao viva,
         PRs automaticos,
         testes E2E
```

### Conceito

Em vez de configurar MCP manualmente em cada projeto, você mantém **um único lugar** (`~/.config/mcp/`)
e usa `mcp project add` para vincular qualquer projeto à plataforma.

```
Projeto A (K.A.O.S) ──┐
Projeto B (Wakanda) ──┤── mcp platform (um unico lugar)
Projeto C (API) ──────┘
```

---

## Quick Start

### Windows (PowerShell)

```powershell
cd C:\workspace\Extras\personal-mcp-platform
.\scripts\install.ps1                           # Instala servidores
mcp project add --agent opencode                # Vincula ao projeto
mcp start                                       # Inicia servidores
```

### Linux / macOS

```bash
cd ~
git clone https://github.com/Brian5m1th/personal-mcp-platform.git
cd personal-mcp-platform
./scripts/install.sh
mcp project add --agent opencode
mcp start
```

### Docker (qualquer sistema)

```bash
docker compose -f docker/docker-compose.yml --profile full up -d
```

---

# Para Usuários

## Instalação

### Pré-requisitos

| Programa | Versão | Verificar |
|----------|--------|-----------|
| **Python** | ≥ 3.11 | `python --version` |
| **Node.js** | ≥ 18 | `node --version` |
| **npm** | ≥ 9 | `npm --version` |
| **Git** | ≥ 2 | `git --version` |

### Métodos de Instalação

| Método | Comando | Quando usar |
|--------|---------|-------------|
| **PowerShell** (Windows) | `.\scripts\install.ps1` | Recomendado para Windows |
| **Shell Script** (Linux/macOS) | `./scripts/install.sh` | Recomendado para Linux/macOS |
| **Pip** (qualquer OS) | `pip install -e .` | Quando ja tem Python |
| **Docker** (qualquer OS) | `docker compose up -d` | Para ambientes isolados |

### Pós-instalação

**1. Token do GitHub (obrigatório para GitHub MCP):**

```powershell
# Windows (torna permanente):
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "ghp_seu_token_aqui", "User")

# Linux/macOS (adiciona ao ~/.bashrc):
echo 'export GITHUB_TOKEN="ghp_seu_token_aqui"' >> ~/.bashrc
```

**2. Verificar instalação:**

```bash
mcp config show        # Caminhos da plataforma
mcp registry list      # Servidores disponiveis
mcp profile list       # Perfis de engenharia
```

**3. Vincular projeto e iniciar:**

```bash
cd C:\workspace\SeuProjeto
mcp project add --agent opencode
mcp start
```

---

## Comandos

### Gerenciamento de Servidores

| Comando | Descrição |
|---------|-----------|
| `mcp start` | Inicia todos os servidores do perfil ativo |
| `mcp start --detach` | Inicia em background (PID tracking) |
| `mcp stop [server]` | Para servidor(es) |
| `mcp status` | Mostra status de todos |
| `mcp restart <server>` | Reinicia um servidor |
| `mcp emergency stop` | Para TUDO imediatamente |

### Instalação

| Comando | Descrição |
|---------|-----------|
| `mcp install github` | Instala um servidor especifico |
| `mcp install --tier 1` | Instala todos do Tier 1 (core) |
| `mcp install --tier 2` | Instala todos do Tier 2 |

### Projetos

| Comando | Descrição |
|---------|-----------|
| `mcp project add` | Vincula MCP ao projeto atual |
| `mcp project remove` | Desvincula MCP do projeto |
| `mcp project list` | Lista todos os projetos vinculados |
| `mcp project status` | Status do vinculo do projeto |
| `mcp project add-server` | Adiciona servidor MCP customizado |

### Perfis

| Comando | Descrição |
|---------|-----------|
| `mcp profile list` | Lista todos os perfis |
| `mcp profile set <nome>` | Ativa um perfil |
| `mcp profile current` | Mostra perfil ativo |

### Atualizações

| Comando | Descrição |
|---------|-----------|
| `mcp update check` | Verifica atualizações disponiveis |
| `mcp update apply` | Aplica atualizações (com backup) |
| `mcp update rollback <s>` | Reverte atualização |
| `mcp update history` | Historico de atualizacoes |

### Monitoramento

| Comando | Descrição |
|---------|-----------|
| `mcp health check` | Saude dos servidores |
| `mcp health metrics` | Metricas detalhadas |
| `mcp health summary` | Resumo de saude |
| `mcp benchmark [srv]` | Benchmark de performance |

### Configuração

| Comando | Descrição |
|---------|-----------|
| `mcp config show` | Mostra configuracao atual |
| `mcp config edit` | Abre configuracao no editor |
| `mcp registry list` | Lista servidores do catalogo |
| `mcp registry search <q>` | Busca servidores |
| `mcp registry info <id>` | Detalhes de um servidor |
| `mcp generate <agent>` | Gera config para Claude/OpenCode/VS Code/Cursor |
| `mcp --version` | Versao instalada |

---

## Perfis

Cada perfil ativa **apenas os servidores relevantes** para aquela area de trabalho:

| Perfil | Foco | Servidores | Como Ativar |
|--------|------|:-----------:|-------------|
| `full-stack` | Geral (padrão) | 10 | `mcp profile set full-stack` |
| `backend` | APIs, banco, Docker | 8 | `mcp profile set backend` |
| `frontend` | UI, navegador | 7 | `mcp profile set frontend` |
| `devops` | Cloud, CI/CD, infra | 6 | `mcp profile set devops` |
| `ai-llm` | IA, RAG, LLMs | 7 | `mcp profile set ai-llm` |
| `security` | Auditoria | 5 | `mcp profile set security` |
| `documentation` | Documentação | 4 | `mcp profile set documentation` |
| `data-engineering` | Dados, ETL | 5 | `mcp profile set data-engineering` |
| `minimal` | Leve (3 servidores) | 3 | `mcp profile set minimal` |

A plataforma também **detecta automaticamente** o perfil ideal baseado no projeto:
- `Dockerfile` → perfil `devops`
- `package.json` → perfil `frontend`
- `Cargo.toml` / `pyproject.toml` → perfil `backend`

---

## Vincular a um Projeto

```bash
# Vincular (dentro do diretorio do projeto)
cd C:\workspace\MeuProjeto
mcp project add --agent opencode

# Verificar vinculo
mcp project status

# Listar todos os projetos vinculados
mcp project list

# Desvincular
mcp project remove
```

Cada projeto pode usar um agente diferente:
```bash
mcp project add --agent opencode     # OpenCode
mcp project add --agent claude-code  # Claude Code
mcp project add --agent cursor       # Cursor
mcp project add --agent vscode       # VS Code
```

---

## Adicionar Servidor Customizado

### Método 1 — Pelo CLI (recomendado)

```bash
# Adicionar um servidor npm:
mcp project add-server --name meu-serv --cmd npx --args -y,@pacote/meu-serv

# Adicionar um script Python:
mcp project add-server --name meu-serv --cmd python --args -m,meu_servidor

# Adicionar um executavel local:
mcp project add-server --name meu-serv --cmd node --args servidor.js
```

### Método 2 — Editando o arquivo diretamente

Abra `.opencode/opencode.json` no seu projeto e adicione no bloco `mcp`:

```json
{
  "mcp": {
    "meu-servidor": {
      "type": "local",
      "command": ["npx", "-y", "@pacote/meu-servidor"],
      "enabled": true
    }
  }
}
```

Depois reinicie o OpenCode.

### Método 3 — Adicionar ao Registry (para usar em varios projetos)

Edite `registry.yaml` e adicione uma entrada seguindo o schema existente.
Depois instale e vincule:

```bash
mcp install meu-servidor
mcp generate opencode
```

---

# Para Desenvolvedores

## Arquitetura

```
Agente IA (OpenCode, Claude Code, etc.)
         │  STDIO
         ▼
┌─────────────────────────────┐
│    Transport Layer           │
│  STDIO · HTTP · SSE · WS    │
├─────────────────────────────┤
│    Server Manager            │
│  Lifecycle · State Machine   │
├─────────────────────────────┤
│    Authorization Engine      │
│  Agent × Profile × Risk     │
├─────────────────────────────┤
│    MCP Servers               │
│  GitHub · Filesystem · ...  │
└─────────────────────────────┘
```

Documentação completa da arquitetura: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

### Estrutura do Projeto

```
personal-mcp-platform/
├── mcp_cli/                    # CLI em Python (codigo fonte)
│   ├── __main__.py             # Entry point (16 comandos)
│   ├── core/                   # Biblioteca principal
│   │   ├── config.py           # Path resolution, YAML load/save
│   │   ├── transport.py        # STDIO/HTTP/SSE/WS + TransportFactory
│   │   ├── server_manager.py   # Maquina de estados (12 estados)
│   │   ├── permissions.py      # Engine de autorizacao (6 dimensoes)
│   │   ├── profiles.py         # 9 perfis de engenharia
│   │   ├── secrets.py          # Resolucao de secrets
│   │   ├── health.py           # Monitor de saude (JSONL)
│   │   ├── updater.py          # Version check + rollback
│   │   └── generator.py        # Geracao de configs para agentes
│   └── commands/               # Handlers dos comandos CLI
├── docker/                     # Docker Compose + nginx proxy
├── scripts/                    # Installers (PowerShell, Bash)
├── docs/                       # 8 documentos de documentacao
├── registry.yaml               # Catalogo de servidores
├── profiles/                   # Definicoes dos perfis
├── tests/                      # Testes unitarios
├── config/                     # Configuracao padrao
├── CHANGELOG.md                # Historico de versoes
└── pyproject.toml              # Pacote Python
```

---

## Adicionar Servidor ao Registry

Para adicionar um novo servidor MCP ao catalogo oficial:

**1. Verificar o pacote:**

```bash
npm view @pacote/do-servidor version
npx -y @pacote/do-servidor
```

**2. Adicionar ao `registry.yaml`:**

```yaml
- id: meu-servidor
  name: "Meu Servidor MCP"
  version: "1.0.0"
  category: custom
  maturity: experimental
  protocol:
    default: stdio
    transports:
      - type: stdio
        command: "npx"
        args: ["-y", "@pacote/do-servidor"]
  permissions:
    filesystem: none
    network: https-outbound
    shell: false
    secrets: []
  requirements:
    node: ">=18"
    npm: true
  install:
    method: npx
    command: "npx @pacote/do-servidor"
```

**3. Testar:**

```bash
mcp install meu-servidor
mcp start meu-servidor
mcp status
```

---

## Testes

```bash
# Instalar dependencias de teste
pip install pytest pytest-asyncio

# Rodar todos os testes
pytest tests/

# Cobertura
pip install pytest-cov
pytest --cov=mcp_cli tests/
```

---

# Servidores Disponíveis

### Tier 1 — Core (instalação padrão)
| Servidor | Versão | Função | Risco |
|----------|--------|--------|:-----:|
| Context7 | 3.2.3 | Documentação viva de APIs/frameworks | Baixo |
| Serena | 1.10.0 | Navegação semântica de código | Baixo |
| GitHub | 2025.4.8 | Issues, PRs, commits, busca | Médio |
| Playwright | 0.0.78 | Automação de navegador | Alto |
| Filesystem | 2026.7.10 | Leitura/escrita segura de arquivos | Alto |
| Sequential Thinking | 2026.7.4 | Raciocínio estruturado | Nenhum |

### Tier 2 — Enhanced (sob demanda)
| Servidor | Versão | Função | Risco |
|----------|--------|--------|:-----:|
| PostgreSQL | 0.6.2 | Gerenciamento de banco | Alto |
| Docker | 2026.7.4 | Gerenciamento de containers | Crítico |
| Fetch | 1.1.2 | Pesquisa na web | Baixo |
| Memory | 2026.7.4 | Memória persistente | Baixo |

### Tier 3 — Expert
| Servidor | Versão | Função |
|----------|--------|--------|
| Tavily | 1.0.0 | Pesquisa web profissional |

---

# Solução de Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| `mcp: command not found` | CLI nao instalado | `pip install -e .` |
| `npx: command not found` | Node.js nao instalado | Instalar de https://nodejs.org |
| `Connection closed by server` | Caminho com espacos | Use aspas no path |
| `Server not in registry` | ID errado | `mcp registry list` |
| `Cannot transition from registered` | Servidor nao instalado | `mcp install <server>` |
| `GITHUB_TOKEN not set` | Token faltando | `$env:GITHUB_TOKEN = "ghp_..."` |
| Servidor aparece desabilitado | Docker/DB nao disponivel | Inicie o Docker ou sete DATABASE_URL |
| OpenCode nao ve os servidores | Arquivo no lugar errado | Verifique `.opencode/opencode.json` |

---

# Documentação

| Documento | Para quem | Conteúdo |
|-----------|-----------|----------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Desenvolvedores | C4 diagrams, transport, permission model, lifecycles |
| [`docs/INSTALLATION.md`](docs/INSTALLATION.md) | Usuários | Instalação passo a passo |
| [`docs/USAGE.md`](docs/USAGE.md) | Usuários | Todos os comandos com exemplos |
| [`docs/PROFILES.md`](docs/PROFILES.md) | Usuários | Detalhes dos 9 perfis |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Todos | Modelo de segurança, secrets, auditoria |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | Usuários | Solução de problemas |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | Desenvolvedores | Guia de contribuição, adicionar comandos |
| [`docs/UPGRADE.md`](docs/UPGRADE.md) | Usuários | Atualizações e rollback |

---

## Suporte

- **Issues:** https://github.com/Brian5m1th/personal-mcp-platform/issues
- **Logs da plataforma:** `%APPDATA%/mcp/logs/` (Windows), `~/.config/mcp/logs/` (Linux/macOS)
- **Diagnóstico rápido:** `mcp health check`

---

## Licença

MIT — Livre para uso pessoal e comercial.
