@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title SEPARAR OS IMPETOS - o nome, o nivel e o que ele aumenta
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\separar_os_impetos.py"
echo.
echo  ============================================================
echo   SEPARAR OS IMPETOS
echo  ============================================================
echo.
echo   Hoje TRES coisas moram na mesma string:
echo.
echo      "Precisao +3"  =  o NOME     Precisao
echo                        o NIVEL    3
echo                        e QUAIS ATRIBUTOS ele aumenta
echo.
echo   E o card guarda so a SOMA por atributo, jogando fora quais
echo   impetos produziram aquela soma. Por isso o George Best
echo   aparece com "+5" - que nao existe: e +2 mais +3.
echo.
echo   Este programa separa as tres coisas e confere cada uma
echo   contra o dado do card. O que nao fechar vira NAO SEI, com
echo   o motivo escrito. Nada e chutado.
echo.
echo   NAO escreve no banco. NAO mexe em card nenhum.
echo   Grava tres arquivos:
echo      IMPETOS.json .................. o catalogo separado
echo      dados\impetos_por_card.json ... o impeto de cada card
echo      IMPETOS-QUE-FALTAM.txt ........ o que nao deu para saber
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
pause
