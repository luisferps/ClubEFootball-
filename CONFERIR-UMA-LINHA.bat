@echo off
chcp 65001 >nul
title CONFERIR UMA LINHA
cd /d "%~dp02-MOTORES"
if not exist "OTIMIZADOR\conferir_uma.py" (
  echo   ^>^> nao achei conferir_uma.py em 2-MOTORES\OTIMIZADOR.
  pause
  exit /b 1
)
echo.
python OTIMIZADOR\conferir_uma.py 123236838963522 2 > "%~dp0CONFERENCIA.txt" 2>&1
type "%~dp0CONFERENCIA.txt"
echo.
echo  ------------------------------------------------------------
echo   Tambem ficou salvo em CONFERENCIA.txt, na pasta de cima.
echo  ------------------------------------------------------------
echo.
pause
