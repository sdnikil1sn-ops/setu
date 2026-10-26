[CmdletBinding()]
param(
    [string]$BackendPath = "E:\App\Project\setu\backend",
    [switch]$AllowLiveReadOnlyChecks
)

$ErrorActionPreference = "Continue"
$Started = Get-Date
$Results = [System.Collections.Generic.List[object]]::new()

function Add-Result([string]$Area, [string]$Status, [string]$Detail) {
    $Results.Add([pscustomobject]@{ Area = $Area; Status = $Status; Detail = $Detail })
    $color = switch ($Status) {
        "PASS" { "Green" }
        "REVIEW" { "Yellow" }
        "BLOCKED" { "Red" }
        "FAIL" { "Red" }
        default { "Gray" }
    }
    Write-Host ("[{0}] {1}: {2}" -f $Status, $Area, $Detail) -ForegroundColor $color
}

function Read-DotEnv([string]$Path) {
    $values = @{}
    if (!(Test-Path -LiteralPath $Path)) { return $values }
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$' -and $line -notmatch '^\s*#') {
            $key = $Matches[1]
            $value = $Matches[2].Trim()
            if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            $values[$key] = $value
        }
    }
    return $values
}

function Invoke-PythonFile([string]$Path, [string]$Label) {
    if (!(Test-Path -LiteralPath $Path)) {
        Add-Result $Label "BLOCKED" "Expected script not found: $Path"
        return
    }
    Write-Host "`n--- Running $Label ---" -ForegroundColor Cyan
    & python $Path
    $code = $LASTEXITCODE
    if ($code -eq 0) { Add-Result $Label "PASS" "Script exited successfully." }
    else { Add-Result $Label "FAIL" "Script exit code: $code" }
}

if (!(Test-Path -LiteralPath $BackendPath)) {
    Write-Host "Backend folder not found: $BackendPath" -ForegroundColor Red
    exit 2
}
Set-Location -LiteralPath $BackendPath
$envFile = Join-Path $BackendPath ".env"
$envValues = Read-DotEnv $envFile
$reportPath = Join-Path $BackendPath "setu_remaining_work_report.txt"

Write-Host "SETU remaining-work one-run audit" -ForegroundColor Cyan
Write-Host "Backend: $BackendPath"
Write-Host "Started: $Started"
Write-Host "Safety: no database writes, fixture creation, importer activation, or restore-overwrite are performed by this runner."
Write-Host ""

# 1. Automated tests
Write-Host "--- 1. Automated tests ---" -ForegroundColor Cyan
& python -m pytest -q
$pytestCode = $LASTEXITCODE
if ($pytestCode -eq 0) { Add-Result "Automated tests" "PASS" "pytest -q passed." }
else { Add-Result "Automated tests" "FAIL" "pytest -q exit code: $pytestCode" }

# 2. RLS real-row isolation prerequisites and existing read-only test
$rlsVars = @("SETU_RLS_TEST_DATABASE_URL", "SETU_RLS_ALLOWED_CASE_ID", "SETU_RLS_RESTRICTED_CASE_ID", "SETU_RLS_OUT_OF_SCOPE_CASE_ID")
$rlsMissing = @($rlsVars | Where-Object {
    $processValue = [Environment]::GetEnvironmentVariable($_)
    $dotValue = $envValues[$_]
    [string]::IsNullOrWhiteSpace($processValue) -and [string]::IsNullOrWhiteSpace($dotValue)
})
$rlsScript = Join-Path $BackendPath "test_setu_phase6_direct_login_rls.py"
if ($rlsMissing.Count -eq 0 -and (Test-Path -LiteralPath $rlsScript)) {
    Invoke-PythonFile $rlsScript "RLS session/read-only checks"
    Add-Result "Real-row RLS isolation" "BLOCKED" "Fixture IDs are configured, but this runner will not create or mutate case fixtures. Run a dedicated isolated-fixture verifier after confirming the target database is non-production."
} else {
    Add-Result "Real-row RLS isolation" "BLOCKED" ("Requires an isolated test DB and controlled case IDs. Missing: " + ($rlsMissing -join ", "))
}

