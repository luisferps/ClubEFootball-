begin;
drop trigger if exists build_linha_teste_nao_publica_v1 on clube_novo.build_linha_card;
drop function if exists public.otimizador_bloquear_linha_teste_v1(bigint,uuid,text);
drop function if exists public.otimizador_concluir_linha_teste_v1(bigint,uuid,jsonb);
drop function if exists public.otimizador_iniciar_linha_teste_v1(bigint,uuid);
drop function if exists public.otimizador_fila_teste_v1(uuid);
drop function if exists public.otimizador_criar_amostra_teste_v1(uuid,text);
drop function if exists public.otimizador_status_teste_v1(uuid);
drop function if exists clube_novo.bloquear_publicacao_linha_teste_v1();
drop index if exists clube_novo.build_linha_teste_estado_v1_idx;
drop index if exists clube_novo.build_linha_teste_contexto_v1_uidx;
alter table clube_novo.build_linha_card
 drop constraint if exists build_linha_teste_campos_v1_check,
 drop column if exists otimizador_finalizado_em,
 drop column if exists otimizador_iniciado_em,
 drop column if exists erro_otimizador,
 drop column if exists estado_otimizador,
 drop column if exists sorteada_em,
 drop column if exists amostra_ordem,
 drop column if exists lote_teste_fingerprint,
 drop column if exists lote_teste_semente,
 drop column if exists lote_teste_id,
 drop column if exists execucao_tipo;
commit;
