@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title Otimizador - Somente Shevchenko e Jaap Stam
set "CLUBEFOOTBALL_RESULTADOS_SUBPASTA=RESULTADOS-REPARO-SHEV-STAM"

echo.
echo PROCESSAMENTO RESTRITO:
echo 1. Andriy Shevchenko - 88045755964138
echo 2. Jaap Stam - 88045755964131
echo Nenhuma outra carta pode entrar nesta execucao.
echo.

"bin\OperacaoLocalJson.exe" processar --linhas 380367 380369 380370 380371 380372 380373 380375 380376 380377 380378 403427 403428
if errorlevel 1 goto :falhou

echo.
echo Enviando somente os resultados dessas duas cartas...
echo.
"bin\OperacaoLocalJson.exe" enviar --lote 7581b184-dccb-4a4b-9ad9-c767d4f4947c --linhas 380367 380369 380370 380371 380372 380373 380375 380376 380377 380378
if errorlevel 1 goto :falhou

"bin\OperacaoLocalJson.exe" enviar --lote c5e38fd5-877c-416e-8063-977e24d229db --linhas 403427 403428
if errorlevel 1 goto :falhou

echo.
echo CONCLUIDO.
echo.
pause
exit /b 0

:falhou
echo.
echo A OPERACAO PAROU COM ERRO. Leia a mensagem acima.
echo Nenhum resultado confirmado foi apagado.
echo.
pause
exit /b 2
