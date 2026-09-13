@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0EMPACOTAR-MAQUINA-2.ps1"
set "codigo=%ERRORLEVEL%"
pause
exit /b %codigo%
