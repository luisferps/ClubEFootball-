@echo off
setlocal
cd /d "%~dp0"
set "VERSAO="
if exist "Bonificador ClubEfootball.exe" for /f "usebackq delims=" %%V in (`powershell.exe -NoProfile -Command "(Get-Item -LiteralPath 'Bonificador ClubEfootball.exe').VersionInfo.ProductVersion"`) do set "VERSAO=%%V"
if /I not "%VERSAO:~0,5%"=="2.0.0" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "windows-app\COMPILAR-APLICATIVO.ps1"
)
start "" "Bonificador ClubEfootball.exe"
endlocal
