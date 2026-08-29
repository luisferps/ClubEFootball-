@echo off
setlocal
cd /d "%~dp0"

echo Extrator eFootball V4.6.3
echo Ordem produtiva: METADADOS ^> CARDS

rem Porta exclusiva desta versao para nao reaproveitar runtime antigo.
set "CLUBEF_EXTRACTOR_PORT=8768"

rem IMPORTANTE: este launcher nao decide onde estao os CPKs.
rem A descoberta automatica pertence ao nucleo original do Extrator,
rem que procura diretamente em ProgramData e na pasta Steam do eFootball.
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
