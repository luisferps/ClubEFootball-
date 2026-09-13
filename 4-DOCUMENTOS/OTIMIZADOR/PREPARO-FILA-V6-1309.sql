create or replace procedure clube_novo.preparo_v6_1309_tick()
language plpgsql as $proc$
declare ini timestamptz:=clock_timestamp(); v_estado text; v_antes integer; v_depois integer;
begin
 loop
  select estado,preparo_concluido into v_estado,v_antes from clube_novo.otimizador_lote_producao_v3 where id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
  if v_estado is distinct from 'preparando' then perform cron.unschedule('preparo-v6-1309'); return; end if;
  exit when clock_timestamp()-ini>interval '75 seconds';
  perform public.otimizador_producao_preparar_fatia_v5('39da8ff4-7a4a-4ec7-8641-e81b5677ad4c',20);
  select preparo_concluido into v_depois from clube_novo.otimizador_lote_producao_v3 where id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c';
  commit;
  exit when v_depois=v_antes;
 end loop;
end $proc$;
revoke all on procedure clube_novo.preparo_v6_1309_tick() from public;

-- Job específico; encerra o agendamento quando o preparo termina ou falha.
select cron.schedule('preparo-v6-1309','* * * * *','call clube_novo.preparo_v6_1309_tick()');
