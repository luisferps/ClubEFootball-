@echo off
setlocal
cd /d "%~dp0"
rem Launcher do Extrator de Niveis eFHUB V1; catalogo do Otimizador em lotes de 1000.
if not exist "Extrator Niveis eFHUB.exe" (
  echo O aplicativo Extrator Niveis eFHUB.exe nao foi encontrado nesta pasta.
  pause
  exit /b 1
)
start "" "Extrator Niveis eFHUB.exe"
endlocal
