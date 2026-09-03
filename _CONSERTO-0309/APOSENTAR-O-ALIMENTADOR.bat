@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem APOSENTA O ALIMENTADOR - conserto 03/09
rem Ordem do Luis: o Alimentador e a subida da coleta sao da era em que o dado
rem vinha de site (efHub / efootballdb). Hoje o dado vem do arquivo do jogo,
rem pelo Extrator (7-VARREDURA-DO-JOGO). Eles sao a ULTIMA ligacao viva do
rem sistema com o esquema velho.
rem
rem NADA E APAGADO. So muda de nome e de pasta, do mesmo jeito que ja foi feito
rem com LEGADO-PAINEL-APOSENTADO e com "8 - EXTRATOR DE FOTOS - LEGADO".

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
  echo  Este arquivo precisa ficar DENTRO da copia do sistema.
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  APOSENTAR O ALIMENTADOR
echo ============================================================
echo.
echo  Pasta: !RAIZ!
echo.
echo  1^) 3-ALIMENTADOR                 vira   3-ALIMENTADOR - LEGADO
echo  2^) SUBIDOR-DA-COLETA.js          vai para   5-COLETA-EM-PARALELO\LEGADO\
echo.
echo  Nada e apagado. Os dados ja coletados nao sao tocados.
echo.
pause

set "erros=0"
echo.

if exist "!RAIZ!3-ALIMENTADOR - LEGADO\" (
  echo  [1] ja estava aposentado.
) else (
  if exist "!RAIZ!3-ALIMENTADOR\" (
    ren "!RAIZ!3-ALIMENTADOR" "3-ALIMENTADOR - LEGADO"
    if errorlevel 1 (
      echo  [1] FALHOU ao renomear.
      set /a erros+=1
    ) else (
      echo  [1] ok - 3-ALIMENTADOR - LEGADO
    )
  ) else (
    echo  [1] a pasta nao existe mais, nada a fazer.
  )
)

set "COL=!RAIZ!5-COLETA-EM-PARALELO"
if exist "!COL!\SUBIDOR-DA-COLETA.js" (
  if not exist "!COL!\LEGADO\" mkdir "!COL!\LEGADO"
  move /Y "!COL!\SUBIDOR-DA-COLETA.js" "!COL!\LEGADO\" >nul
  if errorlevel 1 (
    echo  [2] FALHOU ao mover.
    set /a erros+=1
  ) else (
    echo  [2] ok - 5-COLETA-EM-PARALELO\LEGADO\SUBIDOR-DA-COLETA.js
  )
) else (
  echo  [2] ja estava aposentado.
)

echo.
echo ============================================================
if "!erros!"=="0" (
  echo  PRONTO.
  echo  O sistema nao tem mais nenhuma ligacao viva com o esquema velho.
) else (
  echo  Terminou com !erros! falha^(s^). Manda esta tela para o Claude.
)
echo ============================================================
echo.
pause
exit /b !erros!
