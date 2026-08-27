@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title SUBIR OS METADADOS DA TELA - tirar os 8 campos de dentro do HTML
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\subir_metadados_da_tela.py"
echo.
echo  ============================================================
echo   SUBIR OS METADADOS DA TELA
echo  ============================================================
echo.
echo   Os oito campos que so existiam dentro do HTML gerado vao
echo   para o banco, com a origem de cada valor.
echo.
echo   Onde a palavra da casca antiga nao tem traducao EXATA, o
echo   numero fica em branco e a palavra e guardada como estava.
echo   Traduzir no chute e inventar dado.
echo.
echo   NAO apaga nada. NAO muda pontuacao nenhuma.
echo.
echo   Antes disto: RESGATAR-DA-TELA.bat  e o
echo   CRIAR-METADADOS-NO-SUPABASE.html
echo.
echo  ------------------------------------------------------------
python "%PY%"
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Nada ficou pela metade. Leia o motivo acima.
  echo.
  pause
  exit /b 1
)
echo.
pause
