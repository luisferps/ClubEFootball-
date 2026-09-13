create or replace function clube_novo.tg_invalidar_conferencia_bonificador_v1()
returns trigger language plpgsql security definer set search_path='' as $$
begin
 if tg_nargs=1 and tg_argv[0]='regra' then
   perform pg_advisory_xact_lock(hashtextextended('bonificador-conferencia-regra',0));
   delete from clube_novo.bonificador_conferencia_vigente_v1;
 elsif tg_nargs=1 and tg_argv[0]='resultado' then
   delete from clube_novo.bonificador_conferencia_vigente_v1 where bonus_id=old.id;
 else
   if tg_op='UPDATE' and to_jsonb(new) is not distinct from to_jsonb(old) then return null; end if;
   perform pg_advisory_xact_lock(hashtextextended('bonificador-conferencia-card:'||(case when tg_op='DELETE' then to_jsonb(old)->>'card_id' else to_jsonb(new)->>'card_id' end),0));
   delete from clube_novo.bonificador_conferencia_vigente_v1
   where card_id=case when tg_op='DELETE' then to_jsonb(old)->>'card_id' else to_jsonb(new)->>'card_id' end;
   if tg_op='UPDATE' and to_jsonb(new)->>'card_id' is distinct from to_jsonb(old)->>'card_id' then
     delete from clube_novo.bonificador_conferencia_vigente_v1 where card_id=to_jsonb(old)->>'card_id';
   end if;
 end if;
 return null;
end $$;

