@echo off
chcp 65001 >nul
title APAGAR O LIXO
cd /d "%~dp0"

echo.
echo  ============================================================
echo   APAGAR O LIXO
echo  ============================================================
echo.
echo   Os 9 arquivos do motor JA ESTAO em 2-MOTORES.
echo   Este arquivo so apaga. Nao copia nada.
echo.
echo   Vai apagar:
echo     ClubEfootball-V3-main   (a pasta inteira)
echo     _LIXO                   (a pasta inteira)
echo     CLUBEFOOTBALL-OFICINA.zip
echo     _ERRO-DO-GITHUB.txt
echo     0-ARRUMAR-O-V4.bat
echo.
pause

echo.
echo --- conferindo se o motor esta em 2-MOTORES ---
set ERRO=0
for %%A in (roda_lote_v6.py fonte_unica.py motor.py motor_bonus.py equacao.py regua.py grava_direto.py funcao_nativa.py regras_do_card.py) do (
  if not exist "2-MOTORES\%%A" (
    echo   FALTA  %%A
    set ERRO=1
  )
)

if "%ERRO%"=="1" (
  echo.
  echo   [PAREI] Falta arquivo em 2-MOTORES. NAO apaguei nada.
  echo.
  pause
  exit /b 1
)
echo   ok: os 9 estao la.

echo.
echo --- apagando ---
if exist "ClubEfootball-V3-main"      ( rd /s /q "ClubEfootball-V3-main"      & echo   apagada   ClubEfootball-V3-main )
if exist "_LIXO"                       ( rd /s /q "_LIXO"                       & echo   apagada   _LIXO )
if exist "CLUBEFOOTBALL-OFICINA.zip"   ( del /q   "CLUBEFOOTBALL-OFICINA.zip"   & echo   apagado   CLUBEFOOTBALL-OFICINA.zip )
if exist "_ERRO-DO-GITHUB.txt"         ( del /q   "_ERRO-DO-GITHUB.txt"         & echo   apagado   _ERRO-DO-GITHUB.txt )
if exist "0-ARRUMAR-O-V4.bat"          ( del /q   "0-ARRUMAR-O-V4.bat"          & echo   apagado   0-ARRUMAR-O-V4.bat )

echo.
echo  ============================================================
echo   PRONTO.
echo.
echo   Agora:  CRIAR-CONFIG.bat  ^>  RODAR-O-MOTOR.bat
echo  ============================================================
echo.
pause
