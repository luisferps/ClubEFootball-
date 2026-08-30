@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem Compatibilidade com o botao antigo: depois que ele copia este arquivo novo,
rem ele chama FINALIZAR. A finalizacao nova apenas confirma a copia; nao compila.
if /I "%~1"=="FINALIZAR" goto FINALIZAR_ANTIGO
if /I "%~1"=="TRABALHO" goto TRABALHO

rem Roda por uma copia temporaria para que o proprio botao possa ser atualizado.
set "ORIGEM=%~dp0"
if "%ORIGEM:~-1%"=="\" set "ORIGEM=%ORIGEM:~0,-1%"
set "TEMP_SCRIPT=%TEMP%\clubef-copiar-github-%RANDOM%-%RANDOM%.bat"
copy /Y "%~f0" "%TEMP_SCRIPT%" >nul
if errorlevel 1 (
  echo Nao consegui preparar o atualizador temporario.
  pause
  exit /b 1
)
start "4 - COPIAR ARQUIVOS DO GITHUB" cmd /k ""%TEMP_SCRIPT%" TRABALHO "%ORIGEM%""
exit /b

:TRABALHO
set "PASTA=%~2"
set "REPO=https://github.com/luisferps/ClubEFootball-.git"
set "LOG_TEMP=%TEMP%\clubef-github-%RANDOM%-%RANDOM%.log"
set "LOG_FINAL=%PASTA%\_ULTIMO-BAIXAR-DO-GITHUB.txt"
set "REMOTO_SHA="
set "LOCAL_SHA="
set "PRIMEIRA_SINCRONIZACAO=0"
title 4 - COPIAR ARQUIVOS DO GITHUB
cls

>"%LOG_TEMP%" echo ============================================
>>"%LOG_TEMP%" echo COPIAR ARQUIVOS DO GITHUB - %DATE% %TIME%
>>"%LOG_TEMP%" echo pasta: %PASTA%
>>"%LOG_TEMP%" echo repositorio: %REPO%
>>"%LOG_TEMP%" echo ============================================

echo.
echo ============================================================
echo  4 - COPIAR ARQUIVOS DO GITHUB
echo ============================================================
echo.
echo Pasta que sera atualizada:
echo %PASTA%
echo.
echo Este botao somente copia/sincroniza os arquivos do GitHub.
echo Nao compila, nao abre o Extrator e nao toca em configuracoes locais.
echo.

where git >nul 2>&1
if errorlevel 1 goto ERRO_GIT
if not exist "%PASTA%" goto ERRO_PASTA
cd /d "%PASTA%"

if not exist ".git" (
  echo ---- preparando esta pasta baixada como ZIP...
  git init >nul
  if errorlevel 1 goto ERRO_OPERACAO
  set "PRIMEIRA_SINCRONIZACAO=1"
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  git remote add origin "%REPO%"
  if errorlevel 1 goto ERRO_OPERACAO
) else (
  git remote set-url origin "%REPO%"
  if errorlevel 1 goto ERRO_OPERACAO
)

set "GIT_PAGER=cat"
set "PAGER=cat"

echo ---- copiando os arquivos atuais do GitHub...
git -c core.pager=cat fetch --progress --prune --force origin main
if errorlevel 1 goto ERRO_FETCH

for /f "delims=" %%H in ('git rev-parse FETCH_HEAD 2^>nul') do set "REMOTO_SHA=%%H"
if not defined REMOTO_SHA goto ERRO_OPERACAO

rem Regra de seguranca: configuracoes do usuario nunca podem vir do remoto.
rem A verificacao acontece antes de qualquer comando que escreva a arvore.
call :VALIDAR_CONFIG_REMOTO
if errorlevel 1 goto ERRO_CONFIG_REMOTO

rem Uma configuracao que ainda esteja no indice local tambem e insegura: em
rem vez de a remover durante a atualizacao, o botao para sem escrever nada.
call :VALIDAR_CONFIG_LOCAL
if errorlevel 1 goto ERRO_CONFIG_LOCAL

rem Sem reset forçado: uma copia existente avanca apenas por fast-forward.
rem Alteracoes locais conflitantes cancelam a operacao em vez de serem perdidas.
if "%PRIMEIRA_SINCRONIZACAO%"=="1" (
  git checkout -B main FETCH_HEAD
) else (
  git merge --ff-only FETCH_HEAD
)
if errorlevel 1 goto ERRO_CONFLITO_LOCAL

for /f "delims=" %%H in ('git rev-parse HEAD 2^>nul') do set "LOCAL_SHA=%%H"
if /I not "!LOCAL_SHA!"=="!REMOTO_SHA!" goto ERRO_OPERACAO

>>"%LOG_TEMP%" echo RESULTADO: SUCESSO
>>"%LOG_TEMP%" echo commit instalado: !LOCAL_SHA!
>>"%LOG_TEMP%" echo compilacao: NAO EXECUTADA
copy /Y "%LOG_TEMP%" "%LOG_FINAL%" >nul

