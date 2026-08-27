@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title SO O MOTOR - roda a fila, sem coleta
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
echo.
echo  ============================================================
echo   SO O MOTOR
echo  ============================================================
echo.
echo   Roda as linhas que estao na fila e NAO coleta nada.
echo   Nenhuma carta e perguntada ao efHub por causa disto.
echo.
echo   Roda TUDO que estiver na fila sem resultado: o que a rodada
echo   identificou hoje E as funcoes novas das posicoes compradas.
echo   Toda carta delas ja esta na base com todo o insumo.
echo.
echo   >> CLIQUE ISTO DEPOIS QUE A RODADA-DIARIA TERMINAR.
echo      A rodada precisa do motor PARADO para o passo 5k poder
echo      reescrever o linhas.jsonl. Rodando os dois juntos, o
echo      arquivo corrompe no Windows.
echo.
echo   A ORDEM QUE ELE VAI SEGUIR:
echo     1. o que a rodada identificou hoje ... fila_PRIORIDADE
echo     2. as 6.228 basicas ................. por OVERALL, o maior primeiro
echo.
echo   Para parar no meio: crie um arquivo PARAR.txt nesta pasta.
echo   O que ja rodou nao se perde - ele grava linha a linha.
echo.
echo  ------------------------------------------------------------
if exist "LIGAR-MOTOR-AUTOMATICO.txt" (
  echo.
  echo   ^>^> PAREI. O LIGAR-MOTOR-AUTOMATICO.txt esta na pasta.
  echo      A rodada diaria vai abrir um segundo motor.
  echo      Apague ele antes de rodar este aqui.
  echo.
  pause
  exit /b 1
)
if exist "PARAR.txt" del "PARAR.txt"
echo.
python roda_lote_v6.py
echo.
pause
