@echo off
setlocal
cd /d "%~dp0"
title Otimizador - teste isolado de 100 cartas
echo ================================================================
echo   TESTE ISOLADO - 100 CARTAS UNICAS - NAO PUBLICA
echo ================================================================
python "teste_fila_100.py" executar
echo.
echo Resultado e retomada ficam em teste-100\estado-lote.json
pause
endlocal
