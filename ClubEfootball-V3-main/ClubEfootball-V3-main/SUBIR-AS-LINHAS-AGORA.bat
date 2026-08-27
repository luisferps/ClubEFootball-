@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title SUBIR AS LINHAS DO ENCAIXE PARA O BANCO
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\subir_as_linhas_agora.py"
echo.
echo  ============================================================
echo   SUBIR AS LINHAS DO ENCAIXE PARA O BANCO
echo  ============================================================
echo.
echo   Le o encaixe que ja esta na pasta e manda as linhas dele
echo   para o banco. E o que faz o ENCAIXE-DO-BANCO.html ter o
echo   que mostrar.
echo.
echo   ⛔ Nao gera nada. Nao roda motor. Nao apaga nada.
echo   ⛔ Sobe so o que mudou desde a ultima vez.
echo.
echo   A PRIMEIRA vez demora alguns minutos ^(sao 35 MB^).
echo.
echo  ------------------------------------------------------------
python "%PY%"
echo.
pause
