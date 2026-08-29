@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "logs" mkdir "logs" >nul 2>nul
set "BOOTLOG=%~dp0logs\inicializacao-v46.log"

echo.>>"%BOOTLOG%"
echo ============================================================>>"%BOOTLOG%"
echo [%date% %time%] INICIO - Extrator eFootball V4.6.6>>"%BOOTLOG%"

if not exist "%~dp0configuracao.local.json" (
  echo.
  echo ============================================================
  echo  EXTRATOR EFOOTBALL - CONFIGURACAO AUSENTE
  echo ============================================================
  echo.
  echo O arquivo configuracao.local.json nao esta nesta pasta.
  echo Coloque o seu arquivo de configuracao do Supabase aqui e tente de novo.
  echo.
  echo Pasta esperada:
  echo %~dp0
  echo.
  echo [%date% %time%] ERRO - configuracao.local.json ausente>>"%BOOTLOG%"
  start "" "%~dp0"
  pause
  exit /b 2
)

echo [%date% %time%] OK - configuracao.local.json encontrado>>"%BOOTLOG%"

echo Preparando o Extrator eFootball V4.6.6...
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

echo [%date% %time%] OK - EXE V4.6.6 reconstruido; abrindo>>"%BOOTLOG%"
start "" "%~dp0Extrator eFootball.exe"
exit /b 0
