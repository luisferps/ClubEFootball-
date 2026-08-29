@echo off
setlocal
cd /d "%~dp0"

echo Extrator eFootball V4.6
echo Ordem produtiva: METADADOS ^> CARDS

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
