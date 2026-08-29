@echo off
chcp 65001 >nul
setlocal
title 3 - ATUALIZAR O GITHUB
cd /d "%~dp0"
set "LOG=%TEMP%\cf-subir.log"

echo ============================================ > "%LOG%"
echo  ATUALIZAR O GITHUB  %DATE% %TIME% >> "%LOG%"
echo ============================================ >> "%LOG%"

echo.
echo  ============================================================
echo   ATUALIZAR O GITHUB
echo  ============================================================
echo.

where git >nul 2>&1
if errorlevel 1 (
  echo   ^>^> O GIT NAO FOI ENCONTRADO. Reinicie o computador.
  pause
  exit /b 1
)

if not exist ".git" (
  echo   ^>^> Esta pasta ainda nao e um repositorio.
  echo      Rode o 2-SUBIR-PRO-GITHUB.bat primeiro.
  pause
  exit /b 1
)

if not exist ".gitignore" (
  echo   ^>^> PAREI. Nao achei o .gitignore.
  pause
  exit /b 1
)
findstr /C:"config.txt" ".gitignore" >nul 2>&1
if errorlevel 1 (
  echo   ^>^> PAREI. O .gitignore NAO tem o config.txt.
  pause
  exit /b 1
)
echo   ok: a chave esta protegida

if exist "_ERRO-DO-GITHUB.txt" del /f /q "_ERRO-DO-GITHUB.txt" >nul 2>&1

echo   ---- juntando os arquivos
git add -A >> "%LOG%" 2>&1

git status --short | findstr /C:"config.txt" >nul
if not errorlevel 1 (
  echo   ^>^> PAREI. O config.txt entrou na lista. A chave subiria.
  pause
  exit /b 1
)
echo   ok: o config.txt ficou de fora

echo. >> "%LOG%"
echo ---- o que muda >> "%LOG%"
git status --short >> "%LOG%" 2>&1

echo   ---- gravando...
git -c user.name="Luis Fernando" -c user.email="luis.soares.177@gmail.com" commit -m "motores lendo do banco" >> "%LOG%" 2>&1

echo   ---- subindo...
git push origin main >> "%LOG%" 2>&1
set RESULTADO=%errorlevel%

echo.
echo  ============================================================
if "%RESULTADO%"=="0" (
  echo   SUBIU. github.com/luisferps/ClubEFootball-
) else (
  echo   DEU ERRO. O log esta em:
  echo   %LOG%
)
echo  ============================================================
echo.
pause
