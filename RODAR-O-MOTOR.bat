@echo off
chcp 65001 >nul
title RODAR O MOTOR - primeiras 100, para conferir
cd /d "%~dp02-MOTORES"
set PARAR_EM=100

if not exist "OTIMIZADOR\roda_lote_v6.py" (
  echo   ^>^> nao achei roda_lote_v6.py em 2-MOTORES\OTIMIZADOR.
  pause
  exit /b 1
)
if not exist "config.txt" (
  if exist "%~dp0config.txt" ( copy /Y "%~dp0config.txt" "config.txt" >nul ) else (
    echo   ^>^> NAO ACHEI o config.txt. Rode o CRIAR-CONFIG.bat primeiro.
    pause
    exit /b 1
  )
)
if exist "PARAR.txt" del /q "PARAR.txt"

echo.
echo  ============================================================
echo   O MOTOR - PRIMEIRAS 100 LINHAS
echo  ============================================================
echo.
echo   Roda 100 e PARA. Sao as cartas que ja rodaram antes, para
echo   comparar com o arquivo antes de soltar as 125 mil.
echo.
echo   Depois de conferido: RODAR-TUDO.bat
echo.
echo  ------------------------------------------------------------
echo.
python OTIMIZADOR\roda_lote_v6.py
echo.
pause
