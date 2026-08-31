@echo off
setlocal
cd /d "%~dp0"
if not exist "Otimizador ClubEfootball.exe" (
  echo O aplicativo do Otimizador nao foi encontrado nesta pasta.
  echo Copie a pasta OTIMIZADOR completa e tente novamente.
  pause
  exit /b 1
)
start "" "Otimizador ClubEfootball.exe"
endlocal
