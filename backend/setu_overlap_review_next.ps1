Set-Location "E:\App\Project\setu\backend"

Write-Host "`n=== OVERLAP ENGINE FUNCTIONS ===" -ForegroundColor Cyan
Select-String -Path ".\overlap_engine.py", ".\main.py" `
  -Pattern '^def |^async def |find_overlap_candidates|overlap|candidate' `
  -Context 2,3

Write-Host "`n=== OVERLAP TEST FILE ===" -ForegroundColor Cyan
Get-Content ".\test_overlap_engine.py"

Write-Host "`n=== OVERLAP DATA INSPECTION SCRIPT (READ ONLY REVIEW) ===" -ForegroundColor Cyan
Get-Content ".\inspect_overlap_data.py" -TotalCount 180

Write-Host "`n=== OVERLAP UNIT TESTS ===" -ForegroundColor Cyan
python -m pytest -q .\test_overlap_engine.py
