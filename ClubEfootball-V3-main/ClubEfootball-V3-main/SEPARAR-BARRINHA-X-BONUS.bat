@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
title SEPARAR A BARRINHA DO BONUS - grava as listas
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "PY=%~dp0programas\separar_barrinha_de_bonus.py"
echo.
echo  ============================================================
echo   SEPARAR A BARRINHA DO BONUS
echo  ============================================================
echo.
echo   Sao DOIS motores, e eles nao leem as mesmas coisas:
echo.
echo     BARRINHAS  distribui os niveis, escolhe impeto, tecnico
echo                e habilidade. Le: base, orcamento, impeto
echo                nativo, vaga, habilidade de fabrica, rara,
echo                e o espaco de habilidades.
echo.
echo     BONUS      corpo, estilo de jogo da IA, pe ruim. Entra
echo                na nota por cima, SEM mexer na build.
echo.
echo   Mudou o impeto ou a habilidade nativa? roda a barrinha.
echo   Mudou so estilo de IA, corpo ou pe ruim? e so bonus.
echo   Mudou so a data ou o nome da campanha? nao roda nada.
echo.
echo   Ele NAO escreve a lista dos campos a mao: abre os dois
echo   motores e pergunta a eles. Se a leitura falhar, ele PARA.
echo.
echo  ------------------------------------------------------------
echo   ATENCAO: este GRAVA. Ele escreve o REFAZER-A-BARRINHA.txt
echo   e o SO-O-BONUS.txt, e enxuga o PRECISA-REFAZER.txt
echo   (o original fica em PRECISA-REFAZER.txt.ANTES-DA-SEPARACAO).
echo.
echo   Rode o CONFERIR antes, se ainda nao rodou.
echo.
pause
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
