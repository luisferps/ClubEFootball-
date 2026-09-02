@echo off
setlocal
title Extrator de fotos dos cards - interface local
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0abrir-interface.ps1"
if errorlevel 1 (
  echo.
  echo A interface local parou com erro. Leia a mensagem acima.
)
echo.
pause
endlocal
