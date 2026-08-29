@echo off
setlocal
cd /d "%~dp0"

echo =====================================================
echo  Extrator eFootball V4.6.9 - reconstruir aplicativo
echo =====================================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows-app\COMPILAR-APLICATIVO.ps1"
if errorlevel 1 (
  echo.
  echo FALHA: nao foi possivel reconstruir o executavel.
  echo Use ABRIR-EXTRATOR.cmd para iniciar normalmente.
  pause
  exit /b 1
)

echo.
echo OK: Extrator eFootball.exe V4.6.9 reconstruido.
echo Para uso normal, abra ABRIR-EXTRATOR.cmd.
pause
endlocal
