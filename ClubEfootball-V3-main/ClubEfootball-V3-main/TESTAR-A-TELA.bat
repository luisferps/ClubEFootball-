@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title TESTAR A TELA NO BANCO - 50 linhas
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\testar_a_tela.py"
echo.
echo  ============================================================
echo   TESTAR A TELA NO BANCO   -   so 50 linhas
echo  ============================================================
echo.
echo   Pega 50 linhas do encaixe que ja esta na pasta, manda para o
echo   banco, baixa de volta e compara CAMPO A CAMPO.
echo.
echo   ⛔ Nao mexe no encaixe. Nao mexe no gera_encaixe.
echo   ⛔ Nao apaga nada. Pode rodar com tudo ligado.
echo.
echo   E a prova antes de deixar as 12.370 subirem.
echo.
echo  ------------------------------------------------------------
python "%PY%"
echo.
pause
