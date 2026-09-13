@echo off
setlocal
chcp 65001 >nul
title VIGIA do Extrator de Fotos - nao feche esta janela

set "PS=%~dp0controle-operacional.ps1"
set "ESTADO=%~dp0output\operador\estado.json"

:loop
cls
echo ============================================================
echo   VIGIA DO EXTRATOR DE FOTOS   -   %date% %time%
echo ============================================================
echo   Esta tela se atualiza sozinha a cada 60 segundos.
echo   Se o worker cair, o vigia reinicia sozinho.
echo   Para encerrar o vigia: feche esta janela.
echo   (fechar a janela NAO para o worker)
echo ============================================================

set "ST="
if exist "%ESTADO%" for /f "usebackq delims=" %%S in (`powershell.exe -NoProfile -Command "try{(Get-Content -Raw -LiteralPath '%ESTADO%' ^| ConvertFrom-Json).status}catch{''}"`) do set "ST=%%S"
if /I "%ST%"=="completed" goto fim

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS%" -Acao Iniciar -Automatico
echo.
echo ------------------------------------------------------------
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS%" -Acao Status
echo.
echo ------------------------------------------------------------
echo   Proxima atualizacao em 60 segundos...
timeout /t 60 /nobreak >nul
goto loop

:fim
cls
echo ============================================================
echo   FILA CONCLUIDA - nada mais pendente
echo ============================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS%" -Acao Status
echo.
pause
