@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem O primeiro processo só abre uma janela independente. A atualização roda
rem numa cópia temporária para que o próprio botão 4 possa ser substituído.
if /I "%~1"=="TRABALHO" goto TRABALHO
if /I "%~1"=="FINALIZAR" goto FINALIZAR

set "ORIGEM=%~dp0"
if "%ORIGEM:~-1%"=="\" set "ORIGEM=%ORIGEM:~0,-1%"
set "TEMP_SCRIPT=%TEMP%\clubef-baixar-%RANDOM%-%RANDOM%.bat"
copy /Y "%~f0" "%TEMP_SCRIPT%" >nul
if errorlevel 1 (
  echo Nao consegui preparar o atualizador temporario.
  pause
  exit /b 1
)
start "4 - BAIXAR DO GITHUB" cmd /k ""%TEMP_SCRIPT%" TRABALHO "%ORIGEM%""
exit /b

:TRABALHO
set "PASTA=%~2"
set "REPO=https://github.com/luisferps/ClubEFootball-.git"
set "LOG_TEMP=%TEMP%\clubef-github-%RANDOM%-%RANDOM%.log"
set "LOG_FINAL=%PASTA%\_ULTIMO-BAIXAR-DO-GITHUB.txt"
set "CFG_MOTOR=%TEMP%\clubef-config-motor-%RANDOM%-%RANDOM%.tmp"
set "CFG_RAIZ=%TEMP%\clubef-config-raiz-%RANDOM%-%RANDOM%.tmp"
set "BOOTSTRAP=0"
set "ANTES_SHA=SEM_HEAD"
set "REMOTO_SHA="
set "QTD_ALTERADOS=0"
title 4 - BAIXAR DO GITHUB
cls

>"%LOG_TEMP%" echo ============================================
>>"%LOG_TEMP%" echo BAIXAR DO GITHUB - %DATE% %TIME%
>>"%LOG_TEMP%" echo pasta: %PASTA%
>>"%LOG_TEMP%" echo repositorio: %REPO%
>>"%LOG_TEMP%" echo ============================================

echo.
echo ============================================================
echo  4 - BAIXAR DO GITHUB
echo ============================================================
echo.
echo Pasta que sera atualizada:
echo %PASTA%
echo.
echo O download vai comecar agora. O config.txt sera preservado.
echo.

where git >nul 2>&1
if errorlevel 1 goto ERRO_GIT
if not exist "%PASTA%" goto ERRO_PASTA
cd /d "%PASTA%"

if exist ".git" (
  for /f "delims=" %%H in ('git rev-parse --verify HEAD 2^>nul') do set "ANTES_SHA=%%H"
)
>>"%LOG_TEMP%" echo commit antes: !ANTES_SHA!

if exist "2-MOTORES\config.txt" copy /Y "2-MOTORES\config.txt" "%CFG_MOTOR%" >nul
if exist "config.txt" copy /Y "config.txt" "%CFG_RAIZ%" >nul

if not exist ".git" (
  echo ---- preparando esta pasta ZIP para receber atualizacoes...
  git init
  if errorlevel 1 goto ERRO_OPERACAO
  set "BOOTSTRAP=1"
) else (
  git rev-parse --verify HEAD >nul 2>&1
  if errorlevel 1 set "BOOTSTRAP=1"
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  git remote add origin "%REPO%"
  if errorlevel 1 goto ERRO_OPERACAO
) else (
  git remote set-url origin "%REPO%"
  if errorlevel 1 goto ERRO_OPERACAO
)

for /f "delims=" %%R in ('git remote get-url origin') do set "ORIGIN_ATUAL=%%R"
if /I not "!ORIGIN_ATUAL!"=="%REPO%" goto ERRO_OPERACAO

echo.
echo ---- BAIXANDO AGORA DO GITHUB...
echo.
rem Nao esconda a saida do Git: o usuario precisa enxergar o download.
git fetch --progress --prune --force origin main
if errorlevel 1 goto ERRO_FETCH
>>"%LOG_TEMP%" echo git fetch: OK

