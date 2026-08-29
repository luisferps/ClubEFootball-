-- Rollback seguro da cópia paralela.
-- Remove SOMENTE o schema/tabelas clonados; clube permanece intacto.
-- Execute apenas se for necessário desfazer a cópia.

begin;
set transaction isolation level repeatable read;
set local lock_timeout = '5s';
set local statement_timeout = '60s';

create temporary table _clube_novo_manifesto (
  nome text primary key
) on commit drop;

insert into _clube_novo_manifesto (nome) values
  ('texto_do_jogo'),('atributo_jogo'),('corpo_ordem'),('pe'),
  ('posicao_jogo'),('playstyle'),('estilo_ia'),('habilidade_jogo'),
  ('impeto_jogo'),('tecnico_jogo'),('carta_jogo'),
  ('carta_atributo_jogo'),('carta_corpo_jogo'),
  ('carta_habilidade_jogo'),('carta_estilo_ia_jogo'),
  ('carta_posicao_jogo'),('carta_impeto_jogo'),
  ('impeto_atributo_jogo'),('funcao_sistema'),('funcao_alias'),
  ('mapa_do_jogo');

do $preflight$
declare
  v_faltantes text[];
begin
  if to_regnamespace('clube_novo') is null then
    raise exception 'Rollback abortado: schema clube_novo não existe';
  end if;

  if (
    select array_agg(c.relname::text order by c.relname)
      from pg_class c join pg_namespace n on n.oid=c.relnamespace
     where n.nspname='clube_novo' and c.relkind in ('r','p')
  ) is distinct from (
    select array_agg(nome order by nome) from _clube_novo_manifesto
  ) then
    raise exception 'Rollback abortado: clube_novo não contém exatamente as 21 tabelas esperadas';
  end if;

  select array_agg(m.nome order by m.nome)
    into v_faltantes
    from _clube_novo_manifesto m
   where to_regclass(format('clube.%I',m.nome)) is null;
  if v_faltantes is not null then
    raise exception 'Rollback abortado: fontes em clube estão ausentes: %', v_faltantes;
  end if;

  -- Nova FK cruzando a fronteira indica que algum consumidor já foi conectado.
  if exists (
    select 1
      from pg_constraint con
      join pg_class o on o.oid=con.conrelid join pg_namespace ons on ons.oid=o.relnamespace
      join pg_class d on d.oid=con.confrelid join pg_namespace dns on dns.oid=d.relnamespace
     where con.contype='f'
       and (ons.nspname='clube_novo' or dns.nspname='clube_novo')
       and (ons.nspname<>'clube_novo' or dns.nspname<>'clube_novo')
  ) then
    raise exception 'Rollback abortado: existe FK externa conectada a clube_novo';
  end if;

  -- Rotina textual apontando ao novo schema também representa consumidor novo.
  if exists (
    select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
     where p.prokind in ('f','p')
       and n.nspname not in ('pg_catalog','information_schema')
       and n.nspname not like 'pg_toast%'
       and pg_get_functiondef(p.oid) ~
         'clube_novo\.(texto_do_jogo|atributo_jogo|corpo_ordem|pe|posicao_jogo|playstyle|estilo_ia|habilidade_jogo|impeto_jogo|tecnico_jogo|carta_jogo|carta_atributo_jogo|carta_corpo_jogo|carta_habilidade_jogo|carta_estilo_ia_jogo|carta_posicao_jogo|carta_impeto_jogo|impeto_atributo_jogo|funcao_sistema|funcao_alias|mapa_do_jogo)([^[:alnum:]_]|$)'
  ) then
    raise exception 'Rollback abortado: rotina já aponta para clube_novo';
  end if;

  -- Views externas com dependência por OID devem impedir o descarte.
  if exists (
    select 1
      from pg_depend dep
      join pg_rewrite rw on rw.oid=dep.objid and dep.classid='pg_rewrite'::regclass
      join pg_class v on v.oid=rw.ev_class
      join pg_namespace vn on vn.oid=v.relnamespace
      join pg_class t on t.oid=dep.refobjid
      join pg_namespace tn on tn.oid=t.relnamespace
     where tn.nspname='clube_novo'
       and t.relname in (select nome from _clube_novo_manifesto)
       and vn.nspname<>'clube_novo'
  ) then
    raise exception 'Rollback abortado: view externa depende de clube_novo';
  end if;
end
$preflight$;

do $locks$
declare
  v_nome text;
begin
  for v_nome in select nome from _clube_novo_manifesto order by nome loop
    execute format('lock table clube_novo.%I in access exclusive mode nowait',v_nome);
  end loop;
end
$locks$;

-- Uma única lista permite remover as dependências internas entre as 21 tabelas.
drop table
  clube_novo.texto_do_jogo,
  clube_novo.atributo_jogo,
  clube_novo.corpo_ordem,
  clube_novo.pe,
  clube_novo.posicao_jogo,
  clube_novo.playstyle,
  clube_novo.estilo_ia,
  clube_novo.habilidade_jogo,
  clube_novo.impeto_jogo,
  clube_novo.tecnico_jogo,
  clube_novo.carta_jogo,
  clube_novo.carta_atributo_jogo,
  clube_novo.carta_corpo_jogo,
  clube_novo.carta_habilidade_jogo,
  clube_novo.carta_estilo_ia_jogo,
  clube_novo.carta_posicao_jogo,
  clube_novo.carta_impeto_jogo,
  clube_novo.impeto_atributo_jogo,
  clube_novo.funcao_sistema,
  clube_novo.funcao_alias,
  clube_novo.mapa_do_jogo
restrict;

-- RESTRICT confirma que nenhum objeto inesperado foi criado no schema.
drop schema clube_novo restrict;

do $postflight$
begin
  if to_regnamespace('clube_novo') is not null then
    raise exception 'Rollback abortado: schema clube_novo permaneceu';
  end if;
  if exists (
    select 1 from _clube_novo_manifesto m
     where to_regclass(format('clube.%I',m.nome)) is null
  ) then
    raise exception 'Rollback abortado: uma fonte em clube desapareceu';
  end if;
end
$postflight$;

commit;
