# Synaptix Pre-Commit Hook
# Symlink or copy to .git/hooks/pre-commit
# Runs ALL quality gates. Any failure blocks the commit.

$ErrorActionPreference = "Stop"
$startTime = Get-Date

Write-Host "=== Synaptix Pre-Commit Checks ===" -ForegroundColor Cyan

$failed = $false

function Run-Check {
    param($Name, $ScriptBlock)
    Write-Host "Running: $Name..." -ForegroundColor Yellow -NoNewline
    try {
        & $ScriptBlock
        if ($LASTEXITCODE -ne 0) {
            Write-Host " FAILED" -ForegroundColor Red
            $script:failed = $true
        } else {
            Write-Host " OK" -ForegroundColor Green
        }
    } catch {
        Write-Host " FAILED ($_)" -ForegroundColor Red
        $script:failed = $true
    }
}

# 1. Check Python lint
if (Test-Path "pyproject.toml") {
    Run-Check "Python lint (ruff)" { ruff check . }
    Run-Check "Python format (black)" { black --check . }
    Run-Check "Python types (mypy)" { mypy --strict . }
}

# 2. Check TypeScript lint
if (Test-Path "frontend-web/package.json") {
    Push-Location frontend-web
    Run-Check "TS lint (eslint)" { npm run lint }
    Run-Check "TS format (prettier)" { npx prettier --check . }
    Pop-Location
}

# 3. Run unit tests
if (Test-Path "tests/unit") {
    Run-Check "Unit tests" { pytest tests/unit -x --tb=short -q }
}

# 4. Run compliance tests (HARD FAIL — NMC)
if (Test-Path "tests/compliance") {
    Run-Check "NMC Compliance tests (HARD FAIL)" {
        pytest tests/compliance -x --tb=short -q
    }
}

# 5. Verify coverage manifest
if (Test-Path "scripts/verify_coverage_manifest.py") {
    Run-Check "Coverage manifest verification" {
        python scripts/verify_coverage_manifest.py
    }
}

# 6. Check for hardcoded secrets
Run-Check "Secret scan" {
    python scripts/check_secrets.py
}

# 7. Verify documentation updated
Run-Check "Documentation freshness" {
    python scripts/verify_docs_updated.py
}

# 8. Verify commit message format (when commit-msg hook fires)

# Summary
$duration = (Get-Date) - $startTime
Write-Host ""
Write-Host "Total time: $($duration.TotalSeconds.ToString('F1'))s" -ForegroundColor Cyan

if ($failed) {
    Write-Host ""
    Write-Host "COMMIT BLOCKED. Fix the issues above and try again." -ForegroundColor Red
    Write-Host ""
    Write-Host "To bypass (use sparingly, document in INCIDENT_LOG.md):" -ForegroundColor Gray
    Write-Host "  git commit --no-verify" -ForegroundColor Gray
    exit 1
} else {
    Write-Host ""
    Write-Host "All checks passed. Commit proceeding." -ForegroundColor Green
    exit 0
}
