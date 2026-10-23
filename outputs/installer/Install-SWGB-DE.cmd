@echo off
rem Installs SWGB-in-AoE2-DE, generating the Star Wars assets from your own SWGB + Expanding Fronts install.
rem Extra options can be passed through, e.g.  Install-SWGB-DE.cmd -SwgbPath "D:\Games\SWGB" -Yes
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\Install-SWGB-DE.ps1" %*
set RC=%ERRORLEVEL%
echo.
pause
exit /b %RC%
