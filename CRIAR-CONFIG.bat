@echo off
chcp 65001 > nul
title CRIAR O CONFIG.TXT - a chave do banco
cd /d "%~dp0"
echo.
echo  ============================================================
echo   CRIAR O CONFIG.TXT
echo  ============================================================
echo.
echo   Este arquivo guarda a chave do Supabase. Ele NAO vai para o
echo   GitHub - por isso a maquina nova precisa dele criado na mao.
echo.
if exist "config.txt" (
  echo   ^>^> JA EXISTE um config.txt nesta pasta.
  echo      Se quiser trocar a chave, apague ele e rode de novo.
  echo.
  pause
  exit /b 0
)
echo   Pegue a chave em:
echo   https://supabase.com/dashboard/project/trqqpsnafpbudtvvicch/settings/api-keys
echo.
echo   E a "service_role" / "secret". Copie ela inteira.
echo.
set /p CHAVE="   Cole a chave aqui e aperte Enter: "
if "%CHAVE%"=="" (
  echo.
  echo   ^>^> Nada foi colado. Nao criei nada.
  echo.
  pause
  exit /b 1
)
(
echo SUPABASE_URL=https://trqqpsnafpbudtvvicch.supabase.co
echo SUPABASE_KEY=%CHAVE%
) > config.txt
echo.
echo   ^>^> config.txt criado nesta pasta.
echo.
echo   Confira que ele NAO aparece no GitHub Desktop. Se aparecer,
echo   o .gitignore nao pegou - me avise antes de dar push.
echo.
pause
