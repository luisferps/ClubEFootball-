@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "HOTFIX=%~dp0executor\servidor_v4612_hotfix.py"
set "PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "PYTHON_MODO=CONSOLE"

if not exist "%HOTFIX%" (
  echo.
  echo Nao encontrei o runtime corrigido do Extrator:
  echo %HOTFIX%
  echo.
  echo Rode o botao 4 para copiar os arquivos atuais do GitHub.
  pause
  exit /b 2
)

if exist "%PYTHON%" goto PYTHON_OK
set "PYTHON="

for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined PYTHON (
  set "PYTHON=%%P"
  set "PYTHON_MODO=CONSOLE"
)
if defined PYTHON goto PYTHON_OK

for /f "delims=" %%P in ('where py.exe 2^>nul') do if not defined PYTHON (
  set "PYTHON=%%P"
  set "PYTHON_MODO=PYLAUNCHER"
)

:PYTHON_OK
if not defined PYTHON (
  echo.
  echo Nao encontrei o Python neste Windows.
  echo.
  pause
  exit /b 3
)

echo.
echo ============================================================
echo  EXTRATOR EFOOTBALL V4.6.12
echo ============================================================
echo.
echo Abrindo pelo runtime corrigido.
echo Nenhuma compilacao sera feita.
echo Esta janela deve permanecer aberta enquanto o Extrator estiver em uso.
echo.

pushd "%~dp0executor"
if /I "%PYTHON_MODO%"=="PYLAUNCHER" (
  "%PYTHON%" -3 "servidor_v4612_hotfix.py"
) else (
  "%PYTHON%" "servidor_v4612_hotfix.py"
)
set "RESULTADO=%ERRORLEVEL%"
popd

if not "%RESULTADO%"=="0" (
  echo.
  echo ============================================================
  echo  O EXTRATOR ENCERROU COM ERRO %RESULTADO%
  echo ============================================================
  echo.
  echo O erro real apareceu acima e tambem fica em:
  echo %~dp0logs\extrator-v46.log
  echo.
  pause
)
exit /b %RESULTADO%
