@echo off
chcp 65001 >nul
setlocal EnableExtensions

rem O git reescreve TODOS os arquivos da pasta - inclusive este .bat.
rem Por isso o script se copia para TEMP e trabalha na pasta original de fora.

if /I "%~1"=="DELA" goto TRABALHO

set "ORIGEM=%~dp0"
set "ORIGEM=%ORIGEM:~0,-1%"
copy /Y "%~f0" "%TEMP%\cf-baixar.bat" >nul
start "4 - BAIXAR DO GITHUB" cmd /k ""%TEMP%\cf-baixar.bat" DELA "%ORIGEM%""
exit /b

:TRABALHO
set "PASTA=%~2"
set "LOG=%PASTA%\_ULTIMO-BAIXAR-DO-GITHUB.txt"
set "REPO=https://github.com/luisferps/ClubEFootball-.git"
set "BUILD_SCRIPT=%PASTA%\7-VARREDURA-DO-JOGO\windows-app\COMPILAR-APLICATIVO.ps1"
set "EXTRATOR_EXE=%PASTA%\7-VARREDURA-DO-JOGO\Extrator eFootball.exe"
title 4 - BAIXAR DO GITHUB

> "%LOG%" echo ============================================
>>"%LOG%" echo  BAIXAR DO GITHUB  %DATE% %TIME%
>>"%LOG%" echo  pasta: %PASTA%
>>"%LOG%" echo  repo esperado: %REPO%
>>"%LOG%" echo ============================================

echo.
echo  ============================================================
echo   BAIXAR DO GITHUB
echo  ============================================================
echo.
echo   Pasta: %PASTA%
echo   Repositorio: %REPO%
echo.
echo   Baixa o codigo atual, confere o commit e recompila o Extrator V4.6.
echo   O config.txt NAO e tocado.
echo   Esta janela NAO fecha automaticamente.
echo.
pause

where git >nul 2>&1
if errorlevel 1 goto ERRO_GIT
if not exist "%PASTA%" goto ERRO_PASTA

cd /d "%PASTA%"

if not exist ".git" (
  echo   ---- inicializando repositorio local
  git init >> "%LOG%" 2>&1 || goto ERRO_OPERACAO
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  git remote add origin "%REPO%" >> "%LOG%" 2>&1 || goto ERRO_OPERACAO
) else (
  git remote set-url origin "%REPO%" >> "%LOG%" 2>&1 || goto ERRO_OPERACAO
)

for /f "delims=" %%R in ('git remote get-url origin') do set "ORIGIN_ATUAL=%%R"
echo   ---- origem: %ORIGIN_ATUAL%
>>"%LOG%" echo origem efetiva: %ORIGIN_ATUAL%
if /I not "%ORIGIN_ATUAL%"=="%REPO%" goto ERRO_OPERACAO

echo   ---- guardando o config.txt
if exist "2-MOTORES\config.txt" copy /Y "2-MOTORES\config.txt" "%TEMP%\cf-config.txt" >nul
if exist "config.txt" copy /Y "config.txt" "%TEMP%\cf-config.txt" >nul
if exist "_ERRO-DO-GITHUB.txt" del /f /q "_ERRO-DO-GITHUB.txt" >nul 2>&1

echo   ---- buscando origin/main...
git fetch --prune origin main >> "%LOG%" 2>&1
if errorlevel 1 goto ERRO_FETCH
for /f "delims=" %%H in ('git rev-parse FETCH_HEAD') do set "REMOTO_SHA=%%H"
if not defined REMOTO_SHA goto ERRO_OPERACAO

echo   ---- aplicando commit %REMOTO_SHA%...
git checkout -B main FETCH_HEAD >> "%LOG%" 2>&1
if errorlevel 1 goto ERRO_OPERACAO
git reset --hard FETCH_HEAD >> "%LOG%" 2>&1
if errorlevel 1 goto ERRO_OPERACAO
for /f "delims=" %%H in ('git rev-parse HEAD') do set "LOCAL_SHA=%%H"
>>"%LOG%" echo remoto: %REMOTO_SHA%
>>"%LOG%" echo local : %LOCAL_SHA%
if /I not "%LOCAL_SHA%"=="%REMOTO_SHA%" goto ERRO_OPERACAO

echo   ---- devolvendo o config.txt
if exist "%TEMP%\cf-config.txt" (
  if not exist "2-MOTORES" mkdir "2-MOTORES"
  copy /Y "%TEMP%\cf-config.txt" "2-MOTORES\config.txt" >nul
  del /f /q "%TEMP%\cf-config.txt" >nul 2>&1
)

echo   ---- recompilando o Extrator V4.6 a partir do codigo baixado...
if not exist "%BUILD_SCRIPT%" goto ERRO_BUILD
where powershell >nul 2>&1
if errorlevel 1 goto ERRO_BUILD
if exist "%EXTRATOR_EXE%" del /f /q "%EXTRATOR_EXE%" >> "%LOG%" 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -File "%BUILD_SCRIPT%" >> "%LOG%" 2>&1
if errorlevel 1 goto ERRO_BUILD
if not exist "%EXTRATOR_EXE%" goto ERRO_BUILD

for %%F in ("%EXTRATOR_EXE%") do (
  echo        Extrator recompilado: %%~tF - %%~zF bytes
  >>"%LOG%" echo executavel recompilado: %%~fF ^| %%~tF ^| %%~zF bytes
)

>>"%LOG%" echo RESULTADO: SUCESSO
>>"%LOG%" echo commit: %LOCAL_SHA%
echo.
echo  ============================================================
echo   BAIXOU, CONFERIU E RECOMPILOU O EXTRATOR.
echo   Commit local = GitHub:
echo   %LOCAL_SHA%
echo  ============================================================
echo.
echo   Resultado gravado em:
echo   %LOG%
echo.
echo   ESTA JANELA FICARA ABERTA. FECHE-A MANUALMENTE QUANDO QUISER.
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
set "MOTIVO=O CODIGO FOI BAIXADO, MAS O EXTRATOR NAO FOI RECOMPILADO. O executavel velho foi removido."
goto ERRO_FINAL

:ERRO_OPERACAO
set "MOTIVO=A ATUALIZACAO NAO FOI CONCLUIDA."
goto ERRO_FINAL

:ERRO_FINAL
echo.
echo   ^>^> ERRO: %MOTIVO%
echo   ^>^> NAO considere a pasta pronta para uso.
>>"%LOG%" echo RESULTADO: ERRO
>>"%LOG%" echo motivo: %MOTIVO%
echo.
echo   Resultado gravado em:
echo   %LOG%
echo.
echo   ESTA JANELA FICARA ABERTA. FECHE-A MANUALMENTE QUANDO QUISER.
goto MANTER_ABERTO

:MANTER_ABERTO
echo.
echo   Digite EXIT e pressione Enter somente quando quiser fechar esta janela.
echo.
cmd /k
