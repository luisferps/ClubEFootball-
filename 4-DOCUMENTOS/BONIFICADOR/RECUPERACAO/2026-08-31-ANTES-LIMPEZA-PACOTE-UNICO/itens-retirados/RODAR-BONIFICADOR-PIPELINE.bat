@echo off
setlocal
cd /d "%~dp0"
if not "%~1"=="" set "CLUBEF_BONIFICADOR_INTERVALO_SEGUNDOS=%~1"
echo Bonificador em pipeline vivo. Ctrl+C faz a parada normal.
python motor_bonus.py
if errorlevel 1 (
  echo.
  echo O Bonificador parou por falha ou gate. Leia a mensagem acima; nada foi aceito silenciosamente.
  pause
)
endlocal
