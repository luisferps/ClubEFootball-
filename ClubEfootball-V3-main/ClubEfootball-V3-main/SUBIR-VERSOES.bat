@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title SUBIR AS VERSOES - o molde inteiro e a identidade dos motores
rem  ---------------------------------------------------------------------
rem  ONDE ELE TRABALHA - vale ANTES e DEPOIS da mudanca de pasta.
rem  Ele PROCURA o config.txt em vez de cravar o caminho.
rem  ---------------------------------------------------------------------
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\subir_versoes.py"
echo.
echo  ============================================================
echo   AS VERSOES DO MOLDE E DOS MOTORES
echo  ============================================================
echo.
echo   Sobe o molde 5 INTEIRO (494 itens, 19 funcoes) e grava a
echo   identidade dos dois motores com a impressao digital de
echo   cada arquivo que compoe cada um.
echo.
echo   NAO apaga nada. As versoes 2 e 3 do molde ficam - sao historico.
echo   Se o molde do arquivo nao tiver 19 funcoes, ele PARA.
echo.
echo   Para so CONFERIR, sem escrever nada, arraste este .bat para
echo   uma janela de comando e acrescente a palavra  conferir
echo.
echo  ------------------------------------------------------------
python "%PY%" %1
if errorlevel 2 (
  echo.
  echo   ^>^> A RECEITA MUDOU desde a ultima gravacao. Leia acima.
  echo.
  pause
  exit /b 2
)
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Nada foi escrito. Leia o motivo acima.
  echo      Se reclamou de tabela que nao existe, abra antes o
  echo      CRIAR-VERSOES-NO-SUPABASE.html e siga os 7 passos.
  echo.
  pause
  exit /b 1
)
echo.
pause
