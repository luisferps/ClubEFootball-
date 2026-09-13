@echo off
cd /d "%~dp0"
echo COMPLEMENTO DE HABILIDADES V14 - CALCULAR
echo Ctrl+C para parar. Fila, JSONs e recibos sao preservados.
"%~dp0ComplementoLocalV14.exe" calcular
echo.
echo Operacao encerrada com codigo %errorlevel%.
pause
