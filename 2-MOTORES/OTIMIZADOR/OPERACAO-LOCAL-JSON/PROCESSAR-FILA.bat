@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Processar fila local em JSON
if not exist "bin\OperacaoLocalJson.exe" (
  echo O programa de processamento local nao foi encontrado.
  echo Copie a pasta OPERACAO-LOCAL-JSON completa, incluindo bin e PACOTE-FILA-INTEGRAL.
  pause
  exit /b 1
)
echo.
echo PROCESSAMENTO LOCAL: uma linha por vez. Nao envia nada ao banco.
echo Para parar com seguranca, pressione Ctrl+C. O que ja foi gravado fica salvo.
echo.
"bin\OperacaoLocalJson.exe" processar %*
set "codigo=%ERRORLEVEL%"
echo.
if not "%codigo%"=="0" echo O processamento terminou com codigo %codigo%. Leia a mensagem acima; os JSONs ja gravados foram preservados.
pause
exit /b %codigo%
