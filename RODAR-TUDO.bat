@echo off
chcp 65001 >nul
title RODAR O MOTOR - a fila inteira
cd /d "%~dp02-MOTORES"
set PARAR_EM=0

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
echo   O MOTOR - A FILA INTEIRA
echo  ============================================================
echo.
echo   So rode isto DEPOIS que as primeiras 100 forem conferidas.
echo.
echo   Para parar: crie um arquivo PARAR.txt dentro de 2-MOTORES.
echo   O que ja rodou nao se perde - grava linha a linha no banco.
echo.
echo  ------------------------------------------------------------
echo.
python OTIMIZADOR\roda_lote_v6.py
echo.
pause
