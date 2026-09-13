@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Fila global por prioridade
rem As correcoes participam da mesma fila global cadastrada em FILA-ATIVA.json.
call "PROCESSAR-FILA.bat" %*
exit /b %ERRORLEVEL%
