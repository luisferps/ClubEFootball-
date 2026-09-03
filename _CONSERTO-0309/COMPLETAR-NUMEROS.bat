@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem CONSERTO 03/09 - etapa avulsa: completar os 26 atributos finais nos
rem Builds gravados antes de a porta do banco passar a guarda-los.
rem
rem Rele os JSON de ENVIADOS e PENDENTES e manda cada um de novo pela mesma
rem porta. Ela reconhece que a linha ja esta concluida, confere que o
rem resultado bate byte a byte, nao duplica nada e so preenche o que faltava.
rem Nenhum calculo e refeito e nenhum arquivo e apagado.

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

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo  PYTHON NAO ENCONTRADO. Instale o Python 3 marcando "Add to PATH".
  echo.
  pause
  exit /b 1
)

pushd "!OPJ!"
%PY% "%~dp0programas\completar_numeros_v1.py" %*
set "codigo=!ERRORLEVEL!"
popd

echo.
if not "!codigo!"=="0" echo  Terminou com codigo !codigo!. Manda esta tela para o Claude.
echo.
pause
exit /b !codigo!
