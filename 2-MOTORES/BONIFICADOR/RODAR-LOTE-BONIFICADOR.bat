@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
if not exist "Bonificador ClubEfootball.exe" (
  echo Aplicativo do Bonificador nao encontrado nesta pasta.
  if /i not "%CLUBEF_SEM_PAUSA%"=="1" pause
  exit /b 2
)
start "" "Bonificador ClubEfootball.exe"
exit /b 0
