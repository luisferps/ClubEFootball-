@echo off
setlocal
cd /d "%~dp0"
title Bonificador - Processar fila canônica
chcp 65001 >nul

if not exist "..\..\config.txt" (
  echo ERRO: a configuracao compartilhada 2-MOTORES\config.txt nao foi encontrada.
  echo Mantenha a pasta BONIFICADOR dentro de 2-MOTORES.
  goto :fim_erro
)

set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD where python >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
  echo ERRO: Python 3 nao foi encontrado neste computador.
  echo Instale o Python 3 ou use a instalacao operacional do ClubeEfootball.
  goto :fim_erro
)

%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 3)" >nul 2>nul
if errorlevel 1 (
  echo ERRO: o Python encontrado e incompativel. O Bonificador exige Python 3.10 ou superior.
  %PYTHON_CMD% --version
  goto :fim_erro
)

set "PYTHONUTF8=1"
if "%~1"=="" goto :confirmar
goto :executar

:confirmar
echo.
echo FILA CANONICA DO BONIFICADOR
echo Esta tarefa calcula e grava somente os resultados confirmados pelo writer novo.
echo Para apenas consultar o estado, use: PROCESSAR-FILA-BONIFICADOR.bat status
echo.
set /p "CONFIRMA=Iniciar ou retomar o lote agora? [S/N]: "
if /i not "%CONFIRMA%"=="S" (
  echo Nenhum processamento foi iniciado.
  set "codigo=0"
  goto :fim
)
%PYTHON_CMD% operacao_lote.py processar
set "codigo=%ERRORLEVEL%"
goto :fim

:executar
%PYTHON_CMD% operacao_lote.py %*
set "codigo=%ERRORLEVEL%"
goto :fim

:fim_erro
set "codigo=1"

:fim
echo.
if not "%codigo%"=="0" echo A tarefa terminou com codigo %codigo%. Leia a mensagem acima; resultados com readback permanecem salvos.
if /i "%CLUBEF_SEM_PAUSA%"=="1" exit /b %codigo%
pause
exit /b %codigo%
