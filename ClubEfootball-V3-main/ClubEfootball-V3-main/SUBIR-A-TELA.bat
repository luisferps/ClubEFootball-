@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title SUBIR O QUE A TELA LE
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\subir_a_tela.py"
echo.
echo  ============================================================
echo   SUBIR O QUE A TELA LE
echo  ============================================================
echo.
echo   Sobe os quatro insumos que a tela le e que nao tinham
echo   tabela no banco:
echo.
echo      regra.json              -^> insumo_regra_funcao
echo      meu_time.json           -^> meu_time
echo      campanhas_efhub.json    -^> campanha
echo      efscout_campanhas.json  -^> campanha + insumo_player_type
echo.
echo   ⛔ RODE ANTES o sql\26-o-que-a-tela-le.sql no Supabase.
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