# 3. Role-by-role E2E prerequisites. Never print token values.
$roleVars = @(
    "SETU_AUDIT_TOKEN_ADMIN",
    "SETU_AUDIT_TOKEN_SENIOR_MANAGEMENT",
    "SETU_AUDIT_TOKEN_BUREAU_HEAD",
    "SETU_AUDIT_TOKEN_REGIONAL_OFFICER",
    "SETU_AUDIT_TOKEN_DESK_OFFICER"
)
$roleMissing = @($roleVars | Where-Object {
    [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($_)) -and [string]::IsNullOrWhiteSpace($envValues[$_])
})
$roleScriptCandidates = @("test_role_authorization_e2e.py", "run_role_authorization_e2e.py", "test_five_role_e2e.py")
$roleScript = $roleScriptCandidates | ForEach-Object { Join-Path $BackendPath $_ } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($roleMissing.Count -eq 0 -and $roleScript) {
    Invoke-PythonFile $roleScript "Five-role authorization E2E"
} else {
    $detail = "Missing token variables: " + ($roleMissing -join ", ")
    if (!$roleScript) { $detail += "; no dedicated role E2E runner found" }
    Add-Result "Five-role authorization E2E" "BLOCKED" $detail
}

# 4. Live overlap retrieval. Run only a named existing live-test script.
$overlapCandidates = @("test_live_overlap_retrieval.py", "run_live_overlap_retrieval.py", "test_overlap_database_integration.py")
$overlapScript = $overlapCandidates | ForEach-Object { Join-Path $BackendPath $_ } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$overlapDb = $envValues["SETU_OVERLAP_TEST_DATABASE_URL"]
if ([string]::IsNullOrWhiteSpace($overlapDb)) { $overlapDb = [Environment]::GetEnvironmentVariable("SETU_OVERLAP_TEST_DATABASE_URL") }
if ($overlapScript -and ![string]::IsNullOrWhiteSpace($overlapDb)) {
    Invoke-PythonFile $overlapScript "Live overlap retrieval"
} else {
    $why = @()
    if (!$overlapScript) { $why += "no dedicated live-overlap test script found" }
    if ([string]::IsNullOrWhiteSpace($overlapDb)) { $why += "SETU_OVERLAP_TEST_DATABASE_URL is not configured" }
    Add-Result "Live overlap retrieval" "BLOCKED" ($why -join "; ")
}
Write-Host "Overlap unit tests are covered by the pytest run above; they do not prove live database candidate retrieval."

# 5. Backup and restore prerequisites. Never execute a restore automatically.
$backupDir = $envValues["SETU_BACKUP_DIR"]
if ([string]::IsNullOrWhiteSpace($backupDir)) { $backupDir = [Environment]::GetEnvironmentVariable("SETU_BACKUP_DIR") }
$pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
$pgRestore = Get-Command pg_restore -ErrorAction SilentlyContinue
$restoreUrl = $envValues["SETU_RESTORE_TEST_DATABASE_URL"]
if ([string]::IsNullOrWhiteSpace($restoreUrl)) { $restoreUrl = [Environment]::GetEnvironmentVariable("SETU_RESTORE_TEST_DATABASE_URL") }
$backupOk = ![string]::IsNullOrWhiteSpace($backupDir) -and (Test-Path -LiteralPath $backupDir -PathType Container)
if ($backupOk -and $pgDump -and $pgRestore -and ![string]::IsNullOrWhiteSpace($restoreUrl) -and $restoreUrl -match '(_restore_test|_test|_testing)(?:[/?]|$)') {
    Add-Result "Backup/restore prerequisites" "PASS" "Backup directory, pg_dump/pg_restore, and explicitly named test restore URL found; restore is not run automatically."
} else {
    $missing = @()
    if (!$backupOk) { $missing += "SETU_BACKUP_DIR must point to an existing directory" }
    if (!$pgDump) { $missing += "pg_dump missing from PATH" }
    if (!$pgRestore) { $missing += "pg_restore missing from PATH" }
    if ([string]::IsNullOrWhiteSpace($restoreUrl) -or $restoreUrl -notmatch '(_restore_test|_test|_testing)(?:[/?]|$)') { $missing += "SETU_RESTORE_TEST_DATABASE_URL must clearly identify a separate test database" }
    Add-Result "Backup/restore proof" "BLOCKED" ($missing -join "; ")
}

