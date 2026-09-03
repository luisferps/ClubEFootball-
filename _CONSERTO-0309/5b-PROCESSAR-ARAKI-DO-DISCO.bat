@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem 5b - PROCESSAR AS 6 DO ARAKI, RODANDO O CODIGO DO DISCO
rem
rem POR QUE ESTE BOTAO EXISTE:
rem
rem O OperacaoLocalJson.exe e um executavel unico com o programa principal
rem EMBUTIDO dentro dele. Ele importa do disco os modulos que usa depois
rem (motor.py, roda_lote_v6.py, fonte_unica.py), e por isso o conserto do
rem motor pegou. Mas a funcao `calcular_linha`, que monta o pedido enviado ao
rem motor, mora no proprio programa principal, dentro do .exe. Editar o
rem operacao_local_json.py do disco nao muda o .exe.
rem
rem Era ela que jogava fora o degrau do Impeto condicional. Este botao chama o
rem .py do disco direto, com o Python da maquina, e assim usa o codigo
rem corrigido. Faz exatamente o mesmo trabalho do botao 5.

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY goto SEMPYTHON

set "RAIZ="
set "P=%~dp0"
for /l %%i in (1,1,6) do (
  if not defined RAIZ (
    if exist "!P!2-MOTORES\OTIMIZADOR\motor.py" set "RAIZ=!P!"
    for %%D in ("!P!..") do set "P=%%~fD\"
  )
)
if not defined RAIZ (
  echo  NAO ACHEI a raiz do sistema a partir daqui.
  pause
  exit /b 1
)
set "OPJ=!RAIZ!2-MOTORES\OTIMIZADOR\OPERACAO-LOCAL-JSON"

echo.
echo ============================================================
echo  5b - PROCESSAR AS 6 DO ARAKI (codigo do disco)
echo ============================================================
echo.
echo  Conferindo se o Python da maquina tem o numpy...
%PY% -c "import numpy" >nul 2>&1
if errorlevel 1 goto SEMNUMPY
echo  numpy: ok
echo.

pushd "!OPJ!"
%PY% "programas\operacao_local_json.py" processar --lote 49df0457-d36b-4562-a0fd-528c9bdd7f89
set "codigo=!ERRORLEVEL!"
popd

echo.
if not "!codigo!"=="0" (
  echo ============================================================
  echo  TERMINOU COM CODIGO !codigo!
  echo ============================================================
  echo  Manda esta tela para o Claude.
) else (
  echo ============================================================
  echo  PRONTO - agora clique em 6-ENVIAR-ARAKI.bat
  echo ============================================================
)
echo.
pause
exit /b !codigo!

:SEMNUMPY
echo.
echo ============================================================
echo  FALTA O NUMPY NO PYTHON DA MAQUINA
echo ============================================================
echo.
echo  O motor precisa dele para calcular. O .exe trazia o numpy
echo  embutido; o Python da maquina nao tem.
echo.
echo  Copie e cole a linha abaixo aqui mesmo nesta janela e de Enter:
echo.
echo     %PY% -m pip install numpy
echo.
echo  Depois feche esta janela e clique neste botao de novo.
echo.
cmd /k
exit /b 1

:SEMPYTHON
echo.
echo  PYTHON NAO ENCONTRADO. Instale o Python 3 marcando
echo  "Add python.exe to PATH".
echo.
pause
exit /b 1
