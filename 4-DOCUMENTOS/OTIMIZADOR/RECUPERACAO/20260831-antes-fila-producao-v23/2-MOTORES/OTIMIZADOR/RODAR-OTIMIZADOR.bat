@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "windows-app\COMPILAR-APLICATIVO.ps1"
if errorlevel 1 exit /b 1
start "" "Otimizador ClubEfootball.exe"
endlocal
