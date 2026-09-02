@echo off
setlocal
cd /d "%~dp0"
echo O painel antigo foi aposentado. Abrindo o processamento local em JSON.
call "OPERACAO-LOCAL-JSON\PROCESSAR-FILA.bat"
exit /b %ERRORLEVEL%
