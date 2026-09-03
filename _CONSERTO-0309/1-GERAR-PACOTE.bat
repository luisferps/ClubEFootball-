@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem CONSERTO 03/09 - etapa 1 de 3: baixar a fotografia selada do lote.
rem 80 linhas de 13 cartas com vaga fisica cujo Build saiu sem Impeto
rem adicional. Nao calcula, nao envia, nao altera a fila.

rem acha a raiz do sistema subindo pastas ate encontrar o motor
set "RAIZ="
set "P=%~dp0"
for /l %%i in (1,1,6) do (
  if not defined RAIZ (
    if exist "!P!2-MOTORES\OTIMIZADOR\motor.py" set "RAIZ=!P!"
    for %%D in ("!P!..") do set "P=%%~fD\"
  )
)
if not defined RAIZ (
  echo.
  echo  NAO ACHEI a raiz do sistema a partir daqui.
  echo  Esta pasta precisa ficar DENTRO da copia do sistema, no mesmo
  echo  nivel de 1-SISTEMA e 2-MOTORES.
  echo.
  pause
  exit /b 1
)
set "OTM=!RAIZ!2-MOTORES\OTIMIZADOR"
set "OPJ=!OTM!\OPERACAO-LOCAL-JSON"

echo.
echo ============================================================
echo  1 de 3 - GERAR O PACOTE
echo ============================================================
echo  Lote: eb4d4208-391c-41d6-a43e-38ac25a9c296
echo  80 linhas - 13 cartas
echo.

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo  PYTHON NAO ENCONTRADO. Instale o Python 3 marcando "Add to PATH".
  echo.
  pause
  exit /b 1
)

pushd "!OTM!"
%PY% "GERAR-PACOTE-CORRECAO-IMPETOS-V8.py" eb4d4208-391c-41d6-a43e-38ac25a9c296
set "codigo=!ERRORLEVEL!"
popd

echo.
if not "!codigo!"=="0" (
  echo ============================================================
  echo  NAO DEU - codigo !codigo!
  echo ============================================================
  echo  Manda esta tela para o Claude.
) else (
  echo ============================================================
  echo  PRONTO - agora clique em 2-PROCESSAR.bat
  echo ============================================================
)
echo.
pause
exit /b !codigo!
