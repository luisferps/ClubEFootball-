@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title CONFERIR AS BOX - nao grava nada
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\entrar_com_as_box.py"
if not exist "%PY%" set "PY=%~dp0ClubEfootball\programas\entrar_com_as_box.py"
echo.
echo  ============================================================
echo   ENTRAR COM AS BOX DO efHUB
echo  ============================================================
echo.
echo   O navegador colheu, este entra com o que veio.
echo.
echo   Ele responde tres coisas:
echo     1. quais BOX o efHub tem e nos nao
echo     2. quais CARTAS aparecem nessas box e faltam na base
echo     3. preenche o nome da box onde estava vazio
echo.
echo   NAO escreve data. A data que o efHub da em cada box e a
echo   coleta SEMANAL deles, nao o lancamento - medido em 17/08:
echo   a box "Summer Transfer 17 Aug '26" vem com data 13/08.
echo   A data de lancamento sai do NOME da box, no programa
echo   SEPARAR-A-DATA-DO-BOX.
echo.
echo   NAO fala com o banco. NAO apaga nada. Faz backup antes.
echo.
echo   Precisa do arquivo efhub_boxes.json nesta pasta. Ele nasce
echo   no ClubEfootball\COLETAR-AS-BOX-NO-EFHUB.html
echo.
echo  MODO CONFERIR: nada vai ser gravado.
  ------------------------------------------------------------
python "%PY%" --conferir
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima.
  echo.
  pause
  exit /b 1
)
echo.
pause
