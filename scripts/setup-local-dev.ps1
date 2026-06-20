# Synaptix Local Development Setup (Windows PowerShell)
# Run from project root: .\scripts\setup-local-dev.ps1

$ErrorActionPreference = "Stop"
Write-Host "=== Synaptix Local Development Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

function Check-Command {
    param($Command, $InstallHint)
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-Host "[X] $Command not found" -ForegroundColor Red
        Write-Host "    Install: $InstallHint" -ForegroundColor Gray
        return $false
    }
    Write-Host "[OK] $Command found" -ForegroundColor Green
    return $true
}

$prereqsOk = $true
$prereqsOk = (Check-Command "docker" "https://www.docker.com/products/docker-desktop") -and $prereqsOk
$prereqsOk = (Check-Command "git" "https://git-scm.com/download/win") -and $prereqsOk
$prereqsOk = (Check-Command "python" "https://www.python.org/downloads/ (3.12+)") -and $prereqsOk
$prereqsOk = (Check-Command "node" "https://nodejs.org/ (LTS 20+)") -and $prereqsOk

# Optional but recommended
if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    Write-Host "[OK] uv found (recommended)" -ForegroundColor Green
} else {
    Write-Host "[i] uv not found (optional but recommended)" -ForegroundColor Yellow
    Write-Host "    Install: irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Gray
}

if (-not $prereqsOk) {
    Write-Host ""
    Write-Host "Please install missing prerequisites and re-run." -ForegroundColor Red
    exit 1
}

# Create .env from template
Write-Host ""
Write-Host "Setting up environment..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Created .env from .env.example" -ForegroundColor Green
    Write-Host "    EDIT .env with your local values before continuing" -ForegroundColor Yellow
} else {
    Write-Host "[i] .env already exists, not overwriting" -ForegroundColor Yellow
}

# Generate JWT secret if placeholder
$envContent = Get-Content ".env" -Raw
if ($envContent -match "change_me_use_secure_random") {
    $jwtSecret = -join ((1..64) | ForEach-Object {[char]((Get-Random -Min 33 -Max 126))})
    $envContent = $envContent -replace "change_me_use_secure_random_string_minimum_32_chars", $jwtSecret
    Set-Content ".env" -Value $envContent -NoNewline
    Write-Host "[OK] Generated random JWT secret" -ForegroundColor Green
}

# Initialise git if not already
if (-not (Test-Path ".git")) {
    git init
    git checkout -b main
    Write-Host "[OK] Initialised git repository" -ForegroundColor Green
}

# Create .gitignore
if (-not (Test-Path ".gitignore")) {
    @"
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*.so
.venv/
venv/
env/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage
*.egg-info/
dist/
build/

# Node
node_modules/
.next/
.nuxt/
out/
*.tsbuildinfo

# Flutter
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.packages
build/

# IDEs
.vscode/
.idea/
*.swp
*.swo
.DS_Store
Thumbs.db

# Agent memory (these ARE committed, see below)
# .agent-memory/  -- DO NOT IGNORE; agent memory is part of repo

# Logs
*.log
logs/

# Storage (local dev only)
storage/
uploads/

# Cloud credentials (NEVER commit)
*.json
service-account*.json
gcp-key.json

# Secrets
secrets/
*.pem
*.key
*.crt
*.p12
"@ | Set-Content ".gitignore"
    Write-Host "[OK] Created .gitignore" -ForegroundColor Green
}

# Start local infrastructure
Write-Host ""
Write-Host "Starting local PostgreSQL..." -ForegroundColor Yellow
docker compose up -d postgres
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Failed to start PostgreSQL" -ForegroundColor Red
    exit 1
}

Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    $result = docker exec snx-postgres pg_isready -U snx 2>$null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 1
}

if ($ready) {
    Write-Host "[OK] PostgreSQL is ready on localhost:5432" -ForegroundColor Green
} else {
    Write-Host "[X] PostgreSQL did not become ready in 30 seconds" -ForegroundColor Red
    exit 1
}

# Final instructions
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open Antigravity in this directory"
Write-Host "  2. Open AGENTS.md and read it first"
Write-Host "  3. Read FIRST_SESSION_GUIDE.md for your first session walkthrough"
Write-Host "  4. Read AOIP_MASTER_SPEC_v5.md (or relevant sections)"
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  docker compose ps                  # check status"
Write-Host "  docker compose logs postgres -f    # tail logs"
Write-Host "  docker compose down                # stop services"
Write-Host "  docker compose down -v             # stop and DELETE DATA"
Write-Host "  docker compose --profile tools up  # start adminer + mailhog"
Write-Host ""
Write-Host "Database access:"
Write-Host "  Host: localhost:5432"
Write-Host "  DB:   synaptix_dev"
Write-Host "  User: snx"
Write-Host "  Pass: snx_dev_pass"
Write-Host ""
Write-Host "Connection URL:"
Write-Host "  postgresql://snx:snx_dev_pass@localhost:5432/synaptix_dev"
