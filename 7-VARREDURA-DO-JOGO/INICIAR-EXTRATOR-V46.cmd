@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "logs" mkdir "logs" >nul 2>nul
set "BOOTLOG=%~dp0logs\inicializacao-v46.log"
set "CFG_RAIZ=%~dp0..\config.txt"
set "CFG_MOTOR=%~dp0..\2-MOTORES\config.txt"

echo.>>"%BOOTLOG%"
echo ============================================================>>"%BOOTLOG%"
echo [%date% %time%] INICIO - Extrator eFootball V4.6.8>>"%BOOTLOG%"

if exist "%CFG_RAIZ%" goto CONFIG_OK
if exist "%CFG_MOTOR%" goto CONFIG_OK

echo.
echo ============================================================
echo  EXTRATOR EFOOTBALL - CONFIG.TXT AUSENTE
echo ============================================================
echo.
echo Coloque o seu config.txt na pasta principal do ClubEfootball
echo e execute novamente ABRIR-EXTRATOR.cmd.
echo.
echo Pasta esperada:
echo %~dp0..
echo.
echo [%date% %time%] ERRO - config.txt ausente>>"%BOOTLOG%"
start "" "%~dp0.."
pause
exit /b 2

:CONFIG_OK
echo [%date% %time%] OK - config.txt encontrado>>"%BOOTLOG%"

echo Preparando o Extrator eFootball V4.6.8...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows-app\COMPILAR-APLICATIVO.ps1" >>"%BOOTLOG%" 2>&1
if errorlevel 1 (
  echo [%date% %time%] ERRO - falha ao reconstruir o EXE>>"%BOOTLOG%"
  echo.
  echo Nao foi possivel preparar o Extrator.
  echo O diagnostico ficou salvo em:
  echo %BOOTLOG%
  echo.
  pause
  exit /b 3
)

if not exist "%~dp0Extrator eFootball.exe" (
  echo [%date% %time%] ERRO - EXE nao foi criado>>"%BOOTLOG%"
  echo.
  echo O EXE nao foi criado. Veja:
  echo %BOOTLOG%
  echo.
  pause
  exit /b 4
)

echo [%date% %time%] OK - EXE V4.6.8 reconstruido; abrindo na porta exclusiva 8772>>"%BOOTLOG%"
start "" "%~dp0Extrator eFootball.exe"
exit /b 0
