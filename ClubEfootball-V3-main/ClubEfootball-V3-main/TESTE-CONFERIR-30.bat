@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title TESTE - conferir so as 30 primeiras
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" goto :SEMCASA
echo.
echo  ==============================================================
echo   TESTE - so as 30 cartas de maior geral
echo  ==============================================================
echo.
echo   E o mesmo conferidor, so que para nas 30 primeiras.
echo   Serve para ver se funciona antes de rodar os 25 minutos.
echo   Leva menos de um minuto.
echo.
echo   NAO escreve na base. NAO escreve no banco.
echo.
echo  --------------------------------------------------------------
python "%~dp0programas\conferir_no_efootballdb.py" --limite 30
if errorlevel 1 goto :PAROU
echo.
echo  ==============================================================
echo   Deu certo. Me manda esta tela.
echo  ==============================================================
echo.
echo   Para rodar tudo depois, apague este arquivo:
echo      dados\conferencia_efootballdb_progresso.json
echo   e use o CONFERIR-NO-EFOOTBALLDB.bat
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
echo   ^>^> PAROU. Me manda esta tela.
echo.
pause
exit /b 1
