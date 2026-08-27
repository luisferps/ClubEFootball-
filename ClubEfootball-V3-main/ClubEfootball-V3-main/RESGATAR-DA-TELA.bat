@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title RESGATAR DA TELA - os oito campos que so existem no HTML
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
set "PY=%~dp0programas\resgatar_da_tela.py"
echo.
echo  ============================================================
echo   RESGATAR DA TELA
echo  ============================================================
echo.
echo   Oito campos do sistema NAO existem em arquivo de dado
echo   nenhum, em tabela nenhuma do banco, e nenhum programa os
echo   coleta. Eles so existem DENTRO DO HTML ja gerado, copiados
echo   de uma geracao para a proxima:
echo.
echo      estilo de jogo da IA   -   idade   -   lesao
echo      pe ruim (uso e precisao)   -   mestre
echo      maximo   -   pontuacao maxima da tela
echo.
echo   Este programa tira eles de la e grava num arquivo de dado,
echo   com a origem de cada valor.
echo.
echo   NAO escreve no banco. NAO mexe em HTML nenhum. So le.
echo.
echo  ------------------------------------------------------------
python "%PY%"
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima. Nada foi perdido - ele
  echo      guarda o arquivo anterior antes de gravar o novo.
  echo.
  pause
  exit /b 1
)
echo.
pause
