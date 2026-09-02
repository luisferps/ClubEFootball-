@echo off
setlocal
cd /d "%~dp0"
set "PROCESSADOR=OPERACAO-LOCAL-LOTE\PROCESSAR-FILA-BONIFICADOR.bat"
if not exist "%PROCESSADOR%" (
  echo ERRO DE INSTALACAO: PROCESSAR-FILA-BONIFICADOR.bat nao foi encontrado.
  echo Mantenha a pasta OPERACAO-LOCAL-LOTE completa dentro de 2-MOTORES\BONIFICADOR.
  if /i not "%CLUBEF_SEM_PAUSA%"=="1" pause
  exit /b 1
)
call "%PROCESSADOR%" %*
exit /b %ERRORLEVEL%
