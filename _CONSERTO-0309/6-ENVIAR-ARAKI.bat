@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem CONSERTO 03/09 - etapa 3 de 3: mandar as 80 ao banco, uma a uma.

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
echo  6 de 6 - ENVIAR AS 6 DO ARAKI
echo ============================================================
echo.

pushd "!OPJ!"
"bin\OperacaoLocalJson.exe" enviar --lote 49df0457-d36b-4562-a0fd-528c9bdd7f89
set "codigo=!ERRORLEVEL!"
popd

echo.
if not "!codigo!"=="0" (
  echo ============================================================
  echo  TERMINOU COM CODIGO !codigo!
  echo ============================================================
  echo  Nada foi apagado. Manda esta tela para o Claude.
) else (
  echo ============================================================
  echo  PRONTO - as 6 do Araki estao no banco.
  echo ============================================================
)
echo.
pause
exit /b !codigo!
