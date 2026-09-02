@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Enviar fila principal
rem Envia somente os resultados da fila principal. Ver PROCESSAR-FILA-PRINCIPAL.bat.
call "ENVIAR-RESULTADOS.bat" --lote ddbcbc86-1ae7-4b95-b9f0-22601f41b61d
exit /b %ERRORLEVEL%
