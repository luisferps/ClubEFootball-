@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title OS QUATRO ESTADOS DE CADA DADO
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\estados.py"
echo.
echo  ============================================================
echo   OS QUATRO ESTADOS DE CADA DADO
echo  ============================================================
echo.
echo   valor          puxou e veio numero        nao e pendencia
echo   zerado         puxou, o campo e 0         nao e pendencia
echo   nao se aplica  conferiu, nao existe       nao e pendencia
echo   NAO SEI        ninguem puxou              E PENDENCIA
echo.
echo   Grava dados\estado_de_cada_campo.json e sobe para o banco.
echo   NAO mexe no base_unica.json. NAO mexe em pontuacao nenhuma.
echo.
echo  ------------------------------------------------------------
python "%PY%" %1
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima.
  echo      Se reclamou de coluna que nao existe, abra antes o
  echo      CRIAR-ESTADOS-NO-SUPABASE.html e siga os passos.
  echo.
  pause
  exit /b 1
)
echo.
pause
