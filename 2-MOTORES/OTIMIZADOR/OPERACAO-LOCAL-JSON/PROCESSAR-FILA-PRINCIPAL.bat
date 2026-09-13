@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Fila global por prioridade
rem FILA-ATIVA.json relaciona os pacotes conferidos, inclusive correcoes.
call "PROCESSAR-FILA.bat" %*
exit /b %ERRORLEVEL%
