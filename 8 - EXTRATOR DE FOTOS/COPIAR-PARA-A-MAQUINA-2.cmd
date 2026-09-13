@echo off
setlocal
chcp 65001 >nul
title Copiar arquivos para a MAQUINA 2

powershell.exe -NoProfile -Command "Set-Clipboard -LiteralPath (Get-ChildItem -LiteralPath '%~dp0.' -File | Select-Object -ExpandProperty FullName)"

echo ============================================================
echo  PRONTO - os arquivos estao no seu Ctrl+C
echo ============================================================
echo.
echo  Agora, na MAQUINA 2, abra esta pasta:
echo.
echo     C:\Users\luis-\Downloads\ClubEFootball--main\8 - EXTRATOR DE FOTOS
echo.
echo  e tecle Ctrl+V.
echo  Escolha "Substituir os arquivos no destino".
echo.
echo ============================================================
pause
