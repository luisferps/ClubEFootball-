@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title CONFERIR A REFORMA - o banco recebeu escrita, a reforma sobreviveu?
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\conferir_a_reforma.py"
echo.
echo  ============================================================
echo   CONFERIR A REFORMA
echo  ============================================================
echo.
echo   As 02h25 o GERAR-ENCAIXE.bat foi rodado, e ele roda o motor
echo   de bonus junto - que ESCREVE no banco. Isso aconteceu no
echo   meio da reforma, depois dos quatro passos ja terem entrado.
echo.
echo   Este programa pergunta ao banco se a reforma continua de pe:
echo      as 19 funcoes com codigo e rotulo
echo      a tabela de traducao
echo      o molde 5 e as versoes antigas
echo      a identidade dos dois motores
echo      o estado de cada campo de cada carta
echo.
echo   NAO escreve nada. NAO apaga nada. NAO conserta nada. So conta.
echo.
echo  ------------------------------------------------------------
python "%PY%"
if errorlevel 2 (
  echo.
  echo   ^>^> NAO FALEI COM O BANCO. Isso nao quer dizer que perdeu
  echo      nada - quer dizer que eu nao consegui perguntar.
  echo.
  pause
  exit /b 2
)
if errorlevel 1 (
  echo.
  echo   ^>^> ALGUMA COISA FOI ATROPELADA. Leia a lista acima.
  echo      Nada foi consertado - a decisao e sua.
  echo.
  pause
  exit /b 1
)
echo.
pause
