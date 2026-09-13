create table if not exists clube_novo.bonificador_conferencia_vigente_v1(
 linha_id bigint primary key references clube_novo.build_linha_card(id) on delete cascade,
 card_id text not null,funcao_id bigint not null,posicao_id integer not null,
 bonus_id bigint not null references clube_novo.build_bonificador(id),
 entrada_fingerprint text not null,resultado_fingerprint text not null,
 regra_fingerprint text not null,conforme boolean not null,conferido_em timestamptz not null default now());
create index if not exists bonificador_conferencia_bonus_idx on clube_novo.bonificador_conferencia_vigente_v1(bonus_id);
create index if not exists bonificador_conferencia_card_idx on clube_novo.bonificador_conferencia_vigente_v1(card_id);
alter table clube_novo.bonificador_conferencia_vigente_v1 enable row level security;
revoke all on clube_novo.bonificador_conferencia_vigente_v1 from public,anon,authenticated;
create or replace function clube_novo.bonificador_conferencia_regra_fingerprint_v1()
returns text language sql stable security invoker set search_path='' as $$
 select encode(extensions.digest(concat(
 pg_get_functiondef('clube_novo.bonificador_componentes_vigentes_v1(text,bigint,integer)'::regprocedure),
 pg_get_functiondef('clube_novo.bonificador_resultado_conforme_componentes_v1(jsonb,jsonb)'::regprocedure),
 pg_get_functiondef('clube_novo.separar_altura_v1(jsonb,bigint,boolean)'::regprocedure),
 pg_get_functiondef('clube_novo.carta_estilos_efetivos_v12(text)'::regprocedure),
 pg_get_functiondef('clube_novo.conferir_bonus_estilo_0909_v1(bigint,integer,integer,integer)'::regprocedure),
 pg_get_functiondef('build_editor.faixa_corpo_v1(numeric,numeric,numeric,numeric,numeric)'::regprocedure)
 ),'sha256'),'hex');
$$;
create or replace function clube_novo.tg_invalidar_conferencia_bonificador_v1()
returns trigger language plpgsql security definer set search_path='' as $$
begin
 if tg_nargs=1 and tg_argv[0]='regra' then
   delete from clube_novo.bonificador_conferencia_vigente_v1;
 elsif tg_nargs=1 and tg_argv[0]='resultado' then
   delete from clube_novo.bonificador_conferencia_vigente_v1 where bonus_id=old.id;
 else
   if tg_op='UPDATE' and to_jsonb(new) is not distinct from to_jsonb(old) then return null; end if;
   delete from clube_novo.bonificador_conferencia_vigente_v1
   where card_id=case when tg_op='DELETE' then to_jsonb(old)->>'card_id' else to_jsonb(new)->>'card_id' end;
   if tg_op='UPDATE' and to_jsonb(new)->>'card_id' is distinct from to_jsonb(old)->>'card_id' then
     delete from clube_novo.bonificador_conferencia_vigente_v1 where card_id=to_jsonb(old)->>'card_id';
   end if;
 end if;
 return null;
end $$;
create trigger invalidar_conferencia_bonus_resultado after update or delete on clube_novo.build_bonificador for each row execute function clube_novo.tg_invalidar_conferencia_bonificador_v1('resultado');
do $$ declare t text; begin
 foreach t in array array['carta_jogo','carta_corpo_jogo','carta_pe_jogo','carta_estilo_ia_jogo','carta_playstyle_jogo','carta_posicao_principal_jogo'] loop
 execute format('create trigger invalidar_conferencia_bonus after insert or update or delete on clube_novo.%I for each row execute function clube_novo.tg_invalidar_conferencia_bonificador_v1()',t);
 end loop;
 foreach t in array array['bonificador_parametro','bonificador_altura_politica_v1','bonificador_politica_estilo','bonificador_regra_playstyle','corpo_ordem','playstyle','pe','posicao_jogo','estilo_ia'] loop
 execute format('create trigger invalidar_conferencia_bonus_regra after insert or update or delete or truncate on clube_novo.%I for each statement execute function clube_novo.tg_invalidar_conferencia_bonificador_v1(''regra'')',t);
 end loop;
end $$;
revoke all on function clube_novo.bonificador_conferencia_regra_fingerprint_v1(),clube_novo.tg_invalidar_conferencia_bonificador_v1() from public,anon,authenticated;
