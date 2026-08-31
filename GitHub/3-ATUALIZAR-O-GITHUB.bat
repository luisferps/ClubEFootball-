@echo off
chcp 65001 >nul
title 3 - ABRIR O UNICO BOTAO CENTRAL DO GITHUB

rem Esta copia nao possui logica propria. Ela chama o unico botao oficial
rem localizado na raiz do clone, evitando duas versoes diferentes.
call "%~dp0..\3-ATUALIZAR-O-GITHUB.bat" %*
exit /b %errorlevel%
