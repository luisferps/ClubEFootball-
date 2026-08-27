@echo off
chcp 65001 >nul
setlocal

rem  O git reescreve TODOS os arquivos da pasta - inclusive este .bat.
rem  O cmd.exe le o .bat do disco linha a linha enquanto roda; se o arquivo
rem  muda de tamanho no meio, ele continua lendo do lugar errado e executa
rem  lixo ("'t' nao e reconhecido"). Por isso o script se copia para a pasta
rem  temporaria e roda de la, mexendo na pasta original de fora.

if /I "%~1"=="DELA" goto TRABALHO

set "ORIGEM=%~dp0"
set "ORIGEM=%ORIGEM:~0,-1%"
copy /Y "%~f0" "%TEMP%\cf-baixar.bat" >nul
"%TEMP%\cf-baixar.bat" DELA "%ORIGEM%"
exit /b


:TRABALHO
set "PASTA=%~2"
set "LOG=%TEMP%\cf-baixar.log"
title 4 - BAIXAR DO GITHUB

echo ============================================ > "%LOG%"
echo  BAIXAR DO GITHUB  %DATE% %TIME% >> "%LOG%"
echo  pasta: %PASTA% >> "%LOG%"
echo ============================================ >> "%LOG%"

echo.
echo  ============================================================
echo   BAIXAR DO GITHUB
echo  ============================================================
echo.
echo   Pasta: %PASTA%
echo.
echo   Traz a versao mais nova, jogando por cima do que estiver ai.
echo   O config.txt NAO e tocado - a chave fica onde esta.
echo.
pause

where git >nul 2>&1
if errorlevel 1 (
  echo   ^>^> O GIT NAO FOI ENCONTRADO. Reinicie o computador.
  echo.
  pause
  exit /b 1
)

if not exist "%PASTA%" (
  echo   ^>^> nao achei a pasta %PASTA%
  pause
  exit /b 1
)

cd /d "%PASTA%"

if not exist ".git" (
  echo   ---- primeira vez nesta maquina
  git init >> "%LOG%" 2>&1
  git branch -M main >> "%LOG%" 2>&1
  git remote remove origin >> "%LOG%" 2>&1
  git remote add origin https://github.com/luisferps/ClubEFootball-.git >> "%LOG%" 2>&1
)

echo   ---- guardando o config.txt
if exist "2-MOTORES\config.txt" copy /Y "2-MOTORES\config.txt" "%TEMP%\cf-config.txt" >nul
if exist "config.txt"           copy /Y "config.txt"           "%TEMP%\cf-config.txt" >nul

echo   ---- tirando da frente os arquivos de log
if exist "_ERRO-DO-GITHUB.txt" del /f /q "_ERRO-DO-GITHUB.txt" >nul 2>&1

echo   ---- buscando...
git fetch origin main >> "%LOG%" 2>&1
if errorlevel 1 (
  echo   ^>^> nao consegui falar com o GitHub. Log em: %LOG%
  pause
  exit /b 1
)

echo   ---- aplicando...
git reset --hard FETCH_HEAD >> "%LOG%" 2>&1
set RESULTADO=%errorlevel%
git branch -f main FETCH_HEAD >> "%LOG%" 2>&1
git checkout main >> "%LOG%" 2>&1

echo   ---- devolvendo o config.txt
if exist "%TEMP%\cf-config.txt" (
  if not exist "2-MOTORES" mkdir "2-MOTORES"
  copy /Y "%TEMP%\cf-config.txt" "2-MOTORES\config.txt" >nul
  del /f /q "%TEMP%\cf-config.txt" >nul 2>&1
  echo        config.txt de volta em 2-MOTORES
)

echo.
echo  ============================================================
if "%RESULTADO%"=="0" (
  echo   BAIXOU.
  echo.
  echo   Se esta maquina ainda nao tem a chave: CRIAR-CONFIG.bat
  echo   Depois: RODAR-O-MOTOR.bat
) else (
  echo   DEU ERRO. O log esta em:
  echo   %LOG%
  echo   Abra ele e me mande o conteudo.
)
echo  ============================================================
echo.
pause
