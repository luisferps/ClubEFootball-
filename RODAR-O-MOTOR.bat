@echo off
chcp 65001 >nul
title RODAR O MOTOR
cd /d "%~dp02-MOTORES"

if not exist "roda_lote_v6.py" (
  echo.
  echo   ^>^> nao achei roda_lote_v6.py em 2-MOTORES.
  echo      Rode o 0-ARRUMAR-O-V4.bat primeiro.
  echo.
  pause
  exit /b 1
)

if not exist "config.txt" (
  if exist "%~dp0config.txt" (
    copy /Y "%~dp0config.txt" "config.txt" >nul
    echo   copiei o config.txt da pasta de cima.
  ) else (
    echo.
    echo   ^>^> NAO ACHEI o config.txt.
    echo      Rode o CRIAR-CONFIG.bat primeiro.
    echo.
    pause
    exit /b 1
  )
)

if exist "PARAR.txt" del /q "PARAR.txt"

echo.
echo  ============================================================
echo   O MOTOR
echo  ============================================================
echo.
echo   Le a fila do BANCO. Nao usa arquivo nenhum.
echo   As cartas que JA RODARAM antes vem primeiro, para conferir.
echo.
echo   Para parar: crie um arquivo PARAR.txt dentro de 2-MOTORES.
echo   O que ja rodou nao se perde - grava linha a linha no banco.
echo.
echo  ------------------------------------------------------------
echo.
python roda_lote_v6.py
echo.
pause
