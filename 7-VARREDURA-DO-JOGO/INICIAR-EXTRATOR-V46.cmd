@echo off
setlocal
cd /d "%~dp0"

echo Extrator eFootball V4.6
echo Ordem produtiva: METADADOS ^> CARDS

rem Fontes padrao da instalacao oficial no Windows.
rem Se existirem, o launcher entrega os caminhos diretamente ao executor.
rem Se nao existirem, o Extrator mantem a descoberta/fallback manual normal.
set "CLUBEF_SOURCE_DT870_UPDATED="
set "CLUBEF_SOURCE_DT200="
set "CLUBEF_SOURCE_DT870_ORIGINAL="
set "CLUBEF_SOURCE_DT261_BRA="

if exist "%ProgramData%\KONAMI\eFootball\ST\Download\dt870_console_win.cpk" (
  set "CLUBEF_SOURCE_DT870_UPDATED=%ProgramData%\KONAMI\eFootball\ST\Download\dt870_console_win.cpk"
)

if exist "%ProgramFiles(x86)%\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk" (
  set "CLUBEF_SOURCE_DT200=%ProgramFiles(x86)%\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk"
)
if exist "%ProgramFiles(x86)%\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk" (
  set "CLUBEF_SOURCE_DT870_ORIGINAL=%ProgramFiles(x86)%\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk"
)
if exist "%ProgramFiles(x86)%\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk" (
  set "CLUBEF_SOURCE_DT261_BRA=%ProgramFiles(x86)%\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk"
)

rem Fallback para maquinas onde as variaveis do Windows nao estejam expostas ao processo.
if not defined CLUBEF_SOURCE_DT870_UPDATED if exist "C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk" set "CLUBEF_SOURCE_DT870_UPDATED=C:\ProgramData\KONAMI\eFootball\ST\Download\dt870_console_win.cpk"
if not defined CLUBEF_SOURCE_DT200 if exist "C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk" set "CLUBEF_SOURCE_DT200=C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt200_console_all.cpk"
if not defined CLUBEF_SOURCE_DT870_ORIGINAL if exist "C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk" set "CLUBEF_SOURCE_DT870_ORIGINAL=C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt870_console_win.cpk"
if not defined CLUBEF_SOURCE_DT261_BRA if exist "C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk" set "CLUBEF_SOURCE_DT261_BRA=C:\Program Files (x86)\Steam\steamapps\common\eFootball\cpk\dt261_bra_console_win.cpk"

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
echo Use o ambiente ja utilizado pelo Extrator ou instale as dependencias do projeto.
pause

:fim
endlocal
