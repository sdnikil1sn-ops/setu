[CmdletBinding()]
param(
    [switch]$InstallDependencies
)

$ErrorActionPreference = 'Stop'
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BackendDir

Write-Host ''
Write-Host 'SETU Phase 5B - automated checks' -ForegroundColor Cyan
Write-Host "Backend: $BackendDir"
Write-Host ''

$VenvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = 'py'
} else {
    $Python = 'python'
}

if ($InstallDependencies) {
    if (-not (Test-Path $VenvPython)) {
        Write-Host 'Creating backend .venv ...' -ForegroundColor Yellow
        if ($Python -eq 'py') {
            & py -3 -m venv (Join-Path $BackendDir '.venv')
        } else {
            & $Python -m venv (Join-Path $BackendDir '.venv')
        }
        if ($LASTEXITCODE -ne 0) { throw 'Could not create .venv.' }
    }
    $Python = $VenvPython
    Write-Host 'Installing declared runtime and test dependencies ...' -ForegroundColor Yellow
    & $Python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
    & $Python -m pip install -r (Join-Path $BackendDir 'requirements-dev.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}

Write-Host '[1/3] Checking Python dependencies ...' -ForegroundColor Cyan
& $Python -c "import fastapi, psycopg, jwt, rapidfuzz, dotenv, google.genai, pytest"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Required dependencies are missing.' -ForegroundColor Red
    Write-Host 'Run: .\run_phase5b_tests.ps1 -InstallDependencies' -ForegroundColor Yellow
    exit 2
}

Write-Host '[2/3] Compiling backend Python files ...' -ForegroundColor Cyan
$PythonFiles = Get-ChildItem -Path $BackendDir -File -Filter '*.py' |
    Where-Object { $_.Name -ne '__init__.py' } |
    ForEach-Object { $_.FullName }
if ($PythonFiles.Count -gt 0) {
    & $Python -m py_compile @PythonFiles
    if ($LASTEXITCODE -ne 0) { throw 'Python compilation failed.' }
}

Write-Host '[3/3] Running the complete automated pytest suite ...' -ForegroundColor Cyan
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host 'TESTS FAILED. Do not switch database credentials or apply security migrations yet.' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ''
Write-Host 'ALL PHASE 5B AUTOMATED CHECKS PASSED.' -ForegroundColor Green
Write-Host 'Note: this runner does not modify the Supabase database or run live-DB smoke tests.' -ForegroundColor Yellow
