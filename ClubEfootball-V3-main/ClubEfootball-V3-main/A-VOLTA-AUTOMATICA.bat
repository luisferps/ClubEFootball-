@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title A VOLTA AUTOMATICA - o que precisa refazer
cd /d "%~dp0"
if not exist "config.txt" cd ..
echo.
echo  ============================================================
echo   A VOLTA AUTOMATICA - passo 7
echo  ============================================================
echo.
echo   Pergunta ao banco o que envelheceu:
echo     - a carta mudou depois da linha ter sido calculada
echo     - a linha saiu de uma receita (motor) que nao vale mais
echo.
echo   Escreve PRECISA-REFAZER.txt no formato que o
echo   REFAZER-DE-VERDADE.bat ja consome.
echo.
echo   ^>^> SO LE. Nao mexe na fila, no feitos.txt nem no banco.
echo      Pode rodar com o motor rodando.
echo.
echo  ------------------------------------------------------------
python "%~dp0programas\a_volta_automatica.py"
if errorlevel 1 goto parou
echo.
pause
exit /b 0
:parou
echo.
echo   ^>^> PAROU. Leia o motivo acima - e informacao, nao falha.
echo.
pause
