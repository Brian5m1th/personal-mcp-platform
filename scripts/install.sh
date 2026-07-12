#!/usr/bin/env bash
# MCP Platform Installer — Linux / macOS
# Personal AI Engineering Platform
set -euo pipefail

MCP_HOME="${MCP_HOME:-}"
COMMAND="${1:-install}"
SERVER_ID="${2:-}"
DRY_RUN="${DRY_RUN:-false}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

step()  { echo -e "\n${CYAN}[Step]${NC} $1"; }
ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
warn()  { echo -e "  ${YELLOW}⚠${NC} $1"; }
err()   { echo -e "  ${RED}✗${NC} $1"; }

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)   echo "linux" ;;
        Darwin*)  echo "macos" ;;
        *)        echo "unknown" ;;
    esac
}

# Resolve MCP_HOME
resolve_home() {
    if [ -n "$MCP_HOME" ]; then
        echo "$MCP_HOME"
        return
    fi

    local os
    os=$(detect_os)
    if [ "$os" = "macos" ]; then
        echo "$HOME/Library/Application Support/mcp"
    else
        echo "${XDG_CONFIG_HOME:-$HOME/.config}/mcp"
    fi
}

# Create directories
create_dirs() {
    local home="$1"
    mkdir -p "$home"/{profiles,servers,secrets,cache/{tools,schemas,health},logs/servers,downloads,templates,backups}
    ok "Platform directories created at $home"
}

# Check prerequisites
check_prereqs() {
    step "Checking prerequisites..."

    local ok=true

    if command -v node &>/dev/null; then
        ok "Node.js $(node --version)"
    else
        warn "Node.js not found. Install from https://nodejs.org (v18+)"
        ok=false
    fi

    if command -v npm &>/dev/null; then
        ok "npm $(npm --version)"
    else
        warn "npm not found"
        ok=false
    fi

    if command -v python3 &>/dev/null; then
        ok "Python3 $(python3 --version 2>&1)"
    elif command -v python &>/dev/null; then
        ok "Python $(python --version 2>&1)"
    else
        warn "Python not found. Install Python 3.11+"
        ok=false
    fi

    if command -v git &>/dev/null; then
        ok "Git $(git --version 2>&1)"
    else
        warn "Git not found (recommended)"
    fi

    $ok || return 1
    return 0
}

# Install npm package
install_npm() {
    local package="$1"
    local server="$2"

    if [ "$DRY_RUN" = "true" ]; then
        ok "[DRY-RUN] Would install: npx -y $package"
        return 0
    fi

    if npx -y "$package" --version &>/dev/null 2>&1; then
        ok "Installed: $server"
        return 0
    fi
    return 1
}

# Install servers
install_servers() {
    local home="$1"
    local server_id="$2"
    step "Installing MCP servers..."

    declare -A servers
    servers["context7"]="@upstash/context7-mcp"
    servers["serena"]="serena-slim"
    servers["github"]="@modelcontextprotocol/server-github"
    servers["playwright"]="@playwright/mcp"
    servers["filesystem"]="@modelcontextprotocol/server-filesystem"
    servers["sequential-thinking"]="@modelcontextprotocol/server-sequential-thinking"

    if [ -n "$server_id" ]; then
        if [ -n "${servers[$server_id]:-}" ]; then
            install_npm "${servers[$server_id]}" "$server_id"
        else
            err "Unknown server: $server_id"
            return 1
        fi
    else
        local success=0
        local total=0
        for sid in "${!servers[@]}"; do
            total=$((total + 1))
            echo -n "  Installing $sid... "
            if install_npm "${servers[$sid]}" "$sid"; then
                success=$((success + 1))
            fi
        done
        ok "Installed $success/$total servers"
    fi
}

# Create profiles
create_profiles() {
    local home="$1"
    step "Creating engineering profiles..."

    mkdir -p "$home/profiles"

    # Full stack (default)
    cat > "$home/profiles/full-stack.yaml" << 'PROFILE'
name: "Full Stack (Default)"
description: "All servers with sensible limits"
enabled_servers:
  - context7
  - serena
  - github
  - playwright
  - filesystem
  - sequential-thinking
  - postgres
  - docker
  - fetch
  - memory
PROFILE
    ok "Created profile: full-stack"

    # Backend
    cat > "$home/profiles/backend.yaml" << 'PROFILE'
name: "Backend Engineering"
description: "Servers for backend development: APIs, databases, containers"
enabled_servers:
  - context7
  - github
  - postgres
  - docker
  - sequential-thinking
  - filesystem
  - fetch
  - memory
disabled_servers:
  - playwright
  - serena
PROFILE
    ok "Created profile: backend"

    # Minimal
    cat > "$home/profiles/minimal.yaml" << 'PROFILE'
name: "Minimal / Lightweight"
description: "Minimal servers for quick coding sessions"
enabled_servers:
  - filesystem
  - github
  - sequential-thinking
PROFILE
    ok "Created profile: minimal"
}

# Generate agent configs
generate_configs() {
    local home="$1"
    step "Generating agent configurations..."

    # Claude Code
    cat > "$HOME/.claude.json" << 'CLAUDECONFIG'
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "env": {}
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "env": {}
    }
  }
}
CLAUDECONFIG
    ok "Generated: ~/.claude.json"
}

# Main
main() {
    local home
    home=$(resolve_home)

    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║   MCP Platform — Personal AI Engineering   ║"
    echo "╚══════════════════════════════════════════════╝"
    echo ""

    case "$COMMAND" in
        install)
            check_prereqs || {
                err "Prerequisites not met. Please install missing dependencies."
                exit 1
            }

            local home
            home=$(resolve_home)
            export MCP_HOME="$home"

            create_dirs "$home"
            create_profiles "$home"
            install_servers "$home" "$SERVER_ID"
            generate_configs "$home"

            echo ""
            echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║   Installation Complete!                     ║${NC}"
            echo -e "${GREEN}║                                             ║${NC}"
            echo -e "${GREEN}║   MCP_HOME: $home${NC}"
            echo -e "${GREEN}║                                             ║${NC}"
            echo -e "${GREEN}║   Next steps:                               ║${NC}"
            echo -e "${GREEN}║   1. Set GITHUB_TOKEN env variable          ║${NC}"
            echo -e "${GREEN}║   2. Run: mcp start                         ║${NC}"
            echo -e "${GREEN}║   3. Open your AI agent and start coding    ║${NC}"
            echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
            ;;

        verify)
            check_prereqs
            ;;

        help|--help|-h)
            echo "Usage: ./install.sh [command]"
            echo ""
            echo "Commands:"
            echo "  install           Install MCP platform and servers (default)"
            echo "  verify            Verify prerequisites only"
            echo "  help              Show this help"
            echo ""
            echo "Options:"
            echo "  MCP_HOME=<path>  Override platform root directory"
            echo "  DRY_RUN=true     Preview without installing"
            echo ""
            echo "Examples:"
            echo "  ./install.sh"
            echo "  MCP_HOME=~/.mcp ./install.sh"
            echo "  DRY_RUN=true ./install.sh"
            ;;

        *)
            err "Unknown command: $COMMAND"
            echo "Usage: ./install.sh [install|verify|help]"
            exit 1
            ;;
    esac
}

main
