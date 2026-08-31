@echo off
setlocal
cd /d "%~dp0"
title Otimizador - comparacao de 50 cards do arquivo anterior
echo ================================================================
echo   COMPARACAO ISOLADA - 50 CARDS DO ARQUIVO ANTERIOR
echo   TODAS AS LINHAS - NAO PUBLICA
echo ================================================================
python "fila_comparacao_legado_50.py" executar
echo.
echo Resultado e retomada ficam em teste-legado-50\estado-lote.json
pause
endlocal
