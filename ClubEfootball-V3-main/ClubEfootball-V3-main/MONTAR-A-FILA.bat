@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title MONTAR A FILA - as duas funcoes de cada posicao comprada
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\monta_fila.py"
echo.
echo  ============================================================
echo   MONTAR A FILA
echo  ============================================================
echo.
echo   O QUE MUDOU (18/08):
echo     posicao COMPRADA agora roda as DUAS funcoes da familia,
echo     nao mais uma so escolhida sem criterio.
echo.
echo     linhas na fila antes .... 12.370
echo     linhas na fila depois ... 20.777
echo     linhas novas ............  8.393
echo.
echo   A ORDEM:
echo     1. ATIVAS  - onde o estilo da carta ativa. Lancamento fura a fila.
echo     2. BASICAS - as 8.393 novas, todas ATRAS. Sao aditivo.
echo.
echo   Cada linha leva um rotulo `estilo_ativa` para a tela poder
echo   separar ATIVA de BASICA no modal da carta.
echo.
echo   Ele NAO apaga linha ja rodada e NAO chama o motor.
echo.
echo  ------------------------------------------------------------
python "%PY%"
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima.
  echo.
  pause
  exit /b 1
)
echo.
echo   Pronto. Agora rode a RODADA-DIARIA.bat.
echo.
pause
