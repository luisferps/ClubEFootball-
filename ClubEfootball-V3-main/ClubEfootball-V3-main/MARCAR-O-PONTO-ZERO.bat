@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title MARCAR O PONTO ZERO da volta automatica
cd /d "%~dp0"
if not exist "config.txt" cd ..
echo.
echo  ============================================================
echo   MARCAR O PONTO ZERO
echo  ============================================================
echo.
echo   A hora de cada carta so passou a significar "foi aqui que
echo   este dado mudou" a partir de hoje, 16/08 as 16h.
echo.
echo   Antes disso o subir_base carimbava as 6.469 cartas a cada
echo   upload - e a ultima rodada com o defeito carimbou todas
echo   juntas. Por isso todas parecem mais novas que todas as linhas.
echo.
echo   Este atalho grava a hora de agora como o PONTO ZERO:
echo     carimbo ATE aqui .... nao vale como prova de mudanca
echo     carimbo DEPOIS ...... o dado mudou de verdade
echo.
echo   ^>^> Nao mexe em linha nenhuma. So grava uma data num arquivo.
echo.
echo  ------------------------------------------------------------
python "%~dp0programas\a_volta_automatica.py" marcar
echo.
pause
