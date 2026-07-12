#!/usr/bin/env pwsh
<#
.SYNOPSIS
    MCP Platform Installer — Windows / PowerShell
.DESCRIPTION
    Installs the Personal AI Engineering Platform (MCP) and its servers.
#>

param(
    [Parameter(Position=0)]
    [string]$Command = "install",

    [Parameter(Position=1)]
    [string]$ServerId = "",

    [switch]$Help,
    [switch]$DryRun,
    [string]$McpHome = "",
    [string]$Profile = "full-stack"
)

function Write-Step { param([string]$Msg) Write-Host "`n[Step] $Msg" -ForegroundColor Cyan }
function Write-OK { param([string]$Msg) Write-Host "  ✓ $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "  ⚠ $Msg" -ForegroundColor Yellow }
function Write-Err { param([string]$Msg) Write-Host "  ✗ $Msg" -ForegroundColor Red }

# ── Configuration ──────────────────────────────────────────────

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PlatformRoot = Split-Path -Parent $ScriptDir

if (-not $McpHome) {
    $McpHome = Join-Path $env:APPDATA "mcp"
    if (-not (Test-Path $env:APPDATA)) {
        $McpHome = Join-Path $env:USERPROFILE ".config" "mcp"
    }
}

$env:MCP_HOME = $McpHome

$Directories = @(
    "$McpHome",
    "$McpHome/profiles",
    "$McpHome/servers",
    "$McpHome/secrets",
    "$McpHome/cache/tools",
    "$McpHome/cache/schemas",
    "$McpHome/cache/health",
    "$McpHome/logs/servers",
    "$McpHome/downloads",
    "$McpHome/templates",
    "$McpHome/backups"
)

# ── Prerequisites Check ─────────────────────────────────────────

function Test-Prerequisites {
    Write-Step "Checking prerequisites..."

    $ok = $true

    # Node.js
    try {
        $nodeVer = node --version 2>$null
        Write-OK "Node.js $nodeVer"
    } catch {
        Write-Warn "Node.js not found. Install from https://nodejs.org (v18+)"
        $ok = $false
    }

    # npm
    try {
        $npmVer = npm --version 2>$null
        Write-OK "npm $npmVer"
    } catch {
        Write-Warn "npm not found"
        $ok = $false
    }

    # Python
    try {
        $pyVer = python --version 2>&1
        Write-OK "$pyVer"
    } catch {
        Write-Warn "Python not found. Install Python 3.11+"
        $ok = $false
    }

    # Git
    try {
        $gitVer = git --version 2>$null
        Write-OK "$gitVer"
    } catch {
        Write-Warn "Git not found (recommended for version control)"
    }

    return $ok
}

# ── Directory Setup ────────────────────────────────────────────

function Initialize-Directories {
    Write-Step "Creating platform directories..."
    foreach ($dir in $Directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-OK "Created: $dir"
        } else {
            Write-OK "Exists: $dir"
        }
    }
}

# ── Profile Initialization ─────────────────────────────────────

function Initialize-Profiles {
    Write-Step "Creating engineering profiles..."

    $profiles = @{
        "backend" = @{
            name = "Backend Engineering"
            description = "Servers for backend development"
            enabled_servers = @("context7", "github", "postgres", "docker", "sequential-thinking", "filesystem", "fetch", "memory")
            disabled_servers = @("playwright", "serena")
        }
        "frontend" = @{
            name = "Frontend Engineering"
            description = "Servers for frontend development"
            enabled_servers = @("context7", "github", "playwright", "filesystem", "sequential-thinking", "fetch", "memory")
            disabled_servers = @("postgres", "docker", "serena")
        }
        "ai-llm" = @{
            name = "AI / LLM Engineering"
            description = "Servers for AI development"
            enabled_servers = @("context7", "serena", "github", "sequential-thinking", "memory", "fetch", "filesystem")
            disabled_servers = @("playwright", "docker", "postgres")
        }
        "full-stack" = @{
            name = "Full Stack (Default)"
            description = "All servers with sensible limits"
            enabled_servers = @("context7", "serena", "github", "playwright", "filesystem", "sequential-thinking", "postgres", "docker", "fetch", "memory")
            disabled_servers = @()
        }
        "minimal" = @{
            name = "Minimal / Lightweight"
            description = "Minimal servers for quick sessions"
            enabled_servers = @("filesystem", "github", "sequential-thinking")
            disabled_servers = @()
        }
    }

    $profilesDir = "$McpHome/profiles"
    foreach ($name in $profiles.Keys) {
        $path = Join-Path $profilesDir "$name.yaml"
        if (-not (Test-Path $path)) {
            $profiles[$name] | ConvertTo-Yaml | Out-File -FilePath $path -Encoding utf8
            Write-OK "Created profile: $name"
        }
    }
}

