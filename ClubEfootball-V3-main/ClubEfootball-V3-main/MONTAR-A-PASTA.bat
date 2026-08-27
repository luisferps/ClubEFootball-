@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title MONTAR A PASTA - so o que o sistema precisa
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\montar_a_pasta.py"
cls
echo.
echo  ================================================================
echo    MONTAR A PASTA   -   ClubEfootball
echo  ================================================================
echo.
echo    Copia para a ClubEfootball SO o que o sistema precisa para
echo    funcionar. O resto fica onde esta.
echo.
echo    COMO ELE DECIDE, medindo e nao chutando:
echo.
echo      1. todo .bat e uma porta de entrada - e o que voce clica
echo      2. de cada .bat, ve qual .py ele chama
echo      3. de cada .py, segue os import ate o fim
echo      4. de cada .py, ve qual arquivo de dado ele abre
echo      5. repete ate parar de crescer
echo.
echo    O que nenhum clique seu alcanca e ORFAO, fica para tras, e
echo    a lista dele e escrita para voce olhar.
echo.
echo    ^>^> NADA E APAGADO. So copia.
echo.
echo  ----------------------------------------------------------------
pause
python "%PY%"
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima. Nada foi apagado.
  echo.
  pause
  exit /b 1
)
echo.
echo    Abra o O-QUE-FICOU-PARA-TRAS.txt e veja se concorda com a lista.
echo.
pause
