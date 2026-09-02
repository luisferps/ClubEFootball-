@echo off
setlocal
chcp 65001 >nul
title Extrator de Fotos - Controle Operacional
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0controle-operacional.ps1"
set "CODIGO=%ERRORLEVEL%"
if not "%CODIGO%"=="0" (
  echo.
  echo O controle operacional terminou com erro. Leia a mensagem acima.
  echo.
  pause
)
endlocal & exit /b %CODIGO%