# ── NPM Package Install Helper ─────────────────────────────────

function Install-NpxPackage {
    param([string]$PackageName, [string]$ServerId)

    if ($DryRun) {
        Write-OK "[DRY-RUN] Would install: npx -y $PackageName"
        return $true
    }

    try {
        $proc = Start-Process -FilePath "npx" -ArgumentList "-y", $PackageName -Wait -NoNewWindow -PassThru
        if ($proc.ExitCode -eq 0) {
            Write-OK "Installed: $ServerId"
            return $true
        } else {
            Write-Err "Failed to install $ServerId (exit code: $($proc.ExitCode))"
            return $false
        }
    } catch {
        Write-Err "Failed to install $ServerId`: $($_.Exception.Message)"
        return $false
    }
}

# ── Server Installation ────────────────────────────────────────

function Install-Servers {
    param([string[]]$ServerIds)

    Write-Step "Installing MCP servers..."

    $servers = @{
        "context7" = @{ package = "@context7/mcp-server"; tier = 1 }
        "serena" = @{ package = "serena-mcp"; tier = 1; method = "uvx" }
        "github" = @{ package = "@modelcontextprotocol/server-github"; tier = 1 }
        "playwright" = @{ package = "@playwright/mcp"; tier = 1 }
        "filesystem" = @{ package = "@modelcontextprotocol/server-filesystem"; tier = 1 }
        "sequential-thinking" = @{ package = "@modelcontextprotocol/server-sequential-thinking"; tier = 1 }
        "postgres" = @{ package = "@modelcontextprotocol/server-postgres"; tier = 2 }
        "docker" = @{ package = "@modelcontextprotocol/server-docker"; tier = 2 }
        "fetch" = @{ package = "@modelcontextprotocol/server-fetch"; tier = 2 }
        "memory" = @{ package = "@modelcontextprotocol/server-memory"; tier = 2 }
    }

    $targets = if ($ServerIds.Count -gt 0) { $ServerIds } else { $servers.Keys | Where-Object { $servers[$_].tier -eq 1 } }

    $success = 0
    $fail = 0

    foreach ($sid in $targets) {
        if (-not $servers.ContainsKey($sid)) {
            Write-Warn "Unknown server: $sid"
            continue
        }
        $info = $servers[$sid]
        Write-Host "  Installing $sid..." -NoNewline

        if (Install-NpxPackage -PackageName $info.package -ServerId $sid) {
            $success++
        } else {
            $fail++
        }
    }

    Write-OK "Installed $success/$($success + $fail) servers"
}

# ── Agent Config Generation ────────────────────────────────────

