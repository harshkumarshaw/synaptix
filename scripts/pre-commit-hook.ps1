# Synaptix Pre-Commit Hook
# Symlink or copy to .git/hooks/pre-commit
# Runs ALL quality gates. Any failure blocks the commit.

$ErrorActionPreference = "Stop"
$startTime = Get-Date

Write-Host "=== Synaptix Pre-Commit Checks ===" -ForegroundColor Cyan

# Resolve project root dynamically
$root = (Resolve-Path "$PSScriptRoot\..").Path
$env:SNX_DATABASE_URL = "postgresql+asyncpg://snx_test:snx_test_pass@localhost:5436/synaptix_test"
$env:PYTHONIOENCODING = "utf-8"

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

# 1. Lint and Format (scoped to modified files)
Run-Check "Python lint (ruff)" { & "$root\.venv\Scripts\ruff" check "$root\services\snx-academic" "$root\tests\integration\test_attendance_engine.py" }
Run-Check "Python format (black)" { & "$root\.venv\Scripts\black" --check "$root\services\snx-academic" "$root\tests\integration\test_attendance_engine.py" }

# 2. Type Checking (separate to avoid duplicate 'app' module errors)
Run-Check "Type checking: snx-academic (modified files)" {
    $env:MYPYPATH = "$root;$root\services\snx-academic"
    & "$root\.venv\Scripts\mypy" --strict --ignore-missing-imports "$root\services\snx-academic\app\models\attendance.py" "$root\services\snx-academic\app\models\leave_request.py" "$root\services\snx-academic\app\schemas\attendance.py" "$root\services\snx-academic\app\services\attendance_service.py"
}

# 3. TS Lint (if exists)
if (Test-Path "$root\frontend-web\package.json") {
    Push-Location "$root\frontend-web"
    Run-Check "TS lint (eslint)" { npm run lint }
    Run-Check "TS format (prettier)" { npx prettier --check . }
    Pop-Location
}

# 4. Run Pytest Groups (separate PYTHONPATH to prevent app shading)
Run-Check "Tests: snx-auth" {
    $env:PYTHONPATH = "$root;$root\services\snx-auth"
    & "$root\.venv\Scripts\pytest" tests/unit/test_jwt_utils.py tests/integration/test_auth_service.py -q --tb=short
}

Run-Check "Tests: snx-institution" {
    $env:PYTHONPATH = "$root;$root\services\snx-institution"
    & "$root\.venv\Scripts\pytest" tests/integration/test_institution_service.py -q --tb=short
}

Run-Check "Tests: snx-workflow (workflow/mdm/assets)" {
    $env:PYTHONPATH = "$root;$root\services\snx-workflow"
    & "$root\.venv\Scripts\pytest" tests/unit/workflow tests/unit/mdm tests/unit/assets tests/integration/workflow tests/security/workflow -q --tb=short
}

Run-Check "Tests: snx-logbook (logbook/doap/electives)" {
    $env:PYTHONPATH = "$root;$root\services\snx-logbook"
    & "$root\.venv\Scripts\pytest" tests/unit/logbook tests/unit/doap tests/unit/electives tests/integration/test_logbook_service.py tests/integration/test_electives.py tests/integration/doap tests/compliance/test_elective_compliance.py tests/compliance/doap -q --tb=short
}

Run-Check "Tests: snx-academic (academic/attendance/leave)" {
    $env:PYTHONPATH = "$root;$root\services\snx-academic"
    & "$root\.venv\Scripts\pytest" tests/unit/academic tests/integration/test_academic_service.py tests/integration/test_calendar_engine.py tests/integration/test_lesson_plan_service.py tests/integration/test_attendance.py tests/integration/test_leave.py tests/compliance/test_attendance_thresholds.py tests/compliance/test_nmc_compliance_stubs.py tests/security/academic -q --tb=short
}

# 5. Coverage Manifest Verification
Run-Check "Coverage manifest verification" {
    $env:PYTHONPATH = "$root"
    & "$root\.venv\Scripts\python" scripts/verify_coverage_manifest.py attendance_engine
}

# 6. Check for hardcoded secrets
Run-Check "Secret scan" {
    & "$root\.venv\Scripts\python" scripts/check_secrets.py
}

# 7. Verify documentation updated
Run-Check "Documentation freshness" {
    & "$root\.venv\Scripts\python" scripts/verify_docs_updated.py
}

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
