@echo off
setlocal
title Extrator de fotos dos cards
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0executar-extrator.ps1"
if errorlevel 1 (
  echo.
  echo A execucao parou com erro. Leia a ultima mensagem e consulte output\runs.
)
echo.
pause
endlocal


