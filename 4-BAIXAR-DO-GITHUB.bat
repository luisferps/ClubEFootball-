@echo off
chcp 65001 >nul
setlocal EnableExtensions

rem Executa uma copia temporaria para o Git poder atualizar este proprio arquivo.
if /I "%~1"=="DELA" goto TRABALHO

set "ORIGEM=%~dp0"
set "ORIGEM=%ORIGEM:~0,-1%"
set "TEMP_SCRIPT=%TEMP%\clubef-baixar-%RANDOM%-%RANDOM%.bat"
copy /Y "%~f0" "%TEMP_SCRIPT%" >nul
start "4 - BAIXAR DO GITHUB" cmd /k ""%TEMP_SCRIPT%" DELA "%ORIGEM%""
exit /b

:TRABALHO
set "PASTA=%~2"
set "LOG_TEMP=%TEMP%\clubef-github-%RANDOM%-%RANDOM%.log"
set "LOG_FINAL=%PASTA%\_ULTIMO-BAIXAR-DO-GITHUB.txt"
set "REPO=https://github.com/luisferps/ClubEFootball-.git"
set "BUILD_SCRIPT=%PASTA%\7-VARREDURA-DO-JOGO\windows-app\COMPILAR-APLICATIVO.ps1"
set "EXTRATOR_EXE=%PASTA%\7-VARREDURA-DO-JOGO\Extrator eFootball.exe"
set "CFG_MOTOR=%TEMP%\clubef-config-motor-%RANDOM%-%RANDOM%.tmp"
set "CFG_RAIZ=%TEMP%\clubef-config-raiz-%RANDOM%-%RANDOM%.tmp"
set "BOOTSTRAP=0"
title 4 - BAIXAR DO GITHUB

> "%LOG_TEMP%" echo ============================================
>>"%LOG_TEMP%" echo  BAIXAR DO GITHUB  %DATE% %TIME%
>>"%LOG_TEMP%" echo  pasta: %PASTA%
>>"%LOG_TEMP%" echo  repo esperado: %REPO%
>>"%LOG_TEMP%" echo ============================================

echo.
echo  ============================================================
echo   BAIXAR DO GITHUB
 echo  ============================================================
echo.
echo   Pasta: %PASTA%
echo   Repositorio: %REPO%
echo.
echo   Baixa o codigo atual, confere o commit e recompila o Extrator V4.6.5.
echo   Funciona tambem quando a pasta foi baixada como ZIP do GitHub.
echo   O config.txt NAO e tocado.
echo   Esta janela NAO fecha automaticamente.
echo.
pause

where git >nul 2>&1
if errorlevel 1 goto ERRO_GIT
if not exist "%PASTA%" goto ERRO_PASTA

cd /d "%PASTA%"

rem O log nunca fica aberto dentro da arvore enquanto o Git sincroniza.
if exist "%LOG_FINAL%" del /f /q "%LOG_FINAL%" >nul 2>&1

if exist "2-MOTORES\config.txt" copy /Y "2-MOTORES\config.txt" "%CFG_MOTOR%" >nul
if exist "config.txt" copy /Y "config.txt" "%CFG_RAIZ%" >nul

if not exist ".git" (
  echo   ---- primeiro uso: inicializando repositorio local
  >>"%LOG_TEMP%" echo modo: bootstrap de pasta ZIP sem .git
  git init >> "%LOG_TEMP%" 2>&1
  if errorlevel 1 goto ERRO_OPERACAO
  set "BOOTSTRAP=1"
) else (
  git rev-parse --verify HEAD >nul 2>&1
  if errorlevel 1 (
    echo   ---- primeiro uso incompleto detectado; retomando bootstrap
    >>"%LOG_TEMP%" echo modo: bootstrap retomado; .git existe mas HEAD ainda nao existe
    set "BOOTSTRAP=1"
  )
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  git remote add origin "%REPO%" >> "%LOG_TEMP%" 2>&1
  if errorlevel 1 goto ERRO_OPERACAO
) else (
  git remote set-url origin "%REPO%" >> "%LOG_TEMP%" 2>&1
  if errorlevel 1 goto ERRO_OPERACAO
)

for /f "delims=" %%R in ('git remote get-url origin') do set "ORIGIN_ATUAL=%%R"
echo   ---- origem: %ORIGIN_ATUAL%
>>"%LOG_TEMP%" echo origem efetiva: %ORIGIN_ATUAL%
if /I not "%ORIGIN_ATUAL%"=="%REPO%" goto ERRO_OPERACAO

echo   ---- buscando origin/main...
git fetch --prune origin main >> "%LOG_TEMP%" 2>&1
if errorlevel 1 goto ERRO_FETCH
for /f "delims=" %%H in ('git rev-parse FETCH_HEAD') do set "REMOTO_SHA=%%H"
if not defined REMOTO_SHA goto ERRO_OPERACAO

