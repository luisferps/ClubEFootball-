@echo off
chcp 65001 > nul
title 2 - SUBIR PRO GITHUB
cd /d "%~dp0"
set LOG=%~dp0_ERRO-DO-GITHUB.txt

echo ============================================ > "%LOG%"
echo  LOG DO SUBIR-PRO-GITHUB >> "%LOG%"
echo  %DATE% %TIME% >> "%LOG%"
echo ============================================ >> "%LOG%"
echo. >> "%LOG%"

echo.
echo  ============================================================
echo   SUBIR PRO GITHUB
echo  ============================================================
echo.
echo   Tudo que acontecer fica gravado em _ERRO-DO-GITHUB.txt
echo   Se der errado, e so me mandar esse arquivo.
echo.

echo ---- o git esta instalado? >> "%LOG%"
where git >> "%LOG%" 2>&1
if errorlevel 1 (
  echo   ^>^> O GIT NAO FOI ENCONTRADO.
  echo      Feche TODAS as janelas do Explorer e abra de novo.
  echo      Se nao resolver, reinicie o computador.
  echo GIT NAO ENCONTRADO >> "%LOG%"
  echo.
  pause
  exit /b 1
)
git --version >> "%LOG%" 2>&1
echo   ok: git instalado

echo. >> "%LOG%"
echo ---- o .gitignore protege a chave? >> "%LOG%"
if not exist ".gitignore" (
  echo   ^>^> NAO ACHEI o .gitignore. PAREI.
  echo SEM GITIGNORE >> "%LOG%"
  pause
  exit /b 1
)
findstr /C:"config.txt" ".gitignore" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo   ^>^> PAREI. O .gitignore NAO tem o config.txt.
  echo GITIGNORE SEM CONFIG.TXT >> "%LOG%"
  pause
  exit /b 1
)
echo   ok: a chave esta protegida

echo. >> "%LOG%"
echo ---- estado do repositorio local >> "%LOG%"
if not exist ".git" (
  echo   ---- primeira vez: criando o repositorio local
  echo PRIMEIRA VEZ - git init >> "%LOG%"
  git init >> "%LOG%" 2>&1
  git branch -M main >> "%LOG%" 2>&1
  git remote add origin https://github.com/luisferps/ClubEFootball-.git >> "%LOG%" 2>&1
) else (
  echo REPOSITORIO JA EXISTE >> "%LOG%"
  git remote -v >> "%LOG%" 2>&1
  git remote remove origin >> "%LOG%" 2>&1
  git remote add origin https://github.com/luisferps/ClubEFootball-.git >> "%LOG%" 2>&1
)

echo.
echo   ---- juntando os arquivos (pode demorar um pouco)
echo. >> "%LOG%"
echo ---- git add >> "%LOG%"
git add -A >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo ---- o config.txt escapou? (tem que dar VAZIO) >> "%LOG%"
git status --short | findstr /C:"config.txt" >> "%LOG%" 2>&1
git status --short | findstr /C:"config.txt" > nul
if not errorlevel 1 (
  echo.
  echo   ^>^> PAREI. O config.txt entrou na lista. A chave subiria.
  echo CONFIG.TXT NA LISTA - PAREI >> "%LOG%"
  pause
  exit /b 1
)
echo   ok: o config.txt ficou de fora

echo. >> "%LOG%"
echo ---- quantos arquivos vao subir >> "%LOG%"
git status --short >> "%LOG%" 2>&1

echo.
echo   ---- gravando...
echo. >> "%LOG%"
echo ---- git commit >> "%LOG%"
git -c user.name="Luis Fernando" -c user.email="luis.soares.177@gmail.com" commit -m "ClubEfootball V4 - motores lendo do banco" >> "%LOG%" 2>&1

echo.
echo   ---- subindo (pode abrir uma janela de login do GitHub)
echo. >> "%LOG%"
echo ---- git push >> "%LOG%"
git push -u origin main >> "%LOG%" 2>&1
set RESULTADO=%errorlevel%

echo. >> "%LOG%"
echo ---- codigo de saida do push: %RESULTADO% >> "%LOG%"

echo.
echo  ============================================================
if "%RESULTADO%"=="0" (
  echo   SUBIU. Confira em github.com/luisferps/ClubEFootball-
) else (
  echo   DEU ERRO. Me mande o arquivo  _ERRO-DO-GITHUB.txt
  echo   Ele esta nesta mesma pasta.
)
echo  ============================================================
echo.
pause
