@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title ENTRAR COM O efHUB - por cada campo no lugar certo
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\entrar_com_o_efhub.py"
echo.
echo  ============================================================
echo   ENTRAR COM O efHUB
echo  ============================================================
echo.
echo   Pega o efhub_fichas.json que o Console baixou e poe cada
echo   campo no lugar certo:
echo.
echo      pe ruim (uso e precisao) -^> pe_ruim.json
echo      progressao               -^> dados\levelcap.json
echo      a ficha crua inteira     -^> dados\efhub_bruto_por_card.json
echo      idade, lesao, estilo da IA, forma, condicao, corpo -^> o BANCO
echo.
echo   NUNCA apaga dado bom. So escreve onde estava vazio.
echo   CONTRAPROVA: se o efHub disser diferente do que ja esta
echo   guardado, ele NAO sobrescreve e NAO escolhe - guarda os
echo   dois lados em dados\divergencias.json.
echo.
echo   O arquivo efhub_fichas.json tem que estar NESTA pasta.
echo   Ele e baixado na sua pasta Downloads - recorte e cole aqui.
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
