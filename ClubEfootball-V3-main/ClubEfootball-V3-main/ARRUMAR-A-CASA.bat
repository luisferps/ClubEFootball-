@echo off
chcp 65001 > nul
title ARRUMAR A CASA - tira da raiz o que foi feito para usar uma vez
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
echo   ARRUMAR A CASA
echo  ============================================================
echo.
echo   Tira da raiz da v6 os 62 programas que foram feitos para
echo   usar uma vez: sondas, provas, consertos datados, versoes
echo   alternativas que perderam a disputa.
echo.
echo   NAO APAGA NADA. Move para a pasta _ARQUIVO-MORTO, que fica
echo   fora do GitHub. Se um dia precisar de algum, esta la.
echo.
echo   COMO EU ESCOLHI (medido, nao no olho):
echo     - parti dos .bat do ClubEfootball e do rodada_diaria
echo     - segui quem chama quem e quem importa quem
echo     - o que nao e alcancado por ninguem, sai
echo     - o que se repete (backup, vigia, coleta, fila) FICA
echo.
echo   NAO SAI DAQUI:
echo     - nada do ClubEfootball
echo     - os 29 atalhos (a ponte para os .bat velhos)
echo     - as 16 ferramentas que se repetem
echo     - config.txt, dados, saida_v6, encaixe, logs
echo.
echo  ------------------------------------------------------------
echo.
pause
if not exist "_ARQUIVO-MORTO" mkdir "_ARQUIVO-MORTO"
echo arquivado em %DATE% %TIME% > "_ARQUIVO-MORTO\QUANDO.txt"
echo.
if exist "achar_ficha.py" move /Y "achar_ficha.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "achar_ficha.py" (echo    movido: achar_ficha.py) else (echo    NAO MOVEU: achar_ficha.py)
if exist "adiar_os_sem_falta.py" move /Y "adiar_os_sem_falta.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "adiar_os_sem_falta.py" (echo    movido: adiar_os_sem_falta.py) else (echo    NAO MOVEU: adiar_os_sem_falta.py)
if exist "agregar_teste.py" move /Y "agregar_teste.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "agregar_teste.py" (echo    movido: agregar_teste.py) else (echo    NAO MOVEU: agregar_teste.py)
if exist "aplicar_tecnicos_novos.py" move /Y "aplicar_tecnicos_novos.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "aplicar_tecnicos_novos.py" (echo    movido: aplicar_tecnicos_novos.py) else (echo    NAO MOVEU: aplicar_tecnicos_novos.py)
if exist "baixar_ficha.py" move /Y "baixar_ficha.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "baixar_ficha.py" (echo    movido: baixar_ficha.py) else (echo    NAO MOVEU: baixar_ficha.py)
if exist "cadastrar_habilidades_novas.py" move /Y "cadastrar_habilidades_novas.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "cadastrar_habilidades_novas.py" (echo    movido: cadastrar_habilidades_novas.py) else (echo    NAO MOVEU: cadastrar_habilidades_novas.py)
if exist "cartas_base_pro_fim.py" move /Y "cartas_base_pro_fim.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "cartas_base_pro_fim.py" (echo    movido: cartas_base_pro_fim.py) else (echo    NAO MOVEU: cartas_base_pro_fim.py)
if exist "comparar_efootbase.py" move /Y "comparar_efootbase.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "comparar_efootbase.py" (echo    movido: comparar_efootbase.py) else (echo    NAO MOVEU: comparar_efootbase.py)
if exist "conferir_base.py" move /Y "conferir_base.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "conferir_base.py" (echo    movido: conferir_base.py) else (echo    NAO MOVEU: conferir_base.py)
if exist "conferir_impeto.py" move /Y "conferir_impeto.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "conferir_impeto.py" (echo    movido: conferir_impeto.py) else (echo    NAO MOVEU: conferir_impeto.py)
if exist "conferir_resultado.py" move /Y "conferir_resultado.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "conferir_resultado.py" (echo    movido: conferir_resultado.py) else (echo    NAO MOVEU: conferir_resultado.py)
if exist "consertar_bouaddi.py" move /Y "consertar_bouaddi.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "consertar_bouaddi.py" (echo    movido: consertar_bouaddi.py) else (echo    NAO MOVEU: consertar_bouaddi.py)
if exist "consertar_origem_falso_nove.py" move /Y "consertar_origem_falso_nove.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "consertar_origem_falso_nove.py" (echo    movido: consertar_origem_falso_nove.py) else (echo    NAO MOVEU: consertar_origem_falso_nove.py)
if exist "consertar_posicoes.py" move /Y "consertar_posicoes.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "consertar_posicoes.py" (echo    movido: consertar_posicoes.py) else (echo    NAO MOVEU: consertar_posicoes.py)
if exist "consertar_sl.py" move /Y "consertar_sl.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "consertar_sl.py" (echo    movido: consertar_sl.py) else (echo    NAO MOVEU: consertar_sl.py)
if exist "consertar_sl_base.py" move /Y "consertar_sl_base.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "consertar_sl_base.py" (echo    movido: consertar_sl_base.py) else (echo    NAO MOVEU: consertar_sl_base.py)
if exist "consertar_vagas_514.py" move /Y "consertar_vagas_514.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "consertar_vagas_514.py" (echo    movido: consertar_vagas_514.py) else (echo    NAO MOVEU: consertar_vagas_514.py)
if exist "corpo_para_cards.py" move /Y "corpo_para_cards.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "corpo_para_cards.py" (echo    movido: corpo_para_cards.py) else (echo    NAO MOVEU: corpo_para_cards.py)
if exist "corpo_para_supabase.py" move /Y "corpo_para_supabase.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "corpo_para_supabase.py" (echo    movido: corpo_para_supabase.py) else (echo    NAO MOVEU: corpo_para_supabase.py)
if exist "corrige_habilidade_faltando.py" move /Y "corrige_habilidade_faltando.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "corrige_habilidade_faltando.py" (echo    movido: corrige_habilidade_faltando.py) else (echo    NAO MOVEU: corrige_habilidade_faltando.py)
if exist "corrigir_cards.py" move /Y "corrigir_cards.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "corrigir_cards.py" (echo    movido: corrigir_cards.py) else (echo    NAO MOVEU: corrigir_cards.py)
if exist "cruzar_habilidades.py" move /Y "cruzar_habilidades.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "cruzar_habilidades.py" (echo    movido: cruzar_habilidades.py) else (echo    NAO MOVEU: cruzar_habilidades.py)
if exist "deriva_falta.py" move /Y "deriva_falta.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "deriva_falta.py" (echo    movido: deriva_falta.py) else (echo    NAO MOVEU: deriva_falta.py)
if exist "enviar.py" move /Y "enviar.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "enviar.py" (echo    movido: enviar.py) else (echo    NAO MOVEU: enviar.py)
if exist "gera_boxes.py" move /Y "gera_boxes.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "gera_boxes.py" (echo    movido: gera_boxes.py) else (echo    NAO MOVEU: gera_boxes.py)
if exist "impeto_tudo.py" move /Y "impeto_tudo.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "impeto_tudo.py" (echo    movido: impeto_tudo.py) else (echo    NAO MOVEU: impeto_tudo.py)
if exist "ligar_fonte_unica.py" move /Y "ligar_fonte_unica.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "ligar_fonte_unica.py" (echo    movido: ligar_fonte_unica.py) else (echo    NAO MOVEU: ligar_fonte_unica.py)
if exist "medir_margem.py" move /Y "medir_margem.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "medir_margem.py" (echo    movido: medir_margem.py) else (echo    NAO MOVEU: medir_margem.py)
if exist "medir_passe_do_zagueiro.py" move /Y "medir_passe_do_zagueiro.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "medir_passe_do_zagueiro.py" (echo    movido: medir_passe_do_zagueiro.py) else (echo    NAO MOVEU: medir_passe_do_zagueiro.py)
if exist "motor_FONTE_UNICA.py" move /Y "motor_FONTE_UNICA.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "motor_FONTE_UNICA.py" (echo    movido: motor_FONTE_UNICA.py) else (echo    NAO MOVEU: motor_FONTE_UNICA.py)
if exist "ordenar_fila_leve.py" move /Y "ordenar_fila_leve.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "ordenar_fila_leve.py" (echo    movido: ordenar_fila_leve.py) else (echo    NAO MOVEU: ordenar_fila_leve.py)
if exist "ordenar_por_custo_real.py" move /Y "ordenar_por_custo_real.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "ordenar_por_custo_real.py" (echo    movido: ordenar_por_custo_real.py) else (echo    NAO MOVEU: ordenar_por_custo_real.py)
if exist "os_melhores_primeiro.py" move /Y "os_melhores_primeiro.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "os_melhores_primeiro.py" (echo    movido: os_melhores_primeiro.py) else (echo    NAO MOVEU: os_melhores_primeiro.py)
if exist "posicoes_do_efscout.py" move /Y "posicoes_do_efscout.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "posicoes_do_efscout.py" (echo    movido: posicoes_do_efscout.py) else (echo    NAO MOVEU: posicoes_do_efscout.py)
if exist "preparar_efootbase.py" move /Y "preparar_efootbase.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "preparar_efootbase.py" (echo    movido: preparar_efootbase.py) else (echo    NAO MOVEU: preparar_efootbase.py)
if exist "prioriza_meu_time.py" move /Y "prioriza_meu_time.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "prioriza_meu_time.py" (echo    movido: prioriza_meu_time.py) else (echo    NAO MOVEU: prioriza_meu_time.py)
if exist "provar_corte11.py" move /Y "provar_corte11.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "provar_corte11.py" (echo    movido: provar_corte11.py) else (echo    NAO MOVEU: provar_corte11.py)
if exist "provar_fonte_unica.py" move /Y "provar_fonte_unica.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "provar_fonte_unica.py" (echo    movido: provar_fonte_unica.py) else (echo    NAO MOVEU: provar_fonte_unica.py)
if exist "refazer_bloqueios_1308.py" move /Y "refazer_bloqueios_1308.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "refazer_bloqueios_1308.py" (echo    movido: refazer_bloqueios_1308.py) else (echo    NAO MOVEU: refazer_bloqueios_1308.py)
if exist "refazer_o_impeto_novo.py" move /Y "refazer_o_impeto_novo.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "refazer_o_impeto_novo.py" (echo    movido: refazer_o_impeto_novo.py) else (echo    NAO MOVEU: refazer_o_impeto_novo.py)
if exist "refazer_potw.py" move /Y "refazer_potw.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "refazer_potw.py" (echo    movido: refazer_potw.py) else (echo    NAO MOVEU: refazer_potw.py)
if exist "refazer_prioridade.py" move /Y "refazer_prioridade.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "refazer_prioridade.py" (echo    movido: refazer_prioridade.py) else (echo    NAO MOVEU: refazer_prioridade.py)
if exist "revisar_fila.py" move /Y "revisar_fila.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "revisar_fila.py" (echo    movido: revisar_fila.py) else (echo    NAO MOVEU: revisar_fila.py)
if exist "roda_lote_v6_FONTE_UNICA.py" move /Y "roda_lote_v6_FONTE_UNICA.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "roda_lote_v6_FONTE_UNICA.py" (echo    movido: roda_lote_v6_FONTE_UNICA.py) else (echo    NAO MOVEU: roda_lote_v6_FONTE_UNICA.py)
if exist "separa_fila_adiada.py" move /Y "separa_fila_adiada.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "separa_fila_adiada.py" (echo    movido: separa_fila_adiada.py) else (echo    NAO MOVEU: separa_fila_adiada.py)
if exist "so_o_que_muda_a_conta.py" move /Y "so_o_que_muda_a_conta.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "so_o_que_muda_a_conta.py" (echo    movido: so_o_que_muda_a_conta.py) else (echo    NAO MOVEU: so_o_que_muda_a_conta.py)
if exist "sondar2_efootballdb.py" move /Y "sondar2_efootballdb.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "sondar2_efootballdb.py" (echo    movido: sondar2_efootballdb.py) else (echo    NAO MOVEU: sondar2_efootballdb.py)
if exist "sondar3_efootballdb.py" move /Y "sondar3_efootballdb.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "sondar3_efootballdb.py" (echo    movido: sondar3_efootballdb.py) else (echo    NAO MOVEU: sondar3_efootballdb.py)
if exist "sondar4_efootballdb.py" move /Y "sondar4_efootballdb.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "sondar4_efootballdb.py" (echo    movido: sondar4_efootballdb.py) else (echo    NAO MOVEU: sondar4_efootballdb.py)
if exist "sondar5_efootballdb.py" move /Y "sondar5_efootballdb.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "sondar5_efootballdb.py" (echo    movido: sondar5_efootballdb.py) else (echo    NAO MOVEU: sondar5_efootballdb.py)
if exist "sondar6_habilidades.py" move /Y "sondar6_habilidades.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "sondar6_habilidades.py" (echo    movido: sondar6_habilidades.py) else (echo    NAO MOVEU: sondar6_habilidades.py)
if exist "sondar_efootballdb.py" move /Y "sondar_efootballdb.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "sondar_efootballdb.py" (echo    movido: sondar_efootballdb.py) else (echo    NAO MOVEU: sondar_efootballdb.py)
if exist "subir_as_linhas_agora.py" move /Y "subir_as_linhas_agora.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "subir_as_linhas_agora.py" (echo    movido: subir_as_linhas_agora.py) else (echo    NAO MOVEU: subir_as_linhas_agora.py)
if exist "subir_efhub.py" move /Y "subir_efhub.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "subir_efhub.py" (echo    movido: subir_efhub.py) else (echo    NAO MOVEU: subir_efhub.py)
if exist "subir_o_que_faltava.py" move /Y "subir_o_que_faltava.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "subir_o_que_faltava.py" (echo    movido: subir_o_que_faltava.py) else (echo    NAO MOVEU: subir_o_que_faltava.py)
if exist "tirar_10_funcoes_das_linhas.py" move /Y "tirar_10_funcoes_das_linhas.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "tirar_10_funcoes_das_linhas.py" (echo    movido: tirar_10_funcoes_das_linhas.py) else (echo    NAO MOVEU: tirar_10_funcoes_das_linhas.py)
if exist "tirar_cmovel_das_linhas.py" move /Y "tirar_cmovel_das_linhas.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "tirar_cmovel_das_linhas.py" (echo    movido: tirar_cmovel_das_linhas.py) else (echo    NAO MOVEU: tirar_cmovel_das_linhas.py)
if exist "tirar_goleiro_das_linhas.py" move /Y "tirar_goleiro_das_linhas.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "tirar_goleiro_das_linhas.py" (echo    movido: tirar_goleiro_das_linhas.py) else (echo    NAO MOVEU: tirar_goleiro_das_linhas.py)
if exist "tirar_os_seis_da_frente.py" move /Y "tirar_os_seis_da_frente.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "tirar_os_seis_da_frente.py" (echo    movido: tirar_os_seis_da_frente.py) else (echo    NAO MOVEU: tirar_os_seis_da_frente.py)
if exist "vaga_pelo_efootballdb.py" move /Y "vaga_pelo_efootballdb.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "vaga_pelo_efootballdb.py" (echo    movido: vaga_pelo_efootballdb.py) else (echo    NAO MOVEU: vaga_pelo_efootballdb.py)
if exist "vaga_pelo_efscout.py" move /Y "vaga_pelo_efscout.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "vaga_pelo_efscout.py" (echo    movido: vaga_pelo_efscout.py) else (echo    NAO MOVEU: vaga_pelo_efscout.py)
if exist "zerar_rodada.py" move /Y "zerar_rodada.py" "_ARQUIVO-MORTO\" >nul 2>&1 & if not exist "zerar_rodada.py" (echo    movido: zerar_rodada.py) else (echo    NAO MOVEU: zerar_rodada.py)
echo.
echo  ============================================================
echo   PRONTO. O que saiu esta em _ARQUIVO-MORTO\
echo  ============================================================
echo.
pause
