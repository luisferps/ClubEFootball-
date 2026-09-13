@echo off
chcp 65001 >nul
title Regerar o relatorio da ultima varredura
setlocal enabledelayedexpansion

set "RAIZ=%~dp07-VARREDURA-DO-JOGO"
set "BASE=%RAIZ%\artefatos\desktop"

echo.
echo ============================================================
echo   REGERAR O RELATORIO
echo ============================================================
echo.
echo   NAO refaz a varredura. So redesenha o relatorio em cima
echo   do resultado que ja esta gravado.
echo   O arquivo de resultado tem quase 500 MB: pode levar
echo   alguns minutos. Nao feche esta janela.
echo.

set "ULTIMA="
for /f "tokens=* delims=" %%D in ('dir /b /ad /o-n "%BASE%\run-*" 2^>nul') do (
  if not defined ULTIMA set "ULTIMA=%%D"
)

if not defined ULTIMA (
  echo   [ERRO] Nenhuma varredura encontrada em:
  echo          %BASE%
  echo.
  pause
  exit /b 1
)

if not exist "%BASE%\!ULTIMA!\resultado.json" (
  echo   [ERRO] A varredura !ULTIMA! nao tem resultado.json.
  echo.
  pause
  exit /b 1
)

set "RELATORIO=%BASE%\!ULTIMA!\resultado.html"

echo   Varredura: !ULTIMA!
echo.

where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")

%PY% "%RAIZ%\executor\desktop_worker.py" --root "%RAIZ%" --run-dir "%BASE%\!ULTIMA!" --cancel "%TEMP%\clubef-cancel.flag" --protocol-version 5.3.0 --render-review-html "%BASE%\!ULTIMA!\resultado.json"

if errorlevel 1 (
  echo.
  echo   [ERRO] Nao foi possivel regerar. Veja a mensagem acima.
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   PRONTO. O RELATORIO ESTA AQUI:
echo.
echo   !RELATORIO!
echo ============================================================
echo.
echo   O caminho acima foi copiado para a area de transferencia.
echo   E so colar na barra de enderecos do Chrome (Ctrl+V).
echo.
echo !RELATORIO!| clip
start "" "!RELATORIO!"
echo.
pause
endlocal
