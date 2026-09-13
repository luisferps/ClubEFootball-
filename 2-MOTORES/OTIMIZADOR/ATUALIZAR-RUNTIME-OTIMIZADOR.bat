@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Atualizar runtime do Otimizador
powershell -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0ATUALIZAR-RUNTIME-OTIMIZADOR.ps1" %*
set "codigo=%ERRORLEVEL%"
echo.
if not "%codigo%"=="0" echo A atualizacao nao terminou. Leia a mensagem acima.
pause
exit /b %codigo%
