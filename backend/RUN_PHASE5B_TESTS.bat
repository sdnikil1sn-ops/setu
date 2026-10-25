@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_phase5b_tests.ps1" %*
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
  echo SETU Phase 5B checks passed.
) else (
  echo SETU Phase 5B checks failed with exit code %RESULT%.
)
pause
exit /b %RESULT%
