@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title O VIGIA - um botao, ele faz o resto
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\o_vigia.py"
echo.
echo  ============================================================
echo   O VIGIA
echo  ============================================================
echo.
echo   UM botao. Ele faz tudo sozinho:
echo.
echo     1. abre o Chrome e manda nele
echo     2. le as 600 box do efHub, da mais nova para a mais velha
echo     3. le as cartas de cada box
echo     4. descobre box nova e carta nova
echo     5. puxa a ficha inteira de cada uma
echo     6. grava aqui na pasta
echo.
echo   A ORDEM DA FILA:
echo     1. A BOX NOVA ........... prioridade, sempre
echo     2. O QUE FALTA REFAZER .. carta nossa com furo
echo     3. O RESTANTE ........... por overall, o maior primeiro
echo.
echo   ATENCAO: vai abrir uma janela do Chrome. NAO FECHE ela
echo   enquanto ele trabalha. E um perfil separado - nao mexe
echo   no seu Chrome do dia a dia.
echo.
echo   Ele NAO escreve no banco e NAO apaga nada. Backup antes.
echo.
echo  ------------------------------------------------------------
python "%PY%" %1
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima.
  echo.
  pause
  exit /b 1
)
echo.
pause
