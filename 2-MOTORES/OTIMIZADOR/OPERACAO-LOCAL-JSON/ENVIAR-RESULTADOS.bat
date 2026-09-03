@echo off
setlocal
cd /d "%~dp0"
title Otimizador - Enviar resultados ao banco

rem Faltava no repositorio: ENVIAR-CORRECAO-IMPETOS-V8.bat chama este arquivo,
rem que nunca subiu. Numa copia recem-baixada do GitHub aquele botao morria com
rem "o sistema nao pode encontrar o arquivo". Aceita os mesmos parametros do
rem executavel: --lote e --limite.

if not exist "bin\OperacaoLocalJson.exe" (
  echo O programa local nao foi encontrado.
  echo Copie a pasta OPERACAO-LOCAL-JSON completa, incluindo bin.
  pause
  exit /b 1
)

echo.
echo ENVIO AO BANCO: cada linha e confirmada uma a uma.
echo Para parar com seguranca, pressione Ctrl+C. Os recibos ficam salvos.
echo.

"bin\OperacaoLocalJson.exe" enviar %*
set "codigo=%ERRORLEVEL%"
echo.
if not "%codigo%"=="0" echo O envio terminou com codigo %codigo%. Leia a mensagem acima; nada foi apagado.
pause
exit /b %codigo%
