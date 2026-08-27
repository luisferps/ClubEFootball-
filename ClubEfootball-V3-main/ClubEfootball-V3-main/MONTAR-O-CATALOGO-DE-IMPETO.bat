@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title MONTAR O CATALOGO DE IMPETO
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\monta_catalogo_impeto.py"
echo.
echo  ============================================================
echo   MONTAR O CATALOGO DE IMPETO
echo  ============================================================
echo.
echo   O nome do impeto e CHUTE. O "+1" nao e nome: e quanto ele
echo   soma em cada um dos atributos dele.
echo.
echo   Hoje o sistema guarda 110 nomes para 38 impetos, porque o
echo   nivel esta colado no nome e 27 deles tem nome em portugues
echo   e em ingles.
echo.
echo   Este programa junta tudo PELOS ATRIBUTOS - dois nomes que
echo   mexem nos mesmos atributos sao o mesmo impeto - e grava um
echo   impeto por linha, com o nivel como numero separado.
echo.
echo   NAO apaga nada. NAO toca em carta nenhuma. NAO inventa
echo   degrau de condicional: isso fica vazio para voce conferir.
echo.
echo   Antes disto tem que ter rodado o sql\31-o-catalogo-de-impeto.sql
echo  ============================================================
echo.
python "%PY%" %*
echo.
pause
