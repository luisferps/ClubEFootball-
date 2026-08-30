@echo off
chcp 65001 >nul
setlocal
title 3 - PUBLICAR TODAS AS ALTERACOES
cd /d "%~dp0"
set "LOG=%TEMP%\cf-subir.log"
set "REPO_ESPERADO=https://github.com/luisferps/ClubEFootball-.git"
set "REPO_ATUAL="

echo ============================================ > "%LOG%"
echo  ATUALIZAR O GITHUB  %DATE% %TIME% >> "%LOG%"
echo ============================================ >> "%LOG%"

echo.
echo  ============================================================
echo   3 - PUBLICAR TODAS AS ALTERACOES
echo  ============================================================
echo.
echo   Pasta publicada:
echo   %CD%
echo.
echo   Este botao adiciona, grava e envia TODAS as alteracoes locais.
echo   Ele deve ser usado neste repositorio Main ja existente.
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

for /f "delims=" %%R in ('git remote get-url origin 2^>nul') do set "REPO_ATUAL=%%R"
if /I not "%REPO_ATUAL%"=="%REPO_ESPERADO%" (
  echo   ^>^> PAREI. O origin nao e o GitHub esperado.
  echo      Esperado: %REPO_ESPERADO%
  echo      Encontrado: %REPO_ATUAL%
  pause
  exit /b 1
)
echo   ok: repositorio GitHub correto

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
findstr /C:".env" ".gitignore" >nul 2>&1
if errorlevel 1 (
  echo   ^>^> PAREI. O .gitignore nao protege arquivos .env.
  pause
  exit /b 1
)
findstr /C:"*.key" ".gitignore" >nul 2>&1
if errorlevel 1 (
  echo   ^>^> PAREI. O .gitignore nao protege arquivos de chave.
  pause
  exit /b 1
)
echo   ok: configuracoes e chaves locais estao protegidas

if exist "_ERRO-DO-GITHUB.txt" del /f /q "_ERRO-DO-GITHUB.txt" >nul 2>&1

echo   ---- juntando os arquivos
git add -A >> "%LOG%" 2>&1
if errorlevel 1 (
  echo   ^>^> PAREI. O Git nao conseguiu preparar todos os arquivos.
  echo GIT ADD FALHOU >> "%LOG%"
  pause
  exit /b 1
)

set "ARQUIVO_SENSIVEL="
for /f "delims=" %%F in ('git diff --cached --name-only --diff-filter=ACMR -- "config.txt" ".env" ".env.*" "*.key" "*.pem" "*.secret" "*.secrets" "credenciais.local.*" "configuracao.local.*"') do (
  if /I not "%%~nxF"==".env.example" set "ARQUIVO_SENSIVEL=%%F"
)
if defined ARQUIVO_SENSIVEL (
  echo   ^>^> PAREI. Um arquivo sensivel entrou na lista:
  echo      %ARQUIVO_SENSIVEL%
  echo      Nada foi gravado nem enviado. Remova-o da area preparada.
  pause
  exit /b 1
)
echo   ok: nenhum arquivo sensivel entrou na publicacao

echo. >> "%LOG%"
echo ---- o que muda >> "%LOG%"
git status --short >> "%LOG%" 2>&1

echo   ---- gravando...
git -c user.name="Luis Fernando" -c user.email="luis.soares.177@gmail.com" commit -m "Atualizar todos os arquivos locais" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo   ^>^> PAREI. O Git nao conseguiu criar o commit.
  echo      Nada foi enviado. Consulte o log: %LOG%
  pause
  exit /b 1
)

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