echo   ---- aplicando commit %REMOTO_SHA%...
if "%BOOTSTRAP%"=="1" goto APLICAR_BOOTSTRAP

git reset --hard FETCH_HEAD >> "%LOG_TEMP%" 2>&1
if errorlevel 1 goto ERRO_OPERACAO
git branch -M main >> "%LOG_TEMP%" 2>&1
if errorlevel 1 goto ERRO_OPERACAO
goto APLICADO

:APLICAR_BOOTSTRAP
echo   ---- adotando a pasta ZIP como copia de trabalho do GitHub...
git reset --mixed FETCH_HEAD >> "%LOG_TEMP%" 2>&1
if errorlevel 1 goto ERRO_OPERACAO
git checkout-index -a -f >> "%LOG_TEMP%" 2>&1
if errorlevel 1 goto ERRO_OPERACAO
git branch -M main >> "%LOG_TEMP%" 2>&1
if errorlevel 1 goto ERRO_OPERACAO

:APLICADO
for /f "delims=" %%H in ('git rev-parse HEAD') do set "LOCAL_SHA=%%H"
>>"%LOG_TEMP%" echo remoto: %REMOTO_SHA%
>>"%LOG_TEMP%" echo local : %LOCAL_SHA%
if /I not "%LOCAL_SHA%"=="%REMOTO_SHA%" goto ERRO_OPERACAO

echo   ---- devolvendo o config.txt
if exist "%CFG_MOTOR%" (
  if not exist "2-MOTORES" mkdir "2-MOTORES"
  copy /Y "%CFG_MOTOR%" "2-MOTORES\config.txt" >nul
  del /f /q "%CFG_MOTOR%" >nul 2>&1
)
if exist "%CFG_RAIZ%" (
  copy /Y "%CFG_RAIZ%" "config.txt" >nul
  del /f /q "%CFG_RAIZ%" >nul 2>&1
)

echo   ---- recompilando o Extrator V4.6.5 a partir do codigo baixado...
if not exist "%BUILD_SCRIPT%" goto ERRO_BUILD
where powershell >nul 2>&1
if errorlevel 1 goto ERRO_BUILD
powershell -NoProfile -ExecutionPolicy Bypass -File "%BUILD_SCRIPT%" >> "%LOG_TEMP%" 2>&1
if errorlevel 1 goto ERRO_BUILD
if not exist "%EXTRATOR_EXE%" goto ERRO_BUILD

for %%F in ("%EXTRATOR_EXE%") do (
  echo        Extrator recompilado: %%~tF - %%~zF bytes
  >>"%LOG_TEMP%" echo executavel recompilado: %%~fF ^| %%~tF ^| %%~zF bytes
)

>>"%LOG_TEMP%" echo RESULTADO: SUCESSO
>>"%LOG_TEMP%" echo commit: %LOCAL_SHA%
copy /Y "%LOG_TEMP%" "%LOG_FINAL%" >nul

echo.
echo  ============================================================
echo   BAIXOU, CONFERIU E RECOMPILOU O EXTRATOR V4.6.5.
echo   Commit local = GitHub:
echo   %LOCAL_SHA%
echo  ============================================================
echo.
echo   Resultado gravado em:
echo   %LOG_FINAL%
goto MANTER_ABERTO

:ERRO_GIT
set "MOTIVO=O GIT NAO FOI ENCONTRADO."
goto ERRO_FINAL

:ERRO_PASTA
set "MOTIVO=NAO ACHEI A PASTA: %PASTA%"
goto ERRO_FINAL

:ERRO_FETCH
set "MOTIVO=NAO CONSEGUI BUSCAR O GITHUB."
goto ERRO_FINAL

:ERRO_BUILD
set "MOTIVO=O CODIGO FOI BAIXADO, MAS O EXTRATOR NAO FOI RECOMPILADO."
goto ERRO_FINAL

:ERRO_OPERACAO
set "MOTIVO=A ATUALIZACAO DO GIT FALHOU."
goto ERRO_FINAL

:ERRO_FINAL
echo.
echo   ^>^> ERRO: %MOTIVO%
echo   ^>^> NAO considere a pasta pronta para uso.
>>"%LOG_TEMP%" echo RESULTADO: ERRO
>>"%LOG_TEMP%" echo motivo: %MOTIVO%
copy /Y "%LOG_TEMP%" "%LOG_FINAL%" >nul 2>&1
echo.
echo   Ultimas linhas do erro:
echo   ------------------------------------------------------------
powershell -NoProfile -Command "if (Test-Path -LiteralPath '%LOG_TEMP%') { Get-Content -LiteralPath '%LOG_TEMP%' -Tail 25 }" 2>nul
echo   ------------------------------------------------------------
echo.
echo   Log completo: %LOG_FINAL%

:MANTER_ABERTO
echo.
echo   ESTA JANELA FICARA ABERTA. FECHE-A MANUALMENTE QUANDO QUISER.
echo   Digite EXIT e pressione Enter somente quando quiser fechar.
echo.
cmd /k
