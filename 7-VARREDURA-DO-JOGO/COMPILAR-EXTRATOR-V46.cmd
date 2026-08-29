@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo =====================================================
echo  COMPILACAO OPCIONAL DO EXE
echo =====================================================
echo.
echo O uso normal NAO precisa deste arquivo.
echo Para abrir o Extrator, use somente:
echo ABRIR-EXTRATOR.cmd
echo.
echo Este comando existe apenas para manutencao do EXE antigo.
echo.
choice /C SN /N /M "Deseja compilar o EXE mesmo assim? [S/N] "
if errorlevel 2 exit /b 0

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows-app\COMPILAR-APLICATIVO.ps1"
if errorlevel 1 (
  echo.
  echo FALHA: nao foi possivel reconstruir o executavel opcional.
  pause
  exit /b 1
)

echo.
echo OK: EXE opcional reconstruido.
echo Para o uso normal, continue abrindo ABRIR-EXTRATOR.cmd.
pause
endlocal
