-- O read model publico carrega o degrau da propria linha para que consumidores
-- nao precisem abrir a tabela operacional larga a cada consulta.
alter table clube_novo.build_publicacao_linha_ativa_v1
  add column if not exists impeto_condicional_codigo integer,
  add column if not exists impeto_condicional_nivel smallint;

create or replace function clube_novo.sincronizar_publicacao_degrau_v1()
returns trigger
language plpgsql
security definer
set search_path to ''
as $function$
begin
  select l.impeto_condicional_codigo,l.impeto_condicional_nivel
    into new.impeto_condicional_codigo,new.impeto_condicional_nivel
  from clube_novo.build_linha_card l
  where l.id=new.linha_id;
  return new;
end
$function$;

drop trigger if exists build_publicacao_degrau_v1 on clube_novo.build_publicacao_linha_ativa_v1;
create trigger build_publicacao_degrau_v1
before insert or update of linha_id on clube_novo.build_publicacao_linha_ativa_v1
for each row execute function clube_novo.sincronizar_publicacao_degrau_v1();

create or replace function clube_novo.propagar_linha_degrau_publicacao_v1()
returns trigger
language plpgsql
security definer
set search_path to ''
as $function$
begin
  update clube_novo.build_publicacao_linha_ativa_v1 p
  set impeto_condicional_codigo=new.impeto_condicional_codigo,
      impeto_condicional_nivel=new.impeto_condicional_nivel
  where p.linha_id=new.id
    and (p.impeto_condicional_codigo is distinct from new.impeto_condicional_codigo
      or p.impeto_condicional_nivel is distinct from new.impeto_condicional_nivel);
  return new;
end
$function$;

drop trigger if exists build_linha_propagar_degrau_publicacao_v1 on clube_novo.build_linha_card;
create trigger build_linha_propagar_degrau_publicacao_v1
after update of impeto_condicional_codigo,impeto_condicional_nivel on clube_novo.build_linha_card
for each row execute function clube_novo.propagar_linha_degrau_publicacao_v1();

update clube_novo.build_publicacao_linha_ativa_v1 p
set impeto_condicional_codigo=l.impeto_condicional_codigo,
    impeto_condicional_nivel=l.impeto_condicional_nivel
from clube_novo.build_linha_card l
where l.id=p.linha_id
  and (p.impeto_condicional_codigo is distinct from l.impeto_condicional_codigo
    or p.impeto_condicional_nivel is distinct from l.impeto_condicional_nivel);

alter table clube_novo.build_publicacao_linha_ativa_v1
  drop constraint if exists build_publicacao_linha_ativa_degrau_v1_chk,
  add constraint build_publicacao_linha_ativa_degrau_v1_chk check (
    (impeto_condicional_codigo is null and impeto_condicional_nivel is null)
    or (impeto_condicional_codigo is not null and impeto_condicional_nivel between 1 and 3)
  );

comment on column clube_novo.build_publicacao_linha_ativa_v1.impeto_condicional_codigo
is 'Codigo condicional da linha publicado e sincronizado para leitura do site.';
comment on column clube_novo.build_publicacao_linha_ativa_v1.impeto_condicional_nivel
is 'Degrau condicional 1 a 3 publicado e sincronizado para leitura do site.';

revoke all on function clube_novo.sincronizar_publicacao_degrau_v1() from public,anon,authenticated;
revoke all on function clube_novo.propagar_linha_degrau_publicacao_v1() from public,anon,authenticated;
