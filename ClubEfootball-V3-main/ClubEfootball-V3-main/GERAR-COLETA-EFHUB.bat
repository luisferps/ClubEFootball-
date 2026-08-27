@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title GERAR A COLETA DO efHUB - o bloco para colar no Console
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\gerar_coleta_efhub.py"
echo.
echo  ============================================================
echo   GERAR A COLETA DO efHUB
echo  ============================================================
echo.
echo   A porta do efHub recusa quem chama de fora do navegador -
echo   devolve 403. De dentro de uma aba do proprio site, a mesma
echo   chamada responde 200. So o seu Chrome passa.
echo.
echo   Entao este programa NAO coleta. Ele MONTA a coleta: le a
echo   fila e escreve uma pagina com o bloco pronto para colar
echo   no Console (F12), com a lista exata das cartas que faltam.
echo.
echo   NAO pede o banco inteiro. Pede so o que esta em NAO SEI.
echo.
echo  ------------------------------------------------------------
python "%PY%"
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima.
  echo.
  pause
  exit /b 1
)
echo.
echo   Agora abra o COLETAR-EFHUB-AGORA.html e siga os 8 passos.
echo.
pause
