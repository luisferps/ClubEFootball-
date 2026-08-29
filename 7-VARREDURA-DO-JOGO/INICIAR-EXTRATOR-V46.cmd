@echo off
setlocal
cd /d "%~dp0"

echo Extrator eFootball V4.6.4
echo Ordem produtiva: METADADOS ^> CARDS

rem Porta exclusiva desta versao para nao reaproveitar runtime antigo.
set "CLUBEF_EXTRACTOR_PORT=8769"

rem Este launcher nao decide onde estao os CPKs.
rem O Extrator procura sozinho no Windows antes de validar/extrair.
set "CLUBEF_SOURCE_DT870_UPDATED="
set "CLUBEF_SOURCE_DT200="
set "CLUBEF_SOURCE_DT870_ORIGINAL="
set "CLUBEF_SOURCE_DT261_BRA="

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 executor\servidor_v46.py
  goto :fim
)

where python >nul 2>nul
if %errorlevel%==0 (
  python executor\servidor_v46.py
  goto :fim
)

echo ERRO: Python nao encontrado no PATH.
pause

:fim
endlocal
