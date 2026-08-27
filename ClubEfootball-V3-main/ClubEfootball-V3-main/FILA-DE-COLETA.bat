@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title A FILA DE COLETA - o que perguntar, a quem, em que ordem
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\fila_de_coleta.py"
echo.
echo  ============================================================
echo   A FILA DE COLETA   -   passo 5, primeira metade
echo  ============================================================
echo.
echo   O sistema tinha o MAPA do que falta, mas nao tinha a FILA:
echo   quais cartas perguntar, a qual fonte, em que ordem.
echo.
echo   Ele descobre os campos NA BASE, nao numa lista escrita a
echo   mao. Campo sem regra declarada faz o programa PARAR - foi
echo   assim que 6.333 cartas ficaram sem idade por dias sem
echo   nenhum relatorio apontar.
echo.
echo   Separa em duas filas: a que roda sozinha e a que so anda
echo   com o navegador aberto. E marca desde quando cada coisa
echo   esta em NAO SEI, para o prazo de 2 dias.
echo.
echo   NAO coleta nada. NAO escreve no banco. So le e grava.
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
pause