for /f "delims=" %%H in ('git rev-parse FETCH_HEAD') do set "REMOTO_SHA=%%H"
if not defined REMOTO_SHA goto ERRO_OPERACAO
>>"%LOG_TEMP%" echo commit remoto: !REMOTO_SHA!

echo.
if /I "!ANTES_SHA!"=="SEM_HEAD" (
  echo ---- primeira sincronizacao completa desta pasta.
) else if /I "!ANTES_SHA!"=="!REMOTO_SHA!" (
  echo ---- a pasta ja estava no commit mais recente.
  echo ---- nenhum arquivo novo existia para baixar.
) else (
  for /f %%C in ('git diff --name-only "!ANTES_SHA!" "!REMOTO_SHA!" ^| find /c /v ""') do set "QTD_ALTERADOS=%%C"
  echo ---- !QTD_ALTERADOS! arquivo(s) novo(s), alterado(s) ou removido(s):
  echo ------------------------------------------------------------
  git diff --name-status "!ANTES_SHA!" "!REMOTO_SHA!"
  echo ------------------------------------------------------------
)

echo.
echo ---- instalando o commit !REMOTO_SHA! nesta pasta...
if "!BOOTSTRAP!"=="1" goto APLICAR_BOOTSTRAP

git reset --hard FETCH_HEAD
if errorlevel 1 goto ERRO_OPERACAO
git checkout-index -a -f
if errorlevel 1 goto ERRO_OPERACAO
git branch -M main
if errorlevel 1 goto ERRO_OPERACAO
goto APLICADO

:APLICAR_BOOTSTRAP
git reset --mixed FETCH_HEAD
if errorlevel 1 goto ERRO_OPERACAO
git checkout-index -a -f
if errorlevel 1 goto ERRO_OPERACAO
git branch -M main
if errorlevel 1 goto ERRO_OPERACAO

:APLICADO
for /f "delims=" %%H in ('git rev-parse HEAD') do set "LOCAL_SHA=%%H"
if /I not "!LOCAL_SHA!"=="!REMOTO_SHA!" goto ERRO_OPERACAO
>>"%LOG_TEMP%" echo commit local depois: !LOCAL_SHA!

call :RESTAURAR_CONFIG

echo.
echo ---- codigo baixado e conferido.
echo ---- passando para o botao 4 NOVO que acabou de ser baixado...
>>"%LOG_TEMP%" echo download e checkout: OK

if not exist "%PASTA%\4-BAIXAR-DO-GITHUB.bat" goto ERRO_OPERACAO
call "%PASTA%\4-BAIXAR-DO-GITHUB.bat" FINALIZAR "%PASTA%" "!ANTES_SHA!" "!REMOTO_SHA!" "%LOG_TEMP%"
if errorlevel 1 goto ERRO_FINALIZACAO
exit /b 0

:FINALIZAR
set "PASTA=%~2"
set "ANTES_SHA=%~3"
set "REMOTO_SHA=%~4"
set "LOG_TEMP=%~5"
set "LOG_FINAL=%PASTA%\_ULTIMO-BAIXAR-DO-GITHUB.txt"
set "BUILD_SCRIPT=%PASTA%\7-VARREDURA-DO-JOGO\windows-app\COMPILAR-APLICATIVO.ps1"
set "EXTRATOR_EXE=%PASTA%\7-VARREDURA-DO-JOGO\Extrator eFootball.exe"
set "EXTRATOR_VERSAO=versao nao identificada"
cd /d "%PASTA%"

echo.
echo ---- recompilando o Extrator com o codigo NOVO...
if not exist "%BUILD_SCRIPT%" goto ERRO_BUILD_FINAL
where powershell >nul 2>&1
if errorlevel 1 goto ERRO_BUILD_FINAL
powershell -NoProfile -ExecutionPolicy Bypass -File "%BUILD_SCRIPT%"
if errorlevel 1 goto ERRO_BUILD_FINAL
if not exist "%EXTRATOR_EXE%" goto ERRO_BUILD_FINAL

