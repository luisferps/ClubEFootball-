@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title CONFERIR NO efootballdb - a revisao dos antigos
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" goto :SEMCASA
echo.
echo  ==============================================================
echo   CONFERIR NO efootballdb   -   a revisao dos antigos
echo  ==============================================================
echo.
echo   Bate o que a gente TEM contra o que a fonte DIZ, carta por
echo   carta, em CINCO coisas agora:
echo.
echo      1. os 26 atributos
echo      2. as HABILIDADES de fabrica            (novo)
echo      3. altura e peso                        (novo)
echo      4. a vaga - tem? quantas? quantas cheias?
echo      5. o impeto - NOME e NIVEL, separados
echo.
echo   NAO escreve na base. NAO escreve no banco. So confere.
echo.
echo   O mapa das habilidades NAO esta escrito aqui - ele APRENDE,
echo   contando quantas vezes o campo da fonte vem junto com a
echo   habilidade no nosso fab. O que nao fechar em 95 por cento
echo   ele NAO confere, e diz quais ficaram de fora.
echo.
echo   As fichas ficam GUARDADAS. A primeira vez demora ~25 min;
echo   da segunda em diante e instantaneo.
echo.
echo   O estilo da IA e as 12 medidas do corpo NAO entram aqui:
echo   o efootballdb nao tem. Esses dois vao pelo efHub.
echo.
echo  --------------------------------------------------------------
python "%~dp0programas\conferir_no_efootballdb.py" %*
if errorlevel 1 goto :PAROU
echo.
echo  ==============================================================
echo   PRONTO. Abra o CONFERENCIA-EFOOTBALLDB.html
echo  ==============================================================
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
