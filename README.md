# Personal AI Engineering Platform — MCP

> Universal MCP Infrastructure for AI-Assisted Development.
> Works with Claude Code · OpenCode · Antigravity · Cursor · VS Code AI.
> Reusable across every software project you develop.

---

## Quick Start

### 🪟 Windows

```powershell
# 1. Abrir PowerShell como Administrador e executar:
cd C:\workspace\Extras\personal-mcp-platform
.\scripts\install.ps1

# 2. Adicionar ao PATH (executar apenas uma vez):
$env:Path += ";$env:APPDATA\Python\Scripts"
[Environment]::SetEnvironmentVariable("Path", "$env:Path;$env:APPDATA\Python\Scripts", "User")

# 3. Adicionar ao seu projeto:
cd C:\workspace\SeuProjeto
mcp project add --agent opencode

# 4. Iniciar servidores:
mcp start
```

### 🐧 Linux

```bash
# 1. Clonar e instalar:
cd ~
git clone https://github.com/Brian5m1th/personal-mcp-platform.git
cd personal-mcp-platform
pip install -e .

# 2. Executar setup:
./scripts/install.sh

# 3. Adicionar ao seu projeto:
cd ~/workspace/SeuProjeto
mcp project add --agent opencode

# 4. Iniciar servidores:
mcp start
```

### 🍎 macOS

```bash
# 1. Clonar e instalar:
cd ~
git clone https://github.com/Brian5m1th/personal-mcp-platform.git
cd personal-mcp-platform
pip install -e .

# 2. Executar setup:
./scripts/install.sh

# 3. Adicionar ao seu projeto:
cd ~/workspace/SeuProjeto
mcp project add --agent opencode

# 4. Iniciar servidores:
mcp start
```

### 🐳 Docker (qualquer sistema)

```bash
git clone https://github.com/Brian5m1th/personal-mcp-platform.git
cd personal-mcp-platform
docker compose -f docker/docker-compose.yml --profile full up -d
```

---

## O que é isso?

Uma **Plataforma Pessoal de Engenharia de IA** baseada no Model Context Protocol (MCP).

Ela gerencia servidores MCP (Context7, GitHub, Filesystem, Playwright, PostgreSQL, Docker, etc.)
e disponibiliza as ferramentas deles para qualquer agente de IA compatível com MCP:

- ✅ **Claude Code** — usa os servidores via `~/.claude.json`
- ✅ **OpenCode** — usa via `.opencode.json` no projeto
- ✅ **Cursor** — usa via `.cursor/mcp.json`
- ✅ **VS Code AI** — usa via `.vscode/settings.json`
- ✅ **Antigravity** — usa via `~/.antigravity/mcp.json`

Em vez de configurar MCP manualmente em cada projeto, você mantém **um único lugar**
e usa `mcp project add` para vincular qualquer projeto à plataforma.

---

## Instalação Completa

### Pré-requisitos

| Programa | Versão Mínima | Verificar Instalação |
|----------|---------------|----------------------|
| **Python** | 3.11+ | `python --version` |
| **Node.js** | 18+ | `node --version` |
| **npm** | 9+ | `npm --version` |
| **Git** | 2+ | `git --version` |
| **Docker** (opcional) | 24+ | `docker --version` |

### Método 1 — PowerShell (Windows, recomendado)

```powershell
# Instalação completa com um comando:
.\scripts\install.ps1

# Opções:
.\scripts\install.ps1 -ServerId github     # Instalar apenas um servidor
.\scripts\install.ps1 -Profile minimal      # Instalar com perfil minimal
.\scripts\install.ps1 -DryRun               # Preview sem instalar
.\scripts\install.ps1 help                  # Ajuda completa
```

O instalador faz tudo automaticamente:
1. Verifica pré-requisitos (Node, npm, Python, Git)
2. Cria estrutura de diretórios em `%APPDATA%/mcp/`
3. Instala servidores Tier 1 (Context7, GitHub, Filesystem, Sequential Thinking)
4. Gera arquivos de configuração para Claude Code e OpenCode
5. Gera todos os 9 perfis de engenharia

### Método 2 — Shell Script (Linux/macOS)

```bash
# Dar permissão de execução:
chmod +x scripts/install.sh

# Executar:
./scripts/install.sh

# Opções:
./scripts/install.sh --server github
./scripts/install.sh --profile minimal
./scripts/install.sh --dry-run
```

### Método 3 — Pip (qualquer sistema)

```bash
# Instalar o CLI via pip:
cd personal-mcp-platform
pip install -e .

# Verificar instalação:
mcp --version

# Copiar registry e perfis para o diretório da plataforma:
# (o CLI faz isso automaticamente no primeiro uso)
mcp config show
```

### Método 4 — Docker (qualquer sistema)

```bash
# Iniciar todos os servidores em containers:
docker compose -f docker/docker-compose.yml --profile full up -d

# Verificar saúde:
curl http://localhost:8080/health

# Parar:
docker compose -f docker/docker-compose.yml down
```

---

## Pós-instalação

### 1. Configurar Token do GitHub (obrigatório para GitHub MCP)

