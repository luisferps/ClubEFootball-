@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title CONFERIR O BANCO - so olha
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\do_banco.py"
echo.
echo  ============================================================
echo   CONFERIR O BANCO - so olha
echo  ============================================================
echo.
echo   Baixa os insumos, compara com a pasta e NAO ESCREVE NADA.
echo.
echo   Serve para ver quem esta na frente antes de virar a chave.
echo   Pode rodar com o motor rodando.
echo.
echo  ------------------------------------------------------------
python "%PY%" --conferir
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima.
  echo.
  pause
  exit /b 1
)
echo.
pause
