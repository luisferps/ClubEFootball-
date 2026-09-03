@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem CONSERTO 03/09 - etapa 2 de 3: calcular as 80 linhas, uma por vez.
rem Nao envia nada ao banco. Ctrl+C para com seguranca; o que ja foi
rem gravado fica salvo.

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

if not exist "!OPJ!\bin\OperacaoLocalJson.exe" (
  echo  O programa local nao foi encontrado em:
  echo  !OPJ!\bin
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  2 de 3 - PROCESSAR AS 80 LINHAS
echo ============================================================
echo  Uma linha por vez. Nada e enviado ao banco nesta etapa.
echo  Ctrl+C para com seguranca.
echo.

pushd "!OPJ!"
"bin\OperacaoLocalJson.exe" processar --lote eb4d4208-391c-41d6-a43e-38ac25a9c296
set "codigo=!ERRORLEVEL!"
popd

echo.
if not "!codigo!"=="0" (
  echo ============================================================
  echo  TERMINOU COM CODIGO !codigo!
  echo ============================================================
  echo  Os JSONs ja gravados foram preservados. Manda a tela.
) else (
  echo ============================================================
  echo  PRONTO - agora clique em 3-ENVIAR.bat
  echo ============================================================
)
echo.
pause
exit /b !codigo!
