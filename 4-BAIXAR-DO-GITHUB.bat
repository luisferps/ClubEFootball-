@echo off
chcp 65001 >nul
setlocal EnableExtensions

rem O git reescreve TODOS os arquivos da pasta - inclusive este .bat.
rem Por isso o script se copia para TEMP e trabalha na pasta original de fora.

if /I "%~1"=="DELA" goto TRABALHO

set "ORIGEM=%~dp0"
set "ORIGEM=%ORIGEM:~0,-1%"
copy /Y "%~f0" "%TEMP%\cf-baixar.bat" >nul
"%TEMP%\cf-baixar.bat" DELA "%ORIGEM%"
exit /b

:TRABALHO
set "PASTA=%~2"
set "LOG=%TEMP%\cf-baixar.log"
set "REPO=https://github.com/luisferps/ClubEFootball-.git"
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
echo   Traz a versao mais nova e confirma o commit recebido.
echo   O config.txt NAO e tocado.
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

rem REGRA CRITICA: mesmo se .git ja existir, a origem tem que ser a V4 atual.
rem Antes este passo so era feito na primeira inicializacao; uma pasta herdada
rem podia continuar baixando de um repositorio antigo sem avisar.
git remote get-url origin >nul 2>&1
if errorlevel 1 (
  git remote add origin "%REPO%" >> "%LOG%" 2>&1 || goto ERRO_OPERACAO
) else (
  git remote set-url origin "%REPO%" >> "%LOG%" 2>&1 || goto ERRO_OPERACAO
)

for /f "delims=" %%R in ('git remote get-url origin') do set "ORIGIN_ATUAL=%%R"
echo   ---- origem: %ORIGIN_ATUAL%
>>"%LOG%" echo origem efetiva: %ORIGIN_ATUAL%

if /I not "%ORIGIN_ATUAL%"=="%REPO%" (
  echo   ^>^> ERRO: a origem nao ficou apontada para o repositorio V4.
  goto ERRO_OPERACAO
)

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

if /I not "%LOCAL_SHA%"=="%REMOTO_SHA%" (
  echo   ^>^> ERRO: o commit local nao ficou igual ao GitHub.
  goto ERRO_OPERACAO
)

echo   ---- devolvendo o config.txt
if exist "%TEMP%\cf-config.txt" (
  if not exist "2-MOTORES" mkdir "2-MOTORES"
  copy /Y "%TEMP%\cf-config.txt" "2-MOTORES\config.txt" >nul
  del /f /q "%TEMP%\cf-config.txt" >nul 2>&1
)

echo.
echo  ============================================================
echo   BAIXOU E CONFERIU.
echo   Commit local = GitHub:
echo   %LOCAL_SHA%
echo  ============================================================
echo.
pause
exit /b 0

:ERRO_GIT
echo   ^>^> O GIT NAO FOI ENCONTRADO.
goto ERRO_FINAL

:ERRO_PASTA
echo   ^>^> NAO ACHEI A PASTA: %PASTA%
goto ERRO_FINAL

:ERRO_FETCH
echo   ^>^> NAO CONSEGUI BUSCAR O GITHUB.
goto ERRO_FINAL

:ERRO_OPERACAO
echo   ^>^> A ATUALIZACAO NAO FOI CONCLUIDA.
goto ERRO_FINAL

:ERRO_FINAL
echo.
echo   Log: %LOG%
echo   Nao considere a pasta atualizada.
echo.
pause
exit /b 1
