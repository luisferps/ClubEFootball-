@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Correcao de Impetos V8
call "PROCESSAR-FILA.bat" --lote 5fbe90c8-8e98-4a02-bd41-e8b3272c37f4
exit /b %ERRORLEVEL%
