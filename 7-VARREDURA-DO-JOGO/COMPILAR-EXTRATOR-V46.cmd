@echo off
setlocal
cd /d "%~dp0"

echo =====================================================
echo  Extrator eFootball V4.6 - reconstruir aplicativo
 echo =====================================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows-app\COMPILAR-APLICATIVO.ps1"
if errorlevel 1 (
  echo.
  echo FALHA: o executavel anterior foi preservado se a compilacao nao terminou.
  pause
  exit /b 1
)

echo.
echo OK: Extrator eFootball.exe reconstruido a partir do lancador V4.6.
echo Agora o EXE inicia executor\servidor_v46.py.
pause
endlocal
