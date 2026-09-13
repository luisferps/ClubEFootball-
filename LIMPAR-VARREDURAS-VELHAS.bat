@echo off
chcp 65001 >nul
title Limpar varreduras velhas do Extrator
setlocal enabledelayedexpansion

set "BASE=%~dp07-VARREDURA-DO-JOGO\artefatos\desktop"

echo.
echo ============================================================
echo   LIMPAR VARREDURAS VELHAS
echo ============================================================
echo.
echo   Cada varredura ocupa cerca de 1,3 GB.
echo   Mantem a MAIS RECENTE e apaga o resto.
echo.

if not exist "%BASE%" (
  echo   [ERRO] Pasta nao encontrada:
  echo          %BASE%
  echo   Coloque este arquivo em ClubEFootball--main, junto do ABRIR-EXTRATOR.
  echo.
  pause
  exit /b 1
)

set "MANTER="
for /f "tokens=* delims=" %%D in ('dir /b /ad /o-n "%BASE%\run-*" 2^>nul') do (
  if not defined MANTER set "MANTER=%%D"
)

if not defined MANTER (
  echo   Nao ha nenhuma varredura para limpar.
  echo.
  pause
  exit /b 0
)

echo   MANTER:  !MANTER!
echo.
echo   APAGAR:
set /a N=0
for /f "tokens=* delims=" %%D in ('dir /b /ad /o-n "%BASE%\run-*" 2^>nul') do (
  if /i not "%%D"=="!MANTER!" (
    echo      %%D
    set /a N+=1
  )
)

if !N!==0 (
  echo      nenhuma. So existe a varredura mais recente.
  echo.
  pause
  exit /b 0
)

echo.
echo   Total a apagar: !N! pasta^(s^)
echo.
choice /c SN /n /m "   Confirma? [S]im  [N]ao: "
if errorlevel 2 goto :fim

echo.
for /f "tokens=* delims=" %%D in ('dir /b /ad /o-n "%BASE%\run-*" 2^>nul') do (
  if /i not "%%D"=="!MANTER!" (
    echo   apagando %%D ...
    rd /s /q "%BASE%\%%D"
  )
)

echo.
echo   Pronto. Mantida: !MANTER!
echo.

:fim
pause
endlocal
