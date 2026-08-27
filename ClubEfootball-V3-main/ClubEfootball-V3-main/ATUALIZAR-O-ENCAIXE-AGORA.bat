@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
set PYTHONDONTWRITEBYTECODE=1
title ATUALIZAR O ENCAIXE AGORA - bonus + tela + banco + Drive
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
echo   ATUALIZAR O ENCAIXE AGORA
echo  ============================================================
echo.
echo   Pega TUDO que o motor ja terminou e leva ate a tela.
echo   Nao roda o motor, nao coleta nada, nao refaz carta nenhuma.
echo.
echo   1. BAIXAR A BASE  (as cartas vem do banco, nao da pasta)
echo.
echo   2. MOTOR DE BONUS
echo      le saida_v6\linhas.jsonl (as que ja foram feitas)
echo      calcula corpo, pe ruim, estilo ativo e estilo da IA
echo      grava saida_v6\bonus.jsonl e a tabela `bonus`
echo.
echo.
echo   3. GERAR O ENCAIXE
echo      monta a tela, sobe as linhas para a tabela `tela_encaixe`
echo      e espelha em G:\Meu Drive\ClubeFootball
echo.
echo   ^>^> O MOTOR PRECISA ESTAR PARADO. Se ele estiver aberto,
echo      clique antes em PARAR-O-MOTOR.bat e espere fechar.
echo.
echo   Os tres programas terminam pedindo Enter quando rodam sozinhos.
echo   Aqui eles rodam em corrente, entao a pausa deles fica desligada
echo   (o ^< nul). Voce so aperta Enter uma vez, no fim de tudo.
echo.
echo  ------------------------------------------------------------
echo.
if exist "MOTOR-VIVO.txt" (
  echo   AVISO: existe MOTOR-VIVO.txt na pasta. Se a janela do motor
  echo   ainda estiver aberta, feche antes - os dois escrevendo no
  echo   mesmo linhas.jsonl corrompe o arquivo no Windows.
  echo.
  pause
)
echo.
echo  ------------------------------------------------------------
echo   1 de 3 - BAIXAR A BASE DO BANCO
echo  ------------------------------------------------------------
echo   As cartas moram no Supabase, nao na pasta. O motor de bonus
echo   precisa do campo visto_na_casca, e ele so existe la.
echo.
python baixar_base.py < nul
if errorlevel 1 (
  echo.
  echo   ^>^> Nao consegui baixar a base. Sem ela o bonus sai errado.
  echo      Me mande o que apareceu acima.
  echo.
  pause
  exit /b 1
)
echo.
echo  ------------------------------------------------------------
echo   2 de 3 - MOTOR DE BONUS
echo  ------------------------------------------------------------
python motor_bonus.py < nul
if errorlevel 1 (
  echo.
  echo   ^>^> O motor de bonus falhou. NAO vou gerar o encaixe com
  echo      bonus pela metade. Me mande o que apareceu acima.
  echo.
  pause
  exit /b 1
)
echo.
echo  ------------------------------------------------------------
echo   3 de 3 - GERAR O ENCAIXE E ESPELHAR
echo  ------------------------------------------------------------
python "ClubEfootball\programas\gera_encaixe.py" < nul
echo.
echo  ============================================================
echo   O que passou na tela ficou gravado em ULTIMA-RODADA-BONUS.txt
echo   na pasta do sistema. Abra no bloco de notas e copie com calma.
echo.
echo   PRONTO. Abra o ENCAIXE-TrueFootball.html no Drive e de
echo   Ctrl+F5. No canto de baixo a esquerda tem que aparecer a
echo   versao da tela.
echo  ============================================================
echo.
pause
