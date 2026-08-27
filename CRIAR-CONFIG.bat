@echo off
chcp 65001 >nul
title CRIAR O CONFIG.TXT - a chave do banco
cd /d "%~dp0"
set "DESTINO=%~dp02-MOTORES"

echo.
echo  ============================================================
echo   CRIAR O CONFIG.TXT
echo  ============================================================
echo.
echo   A chave NAO vai para o GitHub. Por isso cada maquina cria
echo   o config.txt na mao, uma vez so.
echo.

if not exist "%DESTINO%" mkdir "%DESTINO%"

if exist "%DESTINO%\config.txt" (
  echo   ^>^> JA EXISTE um config.txt em 2-MOTORES.
  echo      Se quiser trocar a chave, apague ele e rode de novo.
  echo.
  pause
  exit /b 0
)

echo   Pegue a chave SECRET em:
echo   https://supabase.com/dashboard/project/trqqpsnafpbudtvvicch/settings/api-keys
echo.
set /p CHAVE="   Cole a chave aqui e aperte Enter: "
if "%CHAVE%"=="" (
  echo   ^>^> Nada foi colado. Nao criei nada.
  pause
  exit /b 1
)

(
echo SUPABASE_URL=https://trqqpsnafpbudtvvicch.supabase.co
echo SUPABASE_KEY=%CHAVE%
) > "%DESTINO%\config.txt"

copy /Y "%DESTINO%\config.txt" "%~dp0config.txt" >nul

echo.
echo   ^>^> config.txt criado em 2-MOTORES.
echo.
echo   Agora rode o  RODAR-O-MOTOR.bat
echo.
pause
