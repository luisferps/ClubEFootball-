begin;
do $do$ declare v_job bigint; begin
  select jobid into v_job from cron.job where jobname='finalizacao_publica_por_linha_v1' limit 1;
  if v_job is not null then perform cron.unschedule(v_job); end if;
end $do$;
drop trigger if exists build_linha_finalizar_automatico_v1 on clube_novo.build_linha_card;
drop trigger if exists bonificador_correcao_inserir_finalizar_automatico_v1 on clube_novo.bonificador_correcao_item_v1;
drop trigger if exists bonificador_correcao_atualizar_finalizar_automatico_v1 on clube_novo.bonificador_correcao_item_v1;
drop trigger if exists otimizador_vals_finalizar_automatico_v1 on clube_novo.build_otimizador;
drop function if exists public.finalizacao_publica_tick_v1(integer);
drop function if exists clube_novo.disparar_finalizacao_linha_v1();
drop function if exists clube_novo.disparar_finalizacao_correcao_v1();
drop function if exists clube_novo.disparar_finalizacao_otimizador_vals_v1();
revoke all on function clube_novo.finalizar_publicar_linha_v1(bigint,text)
  from public,anon,authenticated,service_role,bonificador_runtime;
update clube_novo.build_finalizacao_fila_v1
set estado='erro',motivo='manutencao fail-closed: automacao desativada',
  proxima_tentativa_em='infinity'::timestamptz,atualizado_em=clock_timestamp()
where estado in ('aguardando','processando');
notify pgrst,'reload schema';
commit;

-- Reversao segura: preserva publicacoes e auditoria, mas desliga novos disparos.
-- A rota global/manual eliminada nao e recriada. Retomar exige uma migracao
-- corretiva nova e explicita, nunca restauracao do caminho removido.