# 6. Logging and exception audit
$scanFiles = @("main.py", "auth.py", "db_context.py", "overlap_engine.py", "import_dataset.py") |
    ForEach-Object { Join-Path $BackendPath $_ } |
    Where-Object { Test-Path -LiteralPath $_ }
$hits = @()
foreach ($file in $scanFiles) {
    $lineNo = 0
    foreach ($line in Get-Content -LiteralPath $file) {
        $lineNo++
        if ($line -match 'detail\s*=\s*str\(exc\)|detail\s*=\s*repr\(exc\)|HTTPException\(.*\bexc\b|print\(.*exc') {
            $hits += ("{0}:{1}" -f (Split-Path $file -Leaf), $lineNo)
        }
    }
}
$logLevel = $envValues["SETU_LOG_LEVEL"]
if ([string]::IsNullOrWhiteSpace($logLevel)) { $logLevel = [Environment]::GetEnvironmentVariable("SETU_LOG_LEVEL") }
if ($hits.Count -eq 0 -and ![string]::IsNullOrWhiteSpace($logLevel)) {
    Add-Result "Logging/exception static scan" "PASS" "No obvious raw-exception patterns detected; SETU_LOG_LEVEL is configured. Manual review is still required."
} else {
    $detail = @()
    if ($hits.Count -gt 0) { $detail += "Potential exception-detail patterns at " + ($hits -join ", ") }
    if ([string]::IsNullOrWhiteSpace($logLevel)) { $detail += "SETU_LOG_LEVEL not found in process environment or .env" }
    Add-Result "Logging/exception audit" "REVIEW" ($detail -join "; ")
}

# 7. Dataset importer stays disabled unless least-privilege credentials and an explicit safe test are available.
$importUrl = $envValues["SETU_IMPORTER_DATABASE_URL"]
if ([string]::IsNullOrWhiteSpace($importUrl)) { $importUrl = [Environment]::GetEnvironmentVariable("SETU_IMPORTER_DATABASE_URL") }
$importScript = Join-Path $BackendPath "import_dataset.py"
if (![string]::IsNullOrWhiteSpace($importUrl) -and (Test-Path -LiteralPath $importScript)) {
    Add-Result "Dataset importer" "REVIEW" "Importer URL and script exist. Least-privilege grants and dry-run/idempotency still require explicit verification; importer was not executed."
} else {
    Add-Result "Dataset importer" "BLOCKED" "Separate SETU_IMPORTER_DATABASE_URL or import_dataset.py is missing. Importer remains unexecuted."
}

# Existing consolidated runner, if present, provides health/demo endpoint checks.
$existingRunner = Join-Path $BackendPath "setu_one_run_readiness.py"
if (Test-Path -LiteralPath $existingRunner) {
    Invoke-PythonFile $existingRunner "Existing consolidated readiness runner"
} else {
    Add-Result "HTTP health/demo checks" "REVIEW" "setu_one_run_readiness.py not found; endpoint checks were not repeated."
}

# Write report without secrets or URLs.
$lines = @(
    "SETU remaining-work audit report",
    "Started: $Started",
    "Finished: $(Get-Date)",
    "Backend: $BackendPath",
    "",
    "No token, password, or database URL values are written to this report.",
    ""
)
foreach ($item in $Results) {
    $lines += ("[{0}] {1}: {2}" -f $item.Status, $item.Area, $item.Detail)
}
$lines += ""
$lines += "Important: PASS on unit tests does not prove real-row RLS isolation, five-role E2E, live overlap retrieval, or successful backup restoration."
$lines | Set-Content -LiteralPath $reportPath -Encoding UTF8

$pass = @($Results | Where-Object Status -eq "PASS").Count
$blocked = @($Results | Where-Object Status -eq "BLOCKED").Count
$review = @($Results | Where-Object Status -eq "REVIEW").Count
$fail = @($Results | Where-Object Status -eq "FAIL").Count
Write-Host "`n--- SUMMARY ---" -ForegroundColor Cyan
Write-Host "PASS=$pass  BLOCKED=$blocked  REVIEW=$review  FAIL=$fail"
Write-Host "Report: $reportPath" -ForegroundColor Cyan
Write-Host "This script does not create fixture data, enable imports, or restore a backup automatically."
if ($fail -gt 0) { exit 1 }
exit 0
