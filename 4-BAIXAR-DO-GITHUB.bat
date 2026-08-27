@echo off
chcp 65001 >nul
title 4 - BAIXAR DO GITHUB
cd /d "%~dp0"
set "LOG=%~dp0_ERRO-DO-GITHUB.txt"

echo ============================================ > "%LOG%"
echo  LOG DO BAIXAR-DO-GITHUB >> "%LOG%"
echo  %DATE% %TIME% >> "%LOG%"
echo ============================================ >> "%LOG%"

echo.
echo  ============================================================
echo   BAIXAR DO GITHUB
echo  ============================================================
echo.
echo   Traz a versao mais nova. O config.txt desta maquina
echo   NAO e tocado - a chave fica onde esta.
echo.
pause

where git >nul 2>&1
if errorlevel 1 (
  echo   ^>^> O GIT NAO FOI ENCONTRADO. Reinicie o computador.
  pause
  exit /b 1
)

if not exist ".git" (
  echo   ---- primeira vez nesta maquina
  git init >> "%LOG%" 2>&1
  git branch -M main >> "%LOG%" 2>&1
  git remote add origin https://github.com/luisferps/ClubEFootball-.git >> "%LOG%" 2>&1
)

echo   ---- buscando...
git fetch origin main >> "%LOG%" 2>&1
git reset --hard origin/main >> "%LOG%" 2>&1
set RESULTADO=%errorlevel%
echo ---- codigo de saida: %RESULTADO% >> "%LOG%"

echo.
echo  ============================================================
if "%RESULTADO%"=="0" (
  echo   BAIXOU. Agora rode o CRIAR-CONFIG.bat se esta maquina
  echo   ainda nao tem a chave, e depois RODAR-O-MOTOR.bat
) else (
  echo   DEU ERRO. Me mande o arquivo  _ERRO-DO-GITHUB.txt
)
echo  ============================================================
echo.
pause
