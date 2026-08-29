@echo off
setlocal
cd /d "%~dp0"
if not exist "Bonificador ClubEfootball.exe" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "windows-app\COMPILAR-APLICATIVO.ps1"
)
start "" "Bonificador ClubEfootball.exe"
endlocal
