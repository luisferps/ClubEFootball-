@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo =====================================================
echo  COMPILACAO DO EXTRATOR DESKTOP V5.3
echo =====================================================
echo.
echo O uso normal abre o aplicativo por:
echo ABRIR-EXTRATOR.cmd
echo.
choice /C SN /N /M "Deseja compilar o aplicativo desktop? [S/N] "
if errorlevel 2 exit /b 0

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows-app\COMPILAR-APLICATIVO.ps1"
if errorlevel 1 (
  echo.
  echo FALHA: nao foi possivel reconstruir o executavel.
  pause
  exit /b 1
)

echo.
echo OK: EXE V5.3 reconstruido.
echo Para usar, abra ABRIR-EXTRATOR.cmd.
pause
endlocal
