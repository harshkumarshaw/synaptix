# Helper to quickly update common doc files at session end
# Usage: .\scripts\update-docs.ps1 -SessionSummary "Built attendance service skeleton"

param(
    [Parameter(Mandatory=$true)][string]$SessionSummary,
    [string]$AgentId = "human"
)

$date = Get-Date -Format "yyyy-MM-dd"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Append to CHANGELOG (unreleased section)
$changelogPath = "docs/CHANGELOG.md"
$changelog = Get-Content $changelogPath -Raw
$entry = "- $SessionSummary (by $AgentId on $date)"
$changelog = $changelog -replace '(## \[Unreleased\]\s*\n\s*\n### Added\s*\n)', "`$1$entry`n"
Set-Content $changelogPath -Value $changelog -NoNewline

# Append to DEVELOPMENT_LOG
Add-Content "docs/DEVELOPMENT_LOG.md" "`n## $date — Session by $AgentId`n`n$SessionSummary`n"

# Append to COMMAND_HISTORY for last commands in this PowerShell session
$lastCommands = Get-History | Select-Object -Last 20 | ForEach-Object {
    "[$timestamp] [$AgentId] $($_.CommandLine)"
}
if ($lastCommands) {
    Add-Content "docs/COMMAND_HISTORY.md" ($lastCommands -join "`n")
}

Write-Host "Documentation updated for: $SessionSummary" -ForegroundColor Green
