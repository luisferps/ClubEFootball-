@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title O QUE O BANCO TEM
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\o_que_o_banco_tem.py"
echo.
echo  ============================================================
echo   O QUE O BANCO TEM
echo  ============================================================
echo.
echo   Pergunta ao banco quais colunas a cards_base tem, conta
echo   quantas cartas tem cada uma, e cruza com o base_unica.json.
echo.
echo   Responde tres coisas:
echo     1. o que o motor le e o banco NAO tem
echo     2. o que o banco tem e o motor NAO recebe
echo     3. duas colunas para a mesma coisa
echo.
echo   NAO escreve nada. Pode rodar com o motor rodando.
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
