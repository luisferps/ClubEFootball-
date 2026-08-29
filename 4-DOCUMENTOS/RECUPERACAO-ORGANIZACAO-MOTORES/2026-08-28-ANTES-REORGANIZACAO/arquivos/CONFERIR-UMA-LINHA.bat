@echo off
chcp 65001 >nul
title CONFERIR UMA LINHA
cd /d "%~dp02-MOTORES"
if not exist "conferir_uma.py" (
  if exist "%~dp0conferir_uma.py" copy /Y "%~dp0conferir_uma.py" "conferir_uma.py" >nul
)
echo.
python conferir_uma.py 123236838963522 2 > "%~dp0CONFERENCIA.txt" 2>&1
type "%~dp0CONFERENCIA.txt"
echo.
echo  ------------------------------------------------------------
echo   Tambem ficou salvo em CONFERENCIA.txt, na pasta de cima.
echo  ------------------------------------------------------------
echo.
pause
