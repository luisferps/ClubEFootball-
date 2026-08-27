@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title CONFERIR a data do box - nao grava nada
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" goto :SEMCASA
echo.
echo  ==============================================================
echo   CONFERIR A DATA DO BOX   -   nao grava nada
echo  ==============================================================
echo.
echo   O nome do box NAO e tocado. "POTW 2 May '26" continua
echo   inteiro - cada POTW e uma box diferente, e o nome e a
echo   chave unica dela. So a DATA vai para um campo separado.
echo.
echo   Hoje 2.485 cards estao com a data do dump (2026-07-09),
echo   que e a mesma para todos e nao e lancamento de nada.
echo   A data verdadeira esta escrita ali do lado, no nome do box.
echo.
echo   ISSO E A CAUSA RAIZ das vagas de impeto fantasma: sem a
echo   data certa, a 1a trava - carta anterior a 12/09/2024 nao
echo   tem vaga - nunca pode ser aplicada.
echo.
echo   O que ele vai fazer:
echo      1.437 datas recuperadas do nome do box
echo        443 delas anteriores a 12/09/2024
echo         35 brigas de data - NAO sobrescreve, so anota
echo      1.180 nomes sem data ficam esperando o efootballdb
echo.
echo   NAO inventa data de temporada nem de ano solto.
echo   "Borussia Dortmund Pack 25-26" NAO vira data.
echo.
echo   MODO CONFERIR: nada vai ser gravado. So mostra.
echo.
echo  --------------------------------------------------------------
python "%~dp0programas\separar_a_data_do_box.py" --conferir
if errorlevel 1 goto :PAROU
echo.
pause
exit /b 0
:SEMCASA
echo.
echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
echo.
pause
exit /b 1
:PAROU
echo.
echo   ^>^> PAROU. Leia o motivo acima.
echo.
pause
exit /b 1
