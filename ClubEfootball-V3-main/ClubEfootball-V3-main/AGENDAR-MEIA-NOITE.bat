@echo off
chcp 65001 >nul
cd /d "%~dp0"
title AGENDAR A RODADA DIARIA - meia-noite
echo.
echo  ============================================================
echo   AGENDAR A RODADA DIARIA
echo  ============================================================
echo.
echo   Cria a tarefa do Windows que chama a RODADA-DIARIA.bat
echo   todo dia a meia-noite.
echo.
echo   A rodada faz, sozinha e nesta ordem:
echo      0. o vigia colhe box nova no efHub
echo      1-4. coleta efScout, impetos, vagas, box e datas
echo      5. unifica a base, sobe e desce do banco
echo      6. carta nova entra e vai pra FRENTE da fila
echo      7. o motor otimiza, e o motor de bonus calcula
echo      8. o encaixe e regerado e as linhas sobem pro banco
echo      9. o painel de acompanhamento
echo.
echo   ⛔ PRECISA SER ADMINISTRADOR. Se der erro de permissao,
echo      feche e clique com o botao DIREITO neste arquivo,
echo      "Executar como administrador".
echo.
echo   ⚠️ A tarefa roda so com o usuario CONECTADO — o vigia abre
echo      o Chrome, e Chrome nao sobe sem sessao de usuario.
echo.
pause
schtasks /Create /TN "TrueFootball - Rodada Diaria" /TR "\"%~dp0RODADA-DIARIA.bat\"" /SC DAILY /ST 00:00 /RL HIGHEST /F
if errorlevel 1 goto :erro
schtasks /Change /TN "TrueFootball - Rodada Diaria" /ENABLE >nul 2>&1
echo.
echo  ============================================================
echo    PRONTO. A rodada esta agendada para toda meia-noite.
echo  ============================================================
echo.
echo    Para conferir: abra o Agendador de Tarefas do Windows e
echo    procure "TrueFootball - Rodada Diaria".
echo.
echo    Para rodar agora sem esperar: dois cliques na RODADA-DIARIA.bat
echo.
pause
exit /b 0
:erro
echo.
echo   ^>^> NAO CONSEGUI AGENDAR. Quase sempre e permissao.
echo      Feche esta janela, clique com o botao DIREITO neste
echo      arquivo e escolha "Executar como administrador".
echo.
pause
exit /b 1
