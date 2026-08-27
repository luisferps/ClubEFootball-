@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title CONFERIR o filtro - nao grava nada
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" goto :SEMCASA
echo.
echo  ==============================================================
echo   CONFERIR O FILTRO   -   nao grava nada
echo  ==============================================================
echo.
echo   O A-VOLTA-AUTOMATICA marcou 5.814 linhas para refazer.
echo   Ele compara so a HORA: viu que a carta foi tocada depois da
echo   linha e marcou. NAO olha qual campo mudou.
echo.
echo   Hoje mudaram 1.437 cartas - e na quase totalidade mudou
echo   SO A DATA. Data nao entra na nota. Refazer essas linhas
echo   gasta maquina para chegar no mesmo numero.
echo.
echo   Este aqui compara a base de agora com a de antes, campo por
echo   campo, e deixa no PRECISA-REFAZER so as cartas em que mudou
echo   alguma coisa que o motor LE.
echo.
echo   Na duvida, ele REFAZ. Errar para mais custa maquina;
echo   errar para menos deixa nota errada de pe.
echo.
echo   MODO CONFERIR: nada vai ser gravado. So mostra.
echo.
echo  --------------------------------------------------------------
python "%~dp0programas\so_o_que_muda_a_conta.py" --conferir
if errorlevel 1 goto :PAROU
echo.
pause
exit /b 0
:SEMCASA
echo.
echo   ^^>^^> nao achei o config.txt nem aqui nem na pasta de cima.
echo.
pause
exit /b 1
:PAROU
echo.
echo   ^^>^^> PAROU. Leia o motivo acima.
echo.
pause
exit /b 1