```powershell
# Windows (PowerShell):
$env:GITHUB_TOKEN = "ghp_seu_token_aqui"

# Para tornar permanente:
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "ghp_seu_token_aqui", "User")
```

```bash
# Linux/macOS:
export GITHUB_TOKEN="ghp_seu_token_aqui"

# Para tornar permanente, adicione ao ~/.bashrc ou ~/.zshrc:
echo 'export GITHUB_TOKEN="ghp_seu_token_aqui"' >> ~/.bashrc
```

### 2. Verificar instalação

```bash
mcp config show        # Ver diretórios da plataforma
mcp registry list      # Ver servidores disponíveis
mcp profile list       # Ver perfis disponíveis
mcp profile current    # Ver perfil ativo
```

### 3. Vincular a um projeto

```bash
# Dentro do diretório do seu projeto:
cd C:\workspace\Freelancer\K.A.O.S
mcp project add --agent opencode

# Ou para Claude Code:
mcp project add --agent claude-code

# Verificar status do projeto:
mcp project status

# Listar todos os projetos vinculados:
mcp project list

# Remover MCP de um projeto:
mcp project remove
```

### 4. Iniciar servidores

```bash
# Iniciar todos os servidores do perfil ativo:
mcp start

# Iniciar com perfil específico:
mcp start --profile backend

# Verificar status:
mcp status
```

### 5. Testar

```bash
# Verificar saúde:
mcp health check

# Ver servidores rodando:
mcp status

# Executar benchmark:
mcp benchmark github
```

---

## Comandos Completos

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `mcp install [server]` | Instalar servidor(es) | `mcp install github` |
| `mcp install --tier 1` | Instalar todos do Tier 1 | `mcp install --tier 1` |
| `mcp start` | Iniciar servidores | `mcp start --profile backend` |
| `mcp stop [server]` | Parar servidor(es) | `mcp stop docker` |
| `mcp restart <server>` | Reiniciar servidor | `mcp restart github` |
| `mcp status` | Status de todos | `mcp status` |
| `mcp emergency stop` | Parar tudo agora | `mcp emergency stop` |
| `mcp project add` | Vincular projeto atual | `mcp project add --agent claude-code` |
| `mcp project remove` | Desvincular projeto | `mcp project remove` |
| `mcp project list` | Listar projetos vinculados | `mcp project list` |
| `mcp project status` | Status do vínculo | `mcp project status` |
| `mcp profile set <nome>` | Trocar perfil | `mcp profile set ai-llm` |
| `mcp profile list` | Listar perfis | `mcp profile list` |
| `mcp generate <agent>` | Gerar config do agente | `mcp generate claude-code` |
| `mcp update check` | Verificar atualizações | `mcp update check` |
| `mcp update apply` | Aplicar atualizações | `mcp update apply` |
| `mcp update rollback <s>` | Reverter atualização | `mcp update rollback github` |
| `mcp update history` | Histórico de updates | `mcp update history` |
| `mcp health check` | Verificar saúde | `mcp health check` |
| `mcp health metrics` | Métricas detalhadas | `mcp health metrics --server github` |
| `mcp health summary` | Resumo de saúde | `mcp health summary` |
| `mcp registry list` | Listar servidores | `mcp registry list` |
| `mcp registry search <q>` | Buscar servidores | `mcp registry search database` |
| `mcp registry info <id>` | Detalhes do servidor | `mcp registry info github` |
| `mcp config show` | Ver configuração | `mcp config show` |
| `mcp config edit` | Editar configuração | `mcp config edit` |
| `mcp benchmark [srv]` | Benchmark | `mcp benchmark github` |
| `mcp --version` | Versão | `mcp --version` |

---

## Perfis de Engenharia

Cada perfil ativa apenas os servidores relevantes para aquela área.
Isso reduz consumo de memória e melhora a qualidade das respostas da IA.

| Perfil | Foco | Servidores | Como Ativar |
|--------|------|-----------|-------------|
| `full-stack` | Geral (padrão) | 10 | `mcp profile set full-stack` |
| `backend` | APIs, banco, Docker | 8 | `mcp profile set backend` |
| `frontend` | UI, navegador | 7 | `mcp profile set frontend` |
| `devops` | Cloud, CI/CD, infra | 6 | `mcp profile set devops` |
| `ai-llm` | IA, RAG, LLMs | 7 | `mcp profile set ai-llm` |
| `security` | Auditoria | 5 | `mcp profile set security` |
| `documentation` | Documentação | 4 | `mcp profile set documentation` |
| `data-engineering` | Dados, ETL | 5 | `mcp profile set data-engineering` |
| `minimal` | Leve (3 servidores) | 3 | `mcp profile set minimal` |

A detecção automática também funciona:
- Projetos com `Dockerfile` → perfil `devops`
- Projetos com `package.json` → perfil `frontend`
- Projetos com `Cargo.toml` ou `pyproject.toml` → perfil `backend`

---

## Servidores Disponíveis

