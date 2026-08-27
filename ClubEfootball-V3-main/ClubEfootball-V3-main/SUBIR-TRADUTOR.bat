@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title SUBIR O TRADUTOR - como cada fonte chama cada coisa
rem  ---------------------------------------------------------------------
rem  ONDE ELE TRABALHA - vale ANTES e DEPOIS da mudanca de 16/08
rem  Hoje o config.txt esta na pasta de cima. Quando tudo for movido para
rem  dentro da ClubEfootball, ele vai estar aqui mesmo. Entao o .bat
rem  PROCURA, em vez de cravar o caminho.
rem  ---------------------------------------------------------------------
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo      Este atalho tem que ficar na pasta do sistema ou numa subpasta dela.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\subir_tradutor.py"
echo.
echo  ============================================================
echo   SUBIR O TRADUTOR
echo  ============================================================
echo.
echo   Leva o CHAVES.json (feito em 14/08 e nunca usado) para o
echo   banco, e preenche o codigo fixo e os rotulos das 19 funcoes.
echo.
echo   NAO apaga nada. NAO troca chave nenhuma.
echo   Se qualquer funcao nao tiver par, ele PARA e nao sobe nada.
echo.
echo  ------------------------------------------------------------
python "%PY%"
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Nada foi subido. Leia o motivo acima.
  echo      Se ele reclamou de coluna que nao existe, abra antes o
  echo      ClubEfootball\CRIAR-TRADUTOR-NO-SUPABASE.html
  echo      e siga os 7 passos.
  echo.
  pause
  exit /b 1
)
echo.
pause
