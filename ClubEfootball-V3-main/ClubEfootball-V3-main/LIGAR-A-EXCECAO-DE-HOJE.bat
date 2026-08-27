@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title LIGAR A EXCECAO DE HOJE
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo   ^>^> nao achei o config.txt.
  pause
  exit /b 1
)
set "PY=%~dp0programas\excecao_de_hoje.py"
echo.
echo  ============================================================
echo   LIGAR A EXCECAO DE HOJE
echo  ============================================================
echo.
echo   O QUE ELA FAZ, so por hoje:
echo     1. a RODADA nao chama o motor .... quem roda e o SO-O-MOTOR.bat
echo     2. o passo 5k fica parado ........ ele exige o motor parado
echo.
echo   O QUE ELA DEIXA LIGADO, DE PROPOSITO:
echo     a etapa 8 (regerar o Encaixe) CONTINUA rodando. E ela que
echo     enche a tabela tela_encaixe, que e de onde a tela le. Sem
echo     ela as 6.230 linhas novas nao apareceriam em lugar nenhum.
echo     O design nao corre risco: o gerador so LE a casca, nunca
echo     escreve nela.
echo.
echo   O QUE ELA NAO FAZ:
echo     nao muda o desenho do sistema. Sao os mesmos interruptores
echo     de sempre - ela so guarda quais mexeu, e a data.
echo.
echo   >> ELA SE DESFAZ SOZINHA. Na primeira RODADA-DIARIA de outro
echo      dia, o sistema repoe tudo e avisa na tela. Voce nao precisa
echo      lembrar de nada.
echo.
echo  ------------------------------------------------------------
python "%PY%" ligar "rodar o motor por fora, nas funcoes novas das posicoes compradas, enquanto o Luis mexe no design da tela"
echo.
pause
