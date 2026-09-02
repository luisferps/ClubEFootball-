@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Fila principal
rem Existe mais de um pacote local nesta pasta. Sem o --lote o programa
rem nao adivinha qual e o certo e para. Este atalho crava a fila principal.
call "PROCESSAR-FILA.bat" --lote ddbcbc86-1ae7-4b95-b9f0-22601f41b61d
exit /b %ERRORLEVEL%
