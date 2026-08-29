@echo off
chcp 65001 > nul
title 1 - LIMPAR ANTES DE SUBIR PRO GITHUB
cd /d "%~dp0"
echo.
echo  ============================================================
echo   LIMPEZA - passo 1 de 2
echo  ============================================================
echo.
echo   Ele NAO APAGA nada. Ele MOVE para a pasta _LIXO.
echo   Se algo der errado, esta tudo la para voltar.
echo.
echo   Depois que o GitHub subir e o motor rodar na outra maquina,
echo   voce apaga a _LIXO na mao.
echo.
pause
echo.

if not exist "_LIXO" mkdir "_LIXO"
if not exist "_LIXO\raiz" mkdir "_LIXO\raiz"
if not exist "_LIXO\dados" mkdir "_LIXO\dados"
if not exist "_LIXO\v3" mkdir "_LIXO\v3"

echo  ---- a tela LEGADA (o LEIA-ME diz que sao copia da versao velha)
for %%F in (
  "elenco.js" "ficha-ajustes.js" "motor-e-ficha-base.js"
  "modulos-elenco-paginas.js" "paginas-e-navegacao.js"
  "dados-e-catalogos.js" "user-state-repository.js"
  "como-funciona.js" "como-funciona.css" "clubefut.css"
  "ClubEfootball-DATA-BOXES-CORRIGIDA-CARDS-LARGOS.html"
  "TELA-CLUBEFOOTBALL-UNICA.html"
) do (
  if exist %%F ( move /Y %%F "_LIXO\raiz\" > nul && echo    movido: %%F )
)

echo.
echo  ---- extrator velho da raiz (o bom esta em 7-VARREDURA-DO-JOGO)
if exist "Extrator-ClubEfootball.html" ( move /Y "Extrator-ClubEfootball.html" "_LIXO\raiz\" > nul && echo    movido: Extrator-ClubEfootball.html )

echo.
echo  ---- copias soltas do extrator
if exist "VER DADOS DO JOGO\Extrator-ClubEfootball.html" ( move /Y "VER DADOS DO JOGO\Extrator-ClubEfootball.html" "_LIXO\raiz\" > nul && echo    movido: VER DADOS DO JOGO\Extrator-ClubEfootball.html )
rem Bonificador oficial: 2-MOTORES\BONIFICADOR\motor_bonus.py (nao mover)
for %%F in ("coletor_efhub.js" "ids-para-coletar.js" "baixar-o-que-tem.js") do (
  if exist "VER DADOS DO JOGO\%%~F" ( move /Y "VER DADOS DO JOGO\%%~F" "_LIXO\raiz\" > nul && echo    movido: VER DADOS DO JOGO\%%~F )
)

echo.
echo  ---- arquivos de trabalho do motor (nao existem mais desde 27/08)
cd /d "%~dp0ClubEfootball-V3-main\ClubEfootball-V3-main" 2>nul
if errorlevel 1 goto FIM
for %%F in (
  "fila_v6.json" "fila_EXTRA.json" "fila_PRIORIDADE.json"
  "fila_ADIADA_pool_vazio.json" "fila_EXCLUIDOS.csv"
  "FONTE-UNICA.txt" "GRAVA-DIRETO.txt" "LIGAR-MOTOR-AUTOMATICO.txt"
  "tecnicos.json" "HAB_EFEITOS_FINAL.json" "CAT_dom.json"
  "habilidades_por_posicao.json" "impeto_conferido_no_jogo.json"
  "ids_sem_vaga_pela_data.json" "pe_ruim.json" "levelcap.json"
  "lancamento_agora.json" "feitos.txt" "NAO-SEI.txt"
) do (
  if exist %%F ( move /Y %%F "%~dp0_LIXO\v3\" > nul && echo    movido: %%~F )
)
for %%F in (
  "base_unica.json" "cards.json" "cards_efhub.json"
  "molde.json" "falta_por_card.json" "raras_por_card.json"
  "insumos_bonus.json" "levelcap.json"
) do (
  if exist "dados\%%~F" ( move /Y "dados\%%~F" "%~dp0_LIXO\dados\" > nul && echo    movido: dados\%%~F )
)
if exist "saida_v6" ( move /Y "saida_v6" "%~dp0_LIXO\" > nul && echo    movida a pasta: saida_v6 )
if exist "__pycache__" ( rmdir /S /Q "__pycache__" && echo    apagado: __pycache__ )
if exist "programas\__pycache__" ( rmdir /S /Q "programas\__pycache__" && echo    apagado: programas\__pycache__ )

:FIM
cd /d "%~dp0"
echo.
echo  ============================================================
echo   PRONTO. Tudo que saiu esta em _LIXO\
echo  ============================================================
echo.
echo   Confira que o sistema ainda abre. Se estiver tudo certo,
echo   rode o  2-SUBIR-PRO-GITHUB.bat
echo.
pause
