@echo off
rem ==================================================================
rem  RODADA DIARIA — e este que o Windows chama sozinho a meia-noite.
rem  Nao tem pause: ele roda e fecha. O relatorio fica em ULTIMA-RODADA.txt
rem  Voce tambem pode dar dois cliques nele para rodar na hora.
rem ==================================================================
cd /d "%~dp0"
if not exist "config.txt" cd ..
title RODADA DIARIA - TrueFootball
set "PYTHONUTF8=1"
set "PYTHONUNBUFFERED=1"
set "PYTHONDONTWRITEBYTECODE=1"
chcp 65001 >nul
python "%~dp0programas\rodada_diaria.py"
