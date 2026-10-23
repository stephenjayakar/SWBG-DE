@echo off
rem Removes the SWGB-DE mods and restores any SWGB-DE folders the installer backed up.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\Install-SWGB-DE.ps1" -Uninstall %*
set RC=%ERRORLEVEL%
echo.
pause
exit /b %RC%