echo.
echo ============================================================
echo  PRONTO - ARQUIVOS COPIADOS DO GITHUB
echo ============================================================
echo Commit instalado:
echo !LOCAL_SHA!
echo.
echo Nenhuma compilacao foi feita ou e necessaria para atualizar.
echo Agora abra:
echo 7-VARREDURA-DO-JOGO\ABRIR-EXTRATOR.cmd
echo.
echo Relatorio:
echo %LOG_FINAL%
echo ============================================================
echo.
echo Esta janela ficara aberta. Pode fecha-la quando quiser.
exit /b 0

:FINALIZAR_ANTIGO
rem O botao anterior chama esta entrada depois de instalar o botao novo.
set "PASTA=%~2"
set "REMOTO_SHA=%~4"
set "LOG_TEMP=%~5"
if not defined PASTA set "PASTA=%~dp0"
set "LOG_FINAL=%PASTA%\_ULTIMO-BAIXAR-DO-GITHUB.txt"
if not defined REMOTO_SHA (
  pushd "%PASTA%" >nul 2>&1
  for /f "delims=" %%H in ('git rev-parse HEAD 2^>nul') do set "REMOTO_SHA=%%H"
  popd >nul 2>&1
)
if defined LOG_TEMP if exist "%LOG_TEMP%" (
  >>"%LOG_TEMP%" echo RESULTADO: SUCESSO
  >>"%LOG_TEMP%" echo commit instalado: %REMOTO_SHA%
  >>"%LOG_TEMP%" echo compilacao: NAO EXECUTADA
  copy /Y "%LOG_TEMP%" "%LOG_FINAL%" >nul 2>&1
)
echo.
echo ============================================================
echo  PRONTO - ARQUIVOS COPIADOS DO GITHUB
echo ============================================================
echo Commit instalado:
echo %REMOTO_SHA%
echo.
echo O botao 4 agora apenas copia os arquivos. Nao compila nada.
echo Agora abra:
echo 7-VARREDURA-DO-JOGO\ABRIR-EXTRATOR.cmd
echo ============================================================
echo.
exit /b 0

:VALIDAR_CONFIG_REMOTO
set "CONFIG_REMOTO="
for /f "delims=" %%F in ('git ls-tree -r --name-only FETCH_HEAD -- "config.txt" ".env" ".env.*" "*.key" "*.pem" "*.secret" "*.secrets" "credenciais.local.*" "configuracao.local.*" 2^>nul') do (
  if /I not "%%~nxF"==".env.example" set "CONFIG_REMOTO=%%F"
)
if defined CONFIG_REMOTO (
  echo O remoto tentou versionar uma configuracao ou chave local: %CONFIG_REMOTO%
  echo A sincronizacao foi cancelada antes de alterar arquivos.
  exit /b 1
)
exit /b 0

:VALIDAR_CONFIG_LOCAL
set "CONFIG_LOCAL="
for /f "delims=" %%F in ('git ls-files -- "config.txt" ".env" ".env.*" "*.key" "*.pem" "*.secret" "*.secrets" "credenciais.local.*" "configuracao.local.*"') do (
  if /I not "%%~nxF"==".env.example" set "CONFIG_LOCAL=%%F"
)
if defined CONFIG_LOCAL (
  echo Configuracao ou chave local ainda esta versionada: %CONFIG_LOCAL%
  echo A sincronizacao foi cancelada antes de alterar arquivos.
  exit /b 1
)
exit /b 0

:ERRO_GIT
set "MOTIVO=O GIT NAO FOI ENCONTRADO NESTE WINDOWS."
goto ERRO_FINAL

:ERRO_PASTA
set "MOTIVO=NAO ACHEI A PASTA: %PASTA%"
goto ERRO_FINAL

:ERRO_FETCH
set "MOTIVO=NAO CONSEGUI BAIXAR OS ARQUIVOS DO GITHUB."
goto ERRO_FINAL

:ERRO_OPERACAO
set "MOTIVO=O GITHUB FOI ACESSADO, MAS NAO CONSEGUI COPIAR OS ARQUIVOS PARA ESTA PASTA."
goto ERRO_FINAL

:ERRO_CONFIG_REMOTO
set "MOTIVO=O remoto contem arquivo de configuracao local. Nada foi sincronizado."
goto ERRO_FINAL

:ERRO_CONFIG_LOCAL
set "MOTIVO=Uma configuracao local ainda esta versionada. Nada foi sincronizado."
goto ERRO_FINAL

:ERRO_CONFLITO_LOCAL
set "MOTIVO=Existem alteracoes locais que impedem a sincronizacao segura. Nada foi sobrescrito."
goto ERRO_FINAL

:ERRO_FINAL
echo.
echo ============================================================
echo  ERRO AO COPIAR OS ARQUIVOS
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
