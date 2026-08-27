@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title A TRANSFORMACAO - ClubEfootball
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
set "V7=%~dp0programas\"

cls
echo.
echo  ================================================================
echo    A TRANSFORMACAO   -   ClubEfootball
echo  ================================================================
echo.
echo    Faz tudo na ordem, e PARA na hora se alguma conferencia
echo    nao fechar. Nada e apagado, nenhuma pontuacao e alterada,
echo    nenhuma chave e trocada.
echo.
echo      0. backup do banco    (e so continua se as contagens baterem)
echo      1. o tradutor          - como cada fonte chama cada coisa
echo      2. as versoes          - o molde inteiro e a identidade dos motores
echo      3. os quatro estados   - zero deixa de ser "nao sei"
echo.
echo    Isto NAO inclui a troca da chave das tres tabelas.
echo    Aquilo se faz com voce acordado, olhando. De proposito.
echo.
echo  ----------------------------------------------------------------
echo.
pause

rem =================================================================
echo.
echo  ================================================================
echo    PASSO 0 de 3  -  BACKUP DO BANCO
echo  ================================================================
python backup_do_banco.py < nul
if errorlevel 1 goto :parou_backup
echo.
echo    ^>^> Backup feito. Confira acima se TODAS deram SIM.
echo       Se alguma nao fechou, feche esta janela agora.
echo.
pause

rem =================================================================
echo.
echo  ================================================================
echo    PASSO 1 de 3  -  O TRADUTOR
echo  ================================================================
python "%V7%subir_tradutor.py"
if errorlevel 1 goto :parou1

rem =================================================================
echo.
echo  ================================================================
echo    PASSO 2 de 3  -  AS VERSOES DO MOLDE E DOS MOTORES
echo  ================================================================
python "%V7%subir_versoes.py"
if errorlevel 1 goto :parou2

rem =================================================================
echo.
echo  ================================================================
echo    PASSO 3 de 3  -  OS QUATRO ESTADOS
echo  ================================================================
python "%V7%estados.py"
if errorlevel 1 goto :parou3

rem =================================================================
echo.
echo  ================================================================
echo    ACABOU. Os tres passos fecharam.
echo  ================================================================
echo.
echo    O que mudou no banco:
echo      - a tabela de traducao, cheia
echo      - as 19 funcoes com codigo fixo e rotulo
echo      - o molde 5 inteiro (494 itens, 19 funcoes)
echo      - a identidade dos dois motores, com impressao digital
echo      - o estado de cada campo de cada carta
echo.
echo    O que NAO mudou: nenhuma pontuacao, nenhuma chave, nada apagado.
echo.
echo    Para conferir antes de uma rodada, quando quiser:
echo       SUBIR-VERSOES.bat conferir
echo.
pause
exit /b 0

:parou_backup
echo.
echo  ================================================================
echo    PAROU NO BACKUP. Nada foi feito no banco.
echo  ================================================================
echo    Sem backup conferido, nao se mexe em nada. Regra sua, 16/08.
echo.
pause
exit /b 1

:parou1
echo.
echo  ================================================================
echo    PAROU NO PASSO 1 (o tradutor). Os passos 2 e 3 NAO rodaram.
echo  ================================================================
echo    Leia o motivo acima. Se reclamou de tabela ou coluna que nao
echo    existe, abra antes o  1-COLAR-NO-SUPABASE.html
echo.
pause
exit /b 1

:parou2
echo.
echo  ================================================================
echo    PAROU NO PASSO 2 (as versoes). O passo 3 NAO rodou.
echo  ================================================================
echo    O passo 1 ja entrou e esta valendo - nao precisa desfazer.
echo.
pause
exit /b 1

:parou3
echo.
echo  ================================================================
echo    PAROU NO PASSO 3 (os estados).
echo  ================================================================
echo    Os passos 1 e 2 ja entraram e estao valendo.
echo.
pause
exit /b 1
