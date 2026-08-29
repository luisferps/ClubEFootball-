@echo off
setlocal
cd /d "%~dp0"
if not exist "Otimizador ClubEfootball.exe" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "windows-app\COMPILAR-APLICATIVO.ps1"
)
start "" "Otimizador ClubEfootball.exe"
endlocal
