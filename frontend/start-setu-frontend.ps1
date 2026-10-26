$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".env.local")) {
    Copy-Item ".env.example" ".env.local"
    Write-Host "Created .env.local. Confirm SETU_BACKEND_TARGET matches your FastAPI port." -ForegroundColor Yellow
}
if (-not (Test-Path "node_modules")) {
    npm install
}
npm run dev