for /f "delims=" %%V in ('powershell -NoProfile -Command "(Get-Item -LiteralPath $env:EXTRATOR_EXE).VersionInfo.FileVersion"') do set "EXTRATOR_VERSAO=%%V"
for %%F in ("%EXTRATOR_EXE%") do (
  echo ---- Extrator V!EXTRATOR_VERSAO! criado em %%~tF - %%~zF bytes
  >>"%LOG_TEMP%" echo executavel: %%~fF ^| versao !EXTRATOR_VERSAO! ^| %%~tF ^| %%~zF bytes
)

>>"%LOG_TEMP%" echo RESULTADO: SUCESSO
>>"%LOG_TEMP%" echo commit final: %REMOTO_SHA%
>>"%LOG_TEMP%" echo versao do Extrator: !EXTRATOR_VERSAO!
copy /Y "%LOG_TEMP%" "%LOG_FINAL%" >nul

echo.
echo ============================================================
echo  PRONTO - O GITHUB FOI BAIXADO DE VERDADE
echo ============================================================
echo Commit instalado:
echo %REMOTO_SHA%
echo.
echo Extrator recompilado: V!EXTRATOR_VERSAO!
echo.
echo Agora abra:
echo 7-VARREDURA-DO-JOGO\ABRIR-EXTRATOR.cmd
echo.
echo Relatorio:
echo %LOG_FINAL%
echo ============================================================
echo.
echo Esta janela ficara aberta. Pode fecha-la quando quiser.
exit /b 0

:RESTAURAR_CONFIG
if exist "%CFG_MOTOR%" (
  if not exist "2-MOTORES" mkdir "2-MOTORES"
  copy /Y "%CFG_MOTOR%" "2-MOTORES\config.txt" >nul
  del /f /q "%CFG_MOTOR%" >nul 2>&1
)
if exist "%CFG_RAIZ%" (
  copy /Y "%CFG_RAIZ%" "config.txt" >nul
  del /f /q "%CFG_RAIZ%" >nul 2>&1
)
exit /b 0

:ERRO_GIT
set "MOTIVO=O GIT NAO FOI ENCONTRADO NESTE WINDOWS."
goto ERRO_FINAL

:ERRO_PASTA
set "MOTIVO=NAO ACHEI A PASTA: %PASTA%"
goto ERRO_FINAL

:ERRO_FETCH
set "MOTIVO=O DOWNLOAD DO GITHUB FALHOU."
goto ERRO_FINAL

:ERRO_OPERACAO
set "MOTIVO=O GITHUB FOI ACESSADO, MAS NAO CONSEGUI INSTALAR OS ARQUIVOS."
goto ERRO_FINAL

:ERRO_FINALIZACAO
set "MOTIVO=OS ARQUIVOS FORAM BAIXADOS, MAS A FINALIZACAO FALHOU."
goto ERRO_FINAL

:ERRO_BUILD_FINAL
echo.
echo ERRO: os arquivos foram baixados, mas o Extrator nao foi recompilado.
>>"%LOG_TEMP%" echo RESULTADO: ERRO DE COMPILACAO
copy /Y "%LOG_TEMP%" "%LOG_FINAL%" >nul 2>&1
exit /b 20

:ERRO_FINAL
call :RESTAURAR_CONFIG
echo.
echo ============================================================
echo  ERRO NO BOTAO 4
echo ============================================================
echo %MOTIVO%
echo.
>>"%LOG_TEMP%" echo RESULTADO: ERRO
>>"%LOG_TEMP%" echo motivo: %MOTIVO%
copy /Y "%LOG_TEMP%" "%LOG_FINAL%" >nul 2>&1
echo Log completo:
echo %LOG_FINAL%
echo.
exit /b 1