### Tier 1 — Core (instalação padrão)
| Servidor | Versão | Função | Risco | Instalar |
|----------|--------|--------|-------|----------|
| Context7 | 3.2.3 | Documentação viva de APIs/frameworks | Baixo | `mcp install context7` |
| Serena | 1.10.0 | Navegação semântica de código | Baixo | `mcp install serena` |
| GitHub | 2025.4.8 | Issues, PRs, commits, busca | Médio | `mcp install github` |
| Playwright | 0.0.78 | Automação de navegador | Alto | `mcp install playwright` |
| Filesystem | 2026.7.10 | Leitura/escrita segura de arquivos | Alto | `mcp install filesystem` |
| Sequential Thinking | 2026.7.4 | Raciocínio estruturado | Nenhum | `mcp install sequential-thinking` |

### Tier 2 — Enhanced (instalação sob demanda)
| Servidor | Versão | Função | Risco | Instalar |
|----------|--------|--------|-------|----------|
| PostgreSQL | 0.6.2 | Gerenciamento de banco | Alto | `mcp install postgres` |
| Docker | 2026.7.4 | Gerenciamento de containers | Crítico | `mcp install docker` |
| Fetch | 0.0.78 | Pesquisa na web | Baixo | `mcp install fetch` |
| Memory | 2026.7.4 | Memória persistente entre sessões | Baixo | `mcp install memory` |

### Tier 3 — Expert
| Servidor | Versão | Função | Instalar |
|----------|--------|--------|----------|
| Tavily | 1.0.0 | Pesquisa web profissional | `mcp install tavily` |

---

## Múltiplos Projetos

Você pode vincular quantos projetos quiser à plataforma MCP:

```bash
# Vincular projetos
cd C:\workspace\Freelancer\K.A.O.S
mcp project add --agent opencode

cd C:\workspace\Freelancer\Wakanda
mcp project add --agent claude-code

cd C:\workspace\OutroProjeto
mcp project add --agent cursor

# Ver todos os projetos vinculados
mcp project list
```

Cada projeto pode usar um agente diferente (OpenCode, Claude Code, Cursor, VS Code).

Para remover um projeto:
```bash
cd C:\workspace\Freelancer\Wakanda
mcp project remove
```

---

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `MCP_HOME` | OS-specific | Diretório raiz da plataforma |
| `MCP_PROFILE` | `full-stack` | Perfil ativo |
| `MCP_DEBUG` | `false` | Logs detalhados |
| `GITHUB_TOKEN` | — | Token do GitHub (obrigatório) |
| `DATABASE_URL` | — | String de conexão PostgreSQL |

### Diretório Padrão da Plataforma

| Sistema | Caminho |
|---------|---------|
| Windows | `%APPDATA%/mcp/` |
| Linux | `~/.config/mcp/` |
| macOS | `~/Library/Application Support/mcp/` |
| Docker | `/home/mcp/.config/mcp/` (volume mcp_config) |

---

## Estrutura do Projeto

```
personal-mcp-platform/
├── mcp_cli/                    # CLI em Python (código fonte)
├── docker/                     # Docker Compose + nginx proxy
│   ├── docker-compose.yml      # 12 serviços MCP conteinerizados
│   └── nginx.conf              # Proxy HTTP/SSE na porta 8080
├── scripts/
│   ├── install.ps1             # Instalador PowerShell (Windows)
│   └── install.sh              # Instalador Bash (Linux/macOS)
├── docs/                       # Documentação completa
│   ├── ARCHITECTURE.md         # Arquitetura do sistema
│   ├── INSTALLATION.md         # Guia de instalação detalhado
│   ├── USAGE.md                # Referência de comandos
│   ├── PROFILES.md             # Perfis de engenharia
│   ├── SECURITY.md             # Modelo de segurança
│   ├── TROUBLESHOOTING.md      # Solução de problemas
│   ├── DEVELOPMENT.md          # Guia do desenvolvedor
│   └── UPGRADE.md              # Atualizações e rollback
├── registry.yaml               # Catálogo de servidores (fonte única da verdade)
├── profiles/                   # Definições dos 9 perfis
├── config/config.yaml          # Configuração do usuário
├── pyproject.toml              # Pacote Python
├── README.md                   # Este arquivo
└── .gitignore
```

---

## Primeiros Passos Após Instalação

```bash
# 1. Verificar se está tudo funcionando
mcp status

# 2. Escolher um perfil
mcp profile set full-stack

# 3. Iniciar servidores
mcp start

# 4. Verificar saúde
mcp health check

# 5. Testar benchmark
mcp benchmark github

# 6. Vincular a um projeto
cd C:\workspace\SeuProjeto
mcp project add --agent opencode
```

Agora abra seu agente de IA no projeto e ele já terá acesso a todas as ferramentas MCP.

---

## Suporte

| Recurso | Onde |
|---------|------|
| Documentação completa | `docs/` |
| GitHub Issues | https://github.com/Brian5m1th/personal-mcp-platform/issues |
| Diagnóstico rápido | `mcp health check` |
| Logs | `%APPDATA%/mcp/logs/` (Windows), `~/.config/mcp/logs/` (Linux/macOS) |

---

## Licença

MIT — Livre para uso pessoal e comercial.
