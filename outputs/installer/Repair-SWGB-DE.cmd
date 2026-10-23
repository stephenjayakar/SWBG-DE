@echo off
rem Re-enables SWBG-Data and SWBG-Logic in DE's mod-status.json without regenerating anything.
rem DE switches the subscribed SWBG-Logic (mod 549437) off whenever it downloads a new version. Close DE first.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\Install-SWGB-DE.ps1" -Repair %*
set RC=%ERRORLEVEL%
echo.
pause
exit /b %RC%
