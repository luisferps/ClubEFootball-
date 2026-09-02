@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Enviar resultados JSON
if not exist "bin\OperacaoLocalJson.exe" (
  echo O programa de envio local nao foi encontrado.
  echo Copie a pasta OPERACAO-LOCAL-JSON completa, incluindo bin.
  pause
  exit /b 1
)
echo.
echo ENVIO: cada linha e confirmada separadamente pelo banco.
echo A data e hora confirmada ficam no recibo local e na linha do banco.
echo Para parar com seguranca, pressione Ctrl+C. Nada confirmado sera enviado de novo.
echo.
"bin\OperacaoLocalJson.exe" enviar
set "codigo=%ERRORLEVEL%"
echo.
if not "%codigo%"=="0" echo O envio parou com codigo %codigo%. Nenhum JSON foi apagado.
pause
exit /b %codigo%
