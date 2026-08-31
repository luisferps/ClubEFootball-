@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "APLICATIVO=%~dp0Extrator eFootball.exe"
set "FONTE=%~dp0windows-app\ClubEfootballExtractorLauncher.cs"
set "WORKER=%~dp0executor\desktop_worker.py"

if not exist "%WORKER%" (
  echo.
  echo Nao encontrei o worker desktop:
  echo %WORKER%
  echo Rode o botao 4 para copiar os arquivos atuais do GitHub.
  pause
  exit /b 2
)

set "VERSAO_EXE="
if exist "%APLICATIVO%" for /f "usebackq delims=" %%V in (`powershell.exe -NoProfile -Command "(Get-Item -LiteralPath '%APLICATIVO%').VersionInfo.ProductVersion"`) do set "VERSAO_EXE=%%V"

if /I "%VERSAO_EXE:~0,5%"=="5.3.0" (
  start "Extrator eFootball" "%APLICATIVO%"
  exit /b 0
)

echo.
echo ============================================================
echo  EXTRATOR EFOOTBALL DESKTOP
echo ============================================================
echo.
echo O executavel desktop V5.3 ainda nao foi compilado nesta pasta.
echo Um EXE anterior nao sera aberto, pois ele usa a interface web antiga.
echo Use uma unica vez:
echo  COMPILAR-EXTRATOR-DESKTOP.cmd
echo.
echo A nova aplicacao nao abre navegador, servidor local ou pagina HTML.
echo Fonte do aplicativo:
echo %FONTE%
echo.
pause
exit /b 0
