@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title SUBIR OS IMPETOS - o catalogo e o impeto de cada card
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
if not exist "IMPETOS.json" (
  echo.
  echo   ^>^> nao achei o IMPETOS.json.
  echo      Rode o SEPARAR-OS-IMPETOS.bat primeiro.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\subir_os_impetos.py"
echo.
echo  ============================================================
echo   SUBIR OS IMPETOS PARA O BANCO
echo  ============================================================
echo.
echo   Poe no banco o que o SEPARAR-OS-IMPETOS.bat gravou:
echo.
echo      impeto ............. o catalogo, com o id DO JOGO
echo      impeto_atributo .... o que cada um aumenta, e em quanto
echo      card_impeto ........ o impeto de cada card
echo.
echo   NAO calcula nada. Se o numero estiver errado na pasta, sobe
echo   errado - o lugar de consertar e o separar_os_impetos.py.
echo.
echo   No fim ele PERGUNTA AO BANCO quantas linhas entraram, em vez
echo   de repetir quantas mandou. Ja aconteceu de dizer 494 subidas
echo   com o banco em zero.
echo.
echo   Pode rodar quantas vezes quiser: as tabelas tem chave, nao
echo   duplica.
echo.
echo  ------------------------------------------------------------
python "%PY%"
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU ou nao fechou. Leia o motivo acima.
  echo.
  pause
  exit /b 1
)
echo.
pause
