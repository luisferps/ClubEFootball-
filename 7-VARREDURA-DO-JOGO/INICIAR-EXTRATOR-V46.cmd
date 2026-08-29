@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "VERSAO=4.6.12"
set "PORTA=8778"
set "URL=http://127.0.0.1:%PORTA%/Extrator-ClubEfootball.html?v=%VERSAO%"
set "STATUS_URL=http://127.0.0.1:%PORTA%/api/runtime-version"
set "RUNTIME=%~dp0executor\servidor_v4612.py"
set "VENDOR=%~dp0executor\vendor"
set "BOOTLOG=%~dp0logs\inicializacao-v46.log"
set "RUNTIMELOG=%~dp0logs\extrator-v46.log"
set "CFG_RAIZ=%~dp0..\config.txt"
set "CFG_ALTERNATIVO=%~dp0..\2-MOTORES\config.txt"

if not exist "logs" mkdir "logs" >nul 2>nul

echo.>>"%BOOTLOG%"
echo ============================================================>>"%BOOTLOG%"
echo [%date% %time%] INICIO DIRETO - Extrator eFootball V%VERSAO%>>"%BOOTLOG%"

echo.
echo Abrindo o Extrator eFootball V%VERSAO%...
echo Nenhuma compilacao sera feita.
echo.

if exist "%CFG_RAIZ%" goto CONFIG_OK
if exist "%CFG_ALTERNATIVO%" goto CONFIG_OK

echo ============================================================
echo  CONFIG.TXT AUSENTE
echo ============================================================
echo.
echo Coloque o config.txt na pasta principal do ClubEfootball.
echo Pasta esperada:
echo %~dp0..
echo.
echo [%date% %time%] ERRO - config.txt ausente>>"%BOOTLOG%"
start "" "%~dp0.."
pause
exit /b 2

:CONFIG_OK
echo [%date% %time%] OK - config.txt encontrado>>"%BOOTLOG%"

if not exist "%RUNTIME%" (
  echo Nao encontrei o runtime:
  echo %RUNTIME%
  echo [%date% %time%] ERRO - runtime ausente>>"%BOOTLOG%"
  pause
  exit /b 3
)

rem Se o servidor desta versao ja estiver aberto, apenas abre a tela.
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try{$r=Invoke-RestMethod -Uri ('%STATUS_URL%?t=' + [DateTime]::UtcNow.Ticks) -TimeoutSec 1; if($r.online -and $r.version -eq '%VERSAO%'){exit 0}}catch{}; exit 1" >nul 2>nul
if not errorlevel 1 goto ABRIR_EXISTENTE

call :ENCONTRAR_PYTHON
if not defined PYTHON (
  echo Nao encontrei o Python neste Windows.
  echo O diagnostico ficou salvo em:
  echo %BOOTLOG%
  echo [%date% %time%] ERRO - Python ausente>>"%BOOTLOG%"
  pause
  exit /b 4
)

echo [%date% %time%] Python: %PYTHON%>>"%BOOTLOG%"
echo [%date% %time%] Runtime: %RUNTIME% porta %PORTA%>>"%BOOTLOG%"

set "PYTHONPATH=%VENDOR%"
set "PYTHONUNBUFFERED=1"
set "CLUBEF_EXTRACTOR_PORT=%PORTA%"
set "CLUBEF_EXTRACTOR_RUNTIME_VERSION=%VERSAO%"
set "CLUBEF_EXTRACTOR_LOG=%RUNTIMELOG%"
set "CLUBEF_SOURCE_DT870_UPDATED="
set "CLUBEF_SOURCE_DT200="
set "CLUBEF_SOURCE_DT870_ORIGINAL="
set "CLUBEF_SOURCE_DT261_BRA="
set "CLUBEF_ENABLE_REAL_WRITE="

echo Iniciando o servidor local...
if /I "%PYTHON_MODO%"=="PYLAUNCHER" (
  start "Extrator eFootball - servidor" /min "%PYTHON%" -3 "%RUNTIME%"
) else (
  start "Extrator eFootball - servidor" /min "%PYTHON%" "%RUNTIME%"
)

echo A tela sera aberta automaticamente pelo servidor.
echo Esta janela pode ser fechada.
echo [%date% %time%] OK - processo do runtime iniciado sem compilacao>>"%BOOTLOG%"
exit /b 0

:ABRIR_EXISTENTE
echo O servidor ja estava aberto. Abrindo a tela...
echo [%date% %time%] OK - runtime existente em %URL%>>"%BOOTLOG%"
call :ABRIR_URL
exit /b 0

:ABRIR_URL
set "EDGE="
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not defined EDGE if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not defined EDGE if exist "%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe" set "EDGE=%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"
if defined EDGE (
  start "" "%EDGE%" --app="%URL%" --start-maximized --no-first-run --disable-http-cache --disable-features=msEdgeSidebarV2
) else (
  start "" "%URL%"
)
exit /b 0

:ENCONTRAR_PYTHON
set "PYTHON="
set "PYTHON_MODO="
set "PY_BASE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python"

rem Usa primeiro o mesmo python.exe que ja abriu as versoes anteriores.
if exist "%PY_BASE%\python.exe" (
  set "PYTHON=%PY_BASE%\python.exe"
  set "PYTHON_MODO=CONSOLE"
  exit /b 0
)

for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined PYTHON (
  set "PYTHON=%%P"
  set "PYTHON_MODO=CONSOLE"
)
if defined PYTHON exit /b 0

for /f "delims=" %%P in ('where py.exe 2^>nul') do if not defined PYTHON (
  set "PYTHON=%%P"
  set "PYTHON_MODO=PYLAUNCHER"
)
exit /b 0
