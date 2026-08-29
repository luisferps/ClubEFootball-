@echo off
setlocal
cd /d "%~dp0"

echo Extrator eFootball V4.6
echo Ordem produtiva: METADADOS ^> CARDS

rem Fontes oficiais conhecidas do eFootball no Windows.
rem O fluxo normal e automatico. Se alguma fonte realmente nao existir,
rem a interface continua oferecendo a selecao manual como recuperacao.
set "CLUBEF_SOURCE_DT870_UPDATED="
set "CLUBEF_SOURCE_DT200="
set "CLUBEF_SOURCE_DT870_ORIGINAL="
set "CLUBEF_SOURCE_DT261_BRA="

rem Instalacao Steam principal. O CMD trata ProgramFiles(x86) com parenteses de
rem forma fragil dentro de blocos; por isso usamos primeiro o caminho oficial
rem literal confirmado e depois ProgramFiles comum como variante.
if exist "C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk" set "CLUBEF_SOURCE_DT200=C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk"
if exist "C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk" set "CLUBEF_SOURCE_DT870_ORIGINAL=C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk"
if exist "C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk" set "CLUBEF_SOURCE_DT261_BRA=C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk"

if not defined CLUBEF_SOURCE_DT200 if exist "C:\Program Files\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk" set "CLUBEF_SOURCE_DT200=C:\Program Files\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk"
if not defined CLUBEF_SOURCE_DT870_ORIGINAL if exist "C:\Program Files\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk" set "CLUBEF_SOURCE_DT870_ORIGINAL=C:\Program Files\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk"
if not defined CLUBEF_SOURCE_DT261_BRA if exist "C:\Program Files\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk" set "CLUBEF_SOURCE_DT261_BRA=C:\Program Files\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk"

rem A atualizacao pode ficar diretamente em Download ou em subpastas internas.
if exist "C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk" set "CLUBEF_SOURCE_DT870_UPDATED=C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk"
if not defined CLUBEF_SOURCE_DT870_UPDATED (
  for /f "delims=" %%F in ('dir /b /s /a-d "C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk" 2^>nul') do set "CLUBEF_SOURCE_DT870_UPDATED=%%F"
)

echo.
echo Fontes detectadas:
echo DT870 atualizado: %CLUBEF_SOURCE_DT870_UPDATED%
echo DT200 base: %CLUBEF_SOURCE_DT200%
echo DT870 original: %CLUBEF_SOURCE_DT870_ORIGINAL%
echo Textos PT-BR: %CLUBEF_SOURCE_DT261_BRA%
echo.

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
