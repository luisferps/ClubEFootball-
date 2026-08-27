@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title DO BANCO - os insumos descem do Supabase
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\do_banco.py"
echo.
echo  ============================================================
echo   DO BANCO - os insumos descem do Supabase
echo  ============================================================
echo.
echo   Reescreve os arquivos de insumo da pasta com o que esta
echo   no Supabase agora. O arquivo vira copia; a fonte e o banco.
echo.
echo   Desce: cards_base, insumo_molde, insumo_tecnico,
echo   insumo_habilidade, insumo_bloqueio, insumo_impeto_catalogo.
echo.
echo   Banco vazio ou fora do ar NAO apaga nada.
echo   Backup de tudo em backups_do_banco\
echo.
echo   Para so olhar sem escrever: CONFERIR-O-BANCO.bat
echo.
echo  ------------------------------------------------------------
python "%PY%"
if errorlevel 1 (
  echo.
  echo   ^>^> PAROU. Leia o motivo acima.
  echo.
  pause
  exit /b 1
)
echo.
pause
