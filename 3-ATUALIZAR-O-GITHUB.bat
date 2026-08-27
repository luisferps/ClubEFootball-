@echo off
chcp 65001 >nul
title 3 - ATUALIZAR O GITHUB
cd /d "%~dp0"
set "LOG=%~dp0_ERRO-DO-GITHUB.txt"

echo ============================================ > "%LOG%"
echo  LOG DO ATUALIZAR-O-GITHUB >> "%LOG%"
echo  %DATE% %TIME% >> "%LOG%"
echo ============================================ >> "%LOG%"

echo.
echo  ============================================================
echo   ATUALIZAR O GITHUB
echo  ============================================================
echo.

where git >nul 2>&1
if errorlevel 1 (
  echo   ^>^> O GIT NAO FOI ENCONTRADO. Reinicie o computador.
  echo GIT NAO ENCONTRADO >> "%LOG%"
  pause
  exit /b 1
)

if not exist ".git" (
  echo   ^>^> Esta pasta ainda nao e um repositorio.
  echo      Rode o 2-SUBIR-PRO-GITHUB.bat primeiro.
  pause
  exit /b 1
)

findstr /C:"config.txt" ".gitignore" >nul 2>&1
if errorlevel 1 (
  echo   ^>^> PAREI. O .gitignore NAO tem o config.txt.
  echo GITIGNORE SEM CONFIG.TXT >> "%LOG%"
  pause
  exit /b 1
)
echo   ok: a chave esta protegida

echo   ---- juntando os arquivos
git add -A >> "%LOG%" 2>&1

git status --short | findstr /C:"config.txt" >nul
if not errorlevel 1 (
  echo   ^>^> PAREI. O config.txt entrou na lista. A chave subiria.
  echo CONFIG.TXT NA LISTA - PAREI >> "%LOG%"
  pause
  exit /b 1
)
echo   ok: o config.txt ficou de fora

echo. >> "%LOG%"
echo ---- o que muda >> "%LOG%"
git status --short >> "%LOG%" 2>&1

echo   ---- gravando...
git -c user.name="Luis Fernando" -c user.email="luis.soares.177@gmail.com" commit -m "atualizacao" >> "%LOG%" 2>&1

echo   ---- subindo...
git push origin main >> "%LOG%" 2>&1
set RESULTADO=%errorlevel%
echo ---- codigo de saida do push: %RESULTADO% >> "%LOG%"

echo.
echo  ============================================================
if "%RESULTADO%"=="0" (
  echo   SUBIU. github.com/luisferps/ClubEFootball-
) else (
  echo   DEU ERRO. Me mande o arquivo  _ERRO-DO-GITHUB.txt
)
echo  ============================================================
echo.
pause
