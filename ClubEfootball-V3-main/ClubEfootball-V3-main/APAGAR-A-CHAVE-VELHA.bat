@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title APAGAR A CHAVE VELHA - escreve no banco
cd /d "%~dp0"
if not exist "config.txt" cd ..
echo.
echo  ============================================================
echo   APAGAR-A-CHAVE-VELHA
echo  ============================================================
echo.
echo   A tabela builds tem linhas gravadas com a chave VELHA:
echo     104717 arroba LE   - a carta mais a posicao comprada
echo   Hoje a chave e so  104717.  A fila de hoje tem ZERO com arroba.
echo.
echo   Ele separa em duas familias:
echo     ja existe com a chave nova .... copia velha, so tirar lixo
echo     nao existe ..................... anota e volta para a fila
echo.
echo   ^>^> ESTE APAGA LINHA DO BANCO. Leia o relatorio antes.
echo.
echo  ------------------------------------------------------------
python "%~dp0programas\limpar_a_chave_velha.py" apagar
if errorlevel 1 goto parou
echo.
pause
exit /b 0
:parou
echo.
echo   ^>^> PAROU. Leia o motivo acima.
echo.
pause
exit /b 1
