@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Otimizador - Enviar fila ativa continuamente

if not exist "bin\OperacaoLocalJson.exe" (
  echo O programa local nao foi encontrado.
  pause
  exit /b 1
)

echo.
echo ENVIO CONTINUO DA FILA PRINCIPAL
echo Envia os JSONs prontos e acompanha o Otimizador enquanto ele estiver ativo.
echo Para parar com seguranca, pressione Ctrl+C. Os recibos ficam salvos.
echo.

:VIGIAR_FILA
dir /b /s "RESULTADOS-JSON\resultado-*.json" 2>nul | findstr /i /c:"PENDENTES" >nul
if errorlevel 1 goto AGUARDAR_JSON

"bin\OperacaoLocalJson.exe" enviar %*
set "codigo=%ERRORLEVEL%"
if not "%codigo%"=="0" goto ERRO_ENVIO

:AGUARDAR_JSON
echo [%time:~0,8%] Aguardando o proximo JSON de 100 linhas... Ctrl+C para parar.
timeout /t 5 /nobreak >nul
goto VIGIAR_FILA

:ERRO_ENVIO
echo.
echo O envio terminou com codigo %codigo%. Leia a mensagem acima; nada foi apagado.
pause
exit /b %codigo%
