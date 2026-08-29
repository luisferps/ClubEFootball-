@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "VERSAO=4.6.12"
set "PORTA=8778"
set "URL=http://127.0.0.1:%PORTA%/Extrator-ClubEfootball.html?v=%VERSAO%"
set "STATUS_URL=http://127.0.0.1:%PORTA%/api/runtime-version"
set "RUNTIME=%~dp0executor\servidor_v4612.py"
set "VENDOR=%~dp0executor\vendor"
set "BOOTLOG=%~dp0logs\inicializacao-v46.log"
set "RUNTIMELOG=%~dp0logs\extrator-v46.log"
set "SERVER_OUT=%~dp0logs\servidor-v4612-saida.log"
set "SERVER_ERR=%~dp0logs\servidor-v4612-erro.log"
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

rem Se o servidor desta versao ja estiver aberto, apenas abre a interface.
call :SERVIDOR_OK
if not errorlevel 1 (
  echo O servidor ja estava pronto.
  goto ABRIR_TELA
)

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

del /f /q "%SERVER_OUT%" >nul 2>nul
del /f /q "%SERVER_ERR%" >nul 2>nul

set "START_PYTHON=%PYTHON%"
set "START_MODE=%PYTHON_MODO%"
set "START_WORKDIR=%~dp0executor"
set "START_STDOUT=%SERVER_OUT%"
set "START_STDERR=%SERVER_ERR%"

echo Iniciando o servidor local...
for /f "delims=" %%P in ('powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$arguments = if ($env:START_MODE -eq 'PYLAUNCHER') { @('-3','servidor_v4612.py','--no-browser') } else { @('servidor_v4612.py','--no-browser') }; $process = Start-Process -FilePath $env:START_PYTHON -ArgumentList $arguments -WorkingDirectory $env:START_WORKDIR -WindowStyle Hidden -RedirectStandardOutput $env:START_STDOUT -RedirectStandardError $env:START_STDERR -PassThru; $process.Id" 2^>^>"%BOOTLOG%"') do set "SERVER_PID=%%P"

if not defined SERVER_PID (
  echo Nao consegui iniciar o processo do servidor.
  echo [%date% %time%] ERRO - processo Python nao iniciou>>"%BOOTLOG%"
  goto MOSTRAR_ERRO
)

echo [%date% %time%] Processo do runtime iniciado. PID=%SERVER_PID%>>"%BOOTLOG%"
echo Aguardando o servidor responder
<nul set /p "=  "
for /L %%S in (1,1,30) do (
  call :SERVIDOR_OK
  if not errorlevel 1 goto ABRIR_TELA
  <nul set /p "=."
  timeout /t 1 /nobreak >nul
)

echo.
echo O servidor nao respondeu em 30 segundos.
echo [%date% %time%] ERRO - runtime nao respondeu na porta %PORTA%>>"%BOOTLOG%"
goto MOSTRAR_ERRO

:ABRIR_TELA
echo.
echo Servidor pronto. Abrindo a interface...
echo [%date% %time%] OK - runtime V%VERSAO% pronto em %URL%>>"%BOOTLOG%"
call :ABRIR_URL
if errorlevel 1 (
  echo Nao consegui abrir o navegador automaticamente.
  echo Abra este endereco no Edge:
  echo %URL%
  pause
  exit /b 6
)
echo Interface enviada ao Microsoft Edge.
timeout /t 3 /nobreak >nul
exit /b 0

:MOSTRAR_ERRO
echo.
echo ============================================================
echo  O EXTRATOR NAO CONSEGUIU INICIAR
echo ============================================================
echo.
echo Erro do servidor:
if exist "%SERVER_ERR%" (
  type "%SERVER_ERR%"
) else (
  echo Nenhum arquivo de erro foi criado.
)
echo.
echo Saida do servidor:
if exist "%SERVER_OUT%" (
  type "%SERVER_OUT%"
) else (
  echo Nenhum arquivo de saida foi criado.
)
echo.
echo Logs completos:
echo %SERVER_ERR%
echo %SERVER_OUT%
echo %RUNTIMELOG%
echo %BOOTLOG%
echo.
pause
exit /b 5

:SERVIDOR_OK
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try{$r=Invoke-RestMethod -Uri ('%STATUS_URL%?t=' + [DateTime]::UtcNow.Ticks) -TimeoutSec 1; if($r.online -and $r.version -eq '%VERSAO%'){exit 0}}catch{}; exit 1" >nul 2>nul
exit /b %errorlevel%

:ABRIR_URL
set "EDGE="
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not defined EDGE if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not defined EDGE if exist "%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe" set "EDGE=%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"
if defined EDGE (
  start "" "%EDGE%" --app="%URL%" --start-maximized --no-first-run --disable-http-cache --disable-features=msEdgeSidebarV2
  exit /b %errorlevel%
)
start "" "%URL%"
exit /b %errorlevel%

:ENCONTRAR_PYTHON
set "PYTHON="
set "PYTHON_MODO="
set "PY_BASE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python"

rem Usa primeiro o mesmo python.exe que abriu as versoes anteriores.
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
