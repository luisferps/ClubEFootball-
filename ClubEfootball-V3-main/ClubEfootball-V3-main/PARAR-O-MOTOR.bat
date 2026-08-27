@echo off
chcp 65001 > nul
title PARAR O MOTOR - sem perder nada
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
echo.
echo  ============================================================
echo   PARAR O MOTOR - o jeito limpo
echo  ============================================================
echo.
echo   Cria o PARAR.txt. O motor testa esse arquivo A CADA LINHA:
echo   ele termina a carta que esta calculando, fecha os arquivos
echo   e sai sozinho.
echo.
echo   NAO SE PERDE NADA. Cada carta e gravada em tres lugares
echo   ANTES de ele passar para a proxima:
echo      saida_v6\linhas.jsonl   (com flush imediato)
echo      feitos.txt              (com flush imediato)
echo      tabela builds           (no Supabase)
echo.
echo   Conferido em 19/08: feitos.txt e linhas.jsonl com 17.461
echo   chaves cada um, ZERO divergencia.
echo.
echo   Quando o motor voltar, ele le o feitos.txt e pula tudo que
echo   ja esta la. Recomeca exatamente de onde parou.
echo.
echo  ------------------------------------------------------------
echo.
echo parado a pedido em %DATE% %TIME% > "PARAR.txt"
echo   ^>^> PARAR.txt criado.
echo.
echo   O motor pode levar alguns segundos para perceber - ele so
echo   olha o arquivo quando termina a carta em curso.
echo   Espere a janela dele fechar sozinha.
echo.
pause
