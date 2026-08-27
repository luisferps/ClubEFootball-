@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title SUBIR O QUE SO EXISTIA NA MAQUINA
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\subir_o_local.py"
echo.
echo  ============================================================
echo   SUBIR O QUE SO EXISTIA NA MAQUINA
echo  ============================================================
echo.
echo   Estes quatro nao tem fonte externa nenhuma. Todo o resto o
echo   sistema recoleta; estes nao:
echo.
echo      falta_por_card ............ 2.420 cartas
echo      raras_por_card .............. 707 cartas
echo      impeto_conferido_no_jogo .... 291 cartas ^(voce olhou no jogo^)
echo      CONFERIDO ..................... 6 cartas
echo.
echo   ⛔ RODE ANTES o sql\29-o-que-so-existia-na-maquina.sql
echo   ⛔ Nao apaga nada. Rodar duas vezes nao duplica.
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