function Generate-AgentConfigs {
    Write-Step "Generating agent configurations..."

    # Claude Code config
    $claudeConfig = @{
        mcpServers = @{
            context7 = @{ command = "npx"; args = @("-y", "@context7/mcp-server"); env = @{} }
            github = @{ command = "npx"; args = @("-y", "@modelcontextprotocol/server-github"); env = @{ GITHUB_TOKEN = '${GITHUB_TOKEN}' } }
            filesystem = @{ command = "npx"; args = @("-y", "@modelcontextprotocol/server-filesystem", "."); env = @{} }
            sequential-thinking = @{ command = "npx"; args = @("-y", "@modelcontextprotocol/server-sequential-thinking"); env = @{} }
        }
    }

    $claudePath = Join-Path $env:USERPROFILE ".claude.json"
    if (-not (Test-Path $claudePath)) {
        $claudeConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $claudePath -Encoding utf8
        Write-OK "Generated Claude Code config: $claudePath"
    } else {
        Write-OK "Claude Code config exists: $claudePath (delete to regenerate)"
    }

    # OpenCode config
    $opencodeConfig = @{
        mcpServers = @{
            context7 = @{ command = "npx"; args = @("-y", "@context7/mcp-server") }
            github = @{ command = "npx"; args = @("-y", "@modelcontextprotocol/server-github") }
            filesystem = @{ command = "npx"; args = @("-y", "@modelcontextprotocol/server-filesystem", ".") }
            sequential-thinking = @{ command = "npx"; args = @("-y", "@modelcontextprotocol/server-sequential-thinking") }
        }
    }

    $opencodePath = Join-Path (Get-Location) ".opencode.json"
    if (-not (Test-Path $opencodePath)) {
        $opencodeConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $opencodePath -Encoding utf8
        Write-OK "Generated OpenCode config: $opencodePath"
    }
}

# ── Health Check ────────────────────────────────────────────────

function Test-Health {
    Write-Step "Verifying installation..."

    $servers = @("context7", "github", "filesystem", "sequential-thinking")
    $healthy = 0

    foreach ($sid in $servers) {
        try {
            $result = npx -y @("$sid/mcp-server", "--version") 2>&1
            Write-OK "$sid — available"
            $healthy++
        } catch {
            Write-Warn "$sid — not verified (expected if not installed)"
        }
    }
}

# ── Main ────────────────────────────────────────────────────────

function Show-Help {
    Write-Host @"
MCP Platform Installer — Personal AI Engineering Platform

USAGE:
    .\install.ps1 [command] [options]

COMMANDS:
    install       Install MCP platform and servers (default)
    verify        Verify prerequisites only
    config        Generate agent configurations only
    help          Show this help

OPTIONS:
    -ServerId     Install a specific server (e.g., "github")
    -Profile      Set active profile (default: full-stack)
    -McpHome      Override MCP_HOME path
    -DryRun       Show what would be installed without installing

EXAMPLES:
    .\install.ps1                            # Full install (Tier 1)
    .\install.ps1 -ServerId github           # Install specific server
    .\install.ps1 -Profile minimal           # Install with minimal profile
    .\install.ps1 -DryRun                    # Preview installation
"@
}

switch ($Command) {
    "help" { Show-Help; return }
    "verify" { Test-Prerequisites; return }
    "config" { Initialize-Directories; Initialize-Profiles; Generate-AgentConfigs; return }
    "install" {
        Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║   MCP Platform — Personal AI Engineering   ║" -ForegroundColor Cyan
        Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan

        if (-not (Test-Prerequisites)) {
            Write-Err "Prerequisites not met. Please install missing dependencies first."
            exit 1
        }

        Initialize-Directories
        Initialize-Profiles

        $targetServers = if ($ServerId) { @($ServerId) } else { @() }
        Install-Servers -ServerIds $targetServers

        Generate-AgentConfigs
        Test-Health

        Write-Host "`n╔══════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║   Installation Complete!                     ║" -ForegroundColor Green
        Write-Host "║                                             ║" -ForegroundColor Green
        Write-Host "║   MCP_HOME: $McpHome" -ForegroundColor Green
        Write-Host "║   Profile: $Profile" -ForegroundColor Green
        Write-Host "║                                             ║" -ForegroundColor Green
        Write-Host "║   Next steps:                               ║" -ForegroundColor Green
        Write-Host "║   1. Set GITHUB_TOKEN environment variable  ║" -ForegroundColor Green
        Write-Host "║   2. Run: mcp start                         ║" -ForegroundColor Green
        Write-Host "║   3. Open your AI agent and start coding    ║" -ForegroundColor Green
        Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
    }
    default {
        Write-Err "Unknown command: $Command"
        Show-Help
        exit 1
    }
}
