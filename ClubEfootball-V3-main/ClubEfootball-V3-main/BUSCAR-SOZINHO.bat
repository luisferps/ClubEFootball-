@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title O BRACO QUE BUSCA SOZINHO - efootballdb
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\braco_efootballdb.py"
echo.
echo  ============================================================
echo   O BRACO QUE BUSCA SOZINHO
echo  ============================================================
echo.
echo   Le a fila de coleta e visita SO as cartas que estao em
echo   NAO SEI. Fonte: efootballdb - a unica que responde sem
echo   navegador. Uma visita traz box, data e vaga de uma vez.
echo.
echo   CONTRAPROVA: se o que veio for DIFERENTE do que ja estava
echo   guardado, ele NAO sobrescreve e NAO escolhe. Guarda os
echo   dois lados em dados\divergencias.json para uma terceira
echo   fonte desempatar.
echo.
echo   Nunca apaga dado bom. Grava a cada 25 cartas.
echo   Pode fechar a janela a hora que quiser - na proxima vez
echo   ele continua de onde parou.
echo.
echo  ------------------------------------------------------------
python "%PY%" %1
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima. Os backups estao ao lado,
  echo      com ANTES-DO-BRACO no nome.
  echo.
  pause
  exit /b 1
)
echo.
pause
