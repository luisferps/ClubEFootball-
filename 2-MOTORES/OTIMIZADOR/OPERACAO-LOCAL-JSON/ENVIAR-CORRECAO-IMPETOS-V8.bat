@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Enviar fila ativa
call "ENVIAR-RESULTADOS.bat" %*
exit /b %ERRORLEVEL%
