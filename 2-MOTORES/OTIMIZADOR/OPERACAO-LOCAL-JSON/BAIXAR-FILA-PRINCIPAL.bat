@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Baixar fila principal v6
if not exist "bin\OperacaoLocalJson.exe" (
  echo Programa ausente. Copie a pasta completa.
  pause
  exit /b 1
)
echo Baixando a fila v6: novas cartas, com orcamento, sem orcamento.
echo Cada grupo segue overall do maior para o menor.
"bin\OperacaoLocalJson.exe" renovar --lotes 39da8ff4-7a4a-4ec7-8641-e81b5677ad4c
set "codigo=%ERRORLEVEL%"
if "%codigo%"=="0" echo Pronto. Abra PROCESSAR-FILA-PRINCIPAL.bat e ENVIAR-FILA-PRINCIPAL.bat.
if not "%codigo%"=="0" echo Download nao concluido. Leia o erro acima antes de processar.
pause
exit /b %codigo%
