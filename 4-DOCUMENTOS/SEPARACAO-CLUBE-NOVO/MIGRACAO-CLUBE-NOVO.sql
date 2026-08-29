-- Cópia paralela e fail-closed do modelo novo do ClubEFootball.
-- Cria clube_novo com exatamente 21 tabelas copiadas de clube.
-- NÃO move, renomeia, apaga ou altera nenhuma tabela/linha de clube.
-- Projeto auditado: trqqpsnafpbudtvvicch (PostgreSQL 17).

begin;
set transaction isolation level repeatable read;
set local lock_timeout = '5s';
set local statement_timeout = '120s';

create temporary table _clube_novo_manifesto (
  nome text primary key
) on commit drop;

insert into _clube_novo_manifesto (nome) values
  ('texto_do_jogo'),
  ('atributo_jogo'),
  ('corpo_ordem'),
  ('pe'),
  ('posicao_jogo'),
  ('playstyle'),
  ('estilo_ia'),
  ('habilidade_jogo'),
  ('impeto_jogo'),
  ('tecnico_jogo'),
  ('carta_jogo'),
  ('carta_atributo_jogo'),
  ('carta_corpo_jogo'),
  ('carta_habilidade_jogo'),
  ('carta_estilo_ia_jogo'),
  ('carta_posicao_jogo'),
  ('carta_impeto_jogo'),
  ('impeto_atributo_jogo'),
  ('funcao_sistema'),
  ('funcao_alias'),
  ('mapa_do_jogo');

do $preflight$
declare
  v_problemas text[];
begin
  if (select count(*) from _clube_novo_manifesto) <> 21 then
    raise exception 'Cópia abortada: manifesto deve conter exatamente 21 tabelas';
  end if;

  if to_regnamespace('clube_novo') is not null then
    raise exception 'Cópia abortada: schema clube_novo já existe';
  end if;

  select array_agg(m.nome order by m.nome)
    into v_problemas
    from _clube_novo_manifesto m
   where not exists (
     select 1
       from pg_class c
       join pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'clube'
        and c.relname = m.nome
        and c.relkind = 'r'
        and not c.relispartition
   );
  if v_problemas is not null then
    raise exception 'Cópia abortada: fontes ausentes, não ordinárias ou particionadas: %', v_problemas;
  end if;

  if exists (
    select 1
      from pg_class c
      join pg_namespace n on n.oid = c.relnamespace
      join _clube_novo_manifesto m on m.nome = c.relname
     where n.nspname = 'clube'
       and c.relowner <> (select oid from pg_roles where rolname = current_user)
  ) then
    raise exception 'Cópia abortada: current_user não é proprietário de todas as fontes';
  end if;

  if exists (
    select 1
      from pg_inherits i
      join pg_class c on c.oid in (i.inhrelid, i.inhparent)
      join pg_namespace n on n.oid = c.relnamespace
      join _clube_novo_manifesto m on m.nome = c.relname
     where n.nspname = 'clube'
  ) then
    raise exception 'Cópia abortada: há herança/particionamento envolvendo o manifesto';
  end if;

  -- Toda FK que toca o conjunto deve ter as duas pontas dentro das 21 tabelas.
  if exists (
    select 1
      from pg_constraint con
      join pg_class origem on origem.oid = con.conrelid
      join pg_namespace origem_ns on origem_ns.oid = origem.relnamespace
      join pg_class destino on destino.oid = con.confrelid
      join pg_namespace destino_ns on destino_ns.oid = destino.relnamespace
     where con.contype = 'f'
       and (
         (origem_ns.nspname = 'clube' and origem.relname in (select nome from _clube_novo_manifesto))
         <>
         (destino_ns.nspname = 'clube' and destino.relname in (select nome from _clube_novo_manifesto))
       )
  ) then
    raise exception 'Cópia abortada: existe FK cruzando a fronteira do manifesto';
  end if;

  -- LIKE copiaria literalmente defaults nextval externos. Identidades são tratadas abaixo.
  if exists (
    select 1
      from pg_attribute a
      join pg_class c on c.oid = a.attrelid
      join pg_namespace n on n.oid = c.relnamespace
      join _clube_novo_manifesto m on m.nome = c.relname
      join pg_attrdef d on d.adrelid = a.attrelid and d.adnum = a.attnum
     where n.nspname = 'clube'
       and a.attidentity = ''
       and pg_get_expr(d.adbin, d.adrelid) ~ 'nextval'
  ) then
    raise exception 'Cópia abortada: default nextval não-identity exige decisão explícita';
  end if;
end
$preflight$;

-- Bloqueia escrita nas fontes durante a fotografia/carga; leituras do motor continuam.
do $locks$
declare
  v_nome text;
begin
  for v_nome in select nome from _clube_novo_manifesto order by nome loop
    execute format('lock table clube.%I in share mode nowait', v_nome);
  end loop;
end
$locks$;

create temporary table _clube_novo_pre (
  nome text primary key,
  oid_fonte oid not null,
  linhas bigint not null,
  fingerprint text not null,
  relrowsecurity boolean not null,
  relforcerowsecurity boolean not null,
  relreplident "char" not null,
  relacl text
) on commit drop;

do $fotografia$
declare
  v_nome text;
  v_oid oid;
  v_linhas bigint;
  v_fingerprint text;
  v_rls boolean;
  v_force boolean;
  v_replident "char";
  v_acl text;
begin
  for v_nome in select nome from _clube_novo_manifesto order by nome loop
    select c.oid, c.relrowsecurity, c.relforcerowsecurity, c.relreplident, c.relacl::text
      into v_oid, v_rls, v_force, v_replident, v_acl
      from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'clube' and c.relname = v_nome;

    execute format(
      'select count(*)::bigint, md5(coalesce(string_agg(md5(to_jsonb(t)::text), '''' order by md5(to_jsonb(t)::text)), '''')) from clube.%I t',
      v_nome
    ) into v_linhas, v_fingerprint;

    insert into _clube_novo_pre values
      (v_nome, v_oid, v_linhas, v_fingerprint, v_rls, v_force, v_replident, v_acl);
  end loop;
end
$fotografia$;

create schema clube_novo authorization postgres;

-- INCLUDING ALL copia colunas, tipos, defaults, identidades, generated columns,
-- NOT NULL, checks, PKs/uniques/exclusions, índices, comentários e opções físicas.
-- FKs, políticas RLS e gatilhos são recriados depois da carga.
do $criar_tabelas$
declare
  v_nome text;
begin
  for v_nome in select nome from _clube_novo_manifesto order by nome loop
    execute format(
      'create table clube_novo.%I (like clube.%I including all)',
      v_nome, v_nome
    );
  end loop;
end
$criar_tabelas$;

-- LIKE preserva a semântica de PK/UNIQUE/check/exclusion, mas pode recalcular
-- nomes. Reaplica os nomes canônicos quando existe uma correspondência
-- semântica única; qualquer ambiguidade aborta antes da carga.
do $normalizar_nomes_constraints$
declare
  r record;
  v_nome_atual text;
  v_correspondencias integer;
begin
  for r in
    select sc.relname as tabela, s.conname, s.contype,
           pg_get_constraintdef(s.oid,true) as definicao
      from pg_constraint s
      join pg_class sc on sc.oid=s.conrelid
      join pg_namespace sn on sn.oid=sc.relnamespace
      join _clube_novo_manifesto m on m.nome=sc.relname
     where sn.nspname='clube' and s.contype<>'f'
     order by sc.relname,s.conname
  loop
    if exists (
      select 1 from pg_constraint d
      join pg_class dc on dc.oid=d.conrelid
      where dc.relnamespace=to_regnamespace('clube_novo')
        and dc.relname=r.tabela and d.conname=r.conname
    ) then
      continue;
    end if;

    select count(*),min(d.conname)
      into v_correspondencias,v_nome_atual
      from pg_constraint d
      join pg_class dc on dc.oid=d.conrelid
     where dc.relnamespace=to_regnamespace('clube_novo')
       and dc.relname=r.tabela
       and d.contype=r.contype
       and pg_get_constraintdef(d.oid,true)=r.definicao;

    if v_correspondencias<>1 then
      raise exception 'Cópia abortada: constraint %.% tem % correspondências semânticas na cópia',
        r.tabela,r.conname,v_correspondencias;
    end if;
    execute format('alter table clube_novo.%I rename constraint %I to %I',
                   r.tabela,v_nome_atual,r.conname);
  end loop;
end
$normalizar_nomes_constraints$;

-- LIKE também pode recalcular nomes de índices não ligados a constraints.
-- Só renomeia quando todos os demais campos semânticos têm correspondência única.
do $normalizar_nomes_indices$
declare
  r record;
  v_nome_atual text;
  v_correspondencias integer;
begin
  for r in
    select t.relname tabela,x.relname indice,am.amname,
           i.indisunique,i.indisprimary,i.indisexclusion,i.indimmediate,
           i.indisvalid,i.indisready,i.indislive,i.indisclustered,i.indisreplident,
           i.indnullsnotdistinct,
           array(select pg_get_indexdef(i.indexrelid,k,true)
                   from generate_series(1,i.indnatts) k order by k) itens,
           regexp_replace(coalesce(pg_get_expr(i.indpred,i.indrelid,true),''),'\s+',' ','g') predicado,
           coalesce(x.reloptions::text,'') opcoes
      from pg_index i join pg_class t on t.oid=i.indrelid
      join pg_namespace n on n.oid=t.relnamespace
      join pg_class x on x.oid=i.indexrelid join pg_am am on am.oid=x.relam
      join _clube_novo_manifesto m on m.nome=t.relname
     where n.nspname='clube'
     order by t.relname,x.relname
  loop
    if exists (
      select 1 from pg_class x
       where x.relnamespace=to_regnamespace('clube_novo')
         and x.relkind='i' and x.relname=r.indice
    ) then
      continue;
    end if;

    select count(*),min(x.relname)
      into v_correspondencias,v_nome_atual
      from pg_index i join pg_class t on t.oid=i.indrelid
      join pg_class x on x.oid=i.indexrelid join pg_am am on am.oid=x.relam
     where t.relnamespace=to_regnamespace('clube_novo')
       and t.relname=r.tabela
       and am.amname=r.amname
       and row(i.indisunique,i.indisprimary,i.indisexclusion,i.indimmediate,
               i.indisvalid,i.indisready,i.indislive,i.indisclustered,i.indisreplident,
               i.indnullsnotdistinct)
           is not distinct from
           row(r.indisunique,r.indisprimary,r.indisexclusion,r.indimmediate,
               r.indisvalid,r.indisready,r.indislive,r.indisclustered,r.indisreplident,
               r.indnullsnotdistinct)
       and array(select pg_get_indexdef(i.indexrelid,k,true)
                   from generate_series(1,i.indnatts) k order by k)=r.itens
       and regexp_replace(coalesce(pg_get_expr(i.indpred,i.indrelid,true),''),'\s+',' ','g')=r.predicado
       and coalesce(x.reloptions::text,'')=r.opcoes;

    if v_correspondencias<>1 then
      raise exception 'Cópia abortada: índice %.% tem % correspondências semânticas na cópia',
        r.tabela,r.indice,v_correspondencias;
    end if;
    execute format('alter index clube_novo.%I rename to %I',v_nome_atual,r.indice);
  end loop;
end
$normalizar_nomes_indices$;

-- Colunas generated são recalculadas; ids identity são preservados explicitamente.
-- Nenhum gatilho de usuário existe ainda na cópia, portanto a carga não produz efeitos externos.
do $copiar_dados$
declare
  v_nome text;
  v_colunas text;
begin
  for v_nome in select nome from _clube_novo_manifesto order by nome loop
    select string_agg(format('%I', a.attname), ', ' order by a.attnum)
      into v_colunas
      from pg_attribute a
      join pg_class c on c.oid = a.attrelid
      join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'clube'
       and c.relname = v_nome
       and a.attnum > 0
       and not a.attisdropped
       and a.attgenerated = '';

    if v_colunas is null then
      raise exception 'Cópia abortada: tabela % não possui colunas copiáveis', v_nome;
    end if;

    execute format(
      'insert into clube_novo.%I (%s) overriding system value select %s from clube.%I',
      v_nome, v_colunas, v_colunas, v_nome
    );
  end loop;
end
$copiar_dados$;

-- Sincroniza as sequências identity independentes criadas em clube_novo.
do $identidades$
declare
  r record;
  v_seq text;
  v_max bigint;
begin
  for r in
    select c.relname as tabela, a.attname as coluna
      from pg_attribute a
      join pg_class c on c.oid = a.attrelid
      join pg_namespace n on n.oid = c.relnamespace
      join _clube_novo_manifesto m on m.nome = c.relname
     where n.nspname = 'clube_novo'
       and a.attnum > 0
       and not a.attisdropped
       and a.attidentity <> ''
     order by c.relname, a.attnum
  loop
    v_seq := pg_get_serial_sequence(format('%I.%I', 'clube_novo', r.tabela), r.coluna);
    if v_seq is null then
      raise exception 'Cópia abortada: sequência identity não encontrada para %.%', r.tabela, r.coluna;
    end if;
    execute format('select max(%I)::bigint from clube_novo.%I', r.coluna, r.tabela) into v_max;
    perform setval(v_seq::regclass, coalesce(v_max, 1), v_max is not null);
  end loop;
end
$identidades$;

-- Recria cada FK apontando para a tabela correspondente em clube_novo.
do $foreign_keys$
declare
  r record;
  v_def text;
begin
  for r in
    select origem.relname as tabela, con.conname, pg_get_constraintdef(con.oid, true) as definicao
      from pg_constraint con
      join pg_class origem on origem.oid = con.conrelid
      join pg_namespace origem_ns on origem_ns.oid = origem.relnamespace
      join _clube_novo_manifesto m on m.nome = origem.relname
     where con.contype = 'f' and origem_ns.nspname = 'clube'
     order by origem.relname, con.conname
  loop
    v_def := replace(r.definicao, 'REFERENCES clube.', 'REFERENCES clube_novo.');
    if v_def = r.definicao then
      raise exception 'Cópia abortada: FK %.% não pôde ser redirecionada', r.tabela, r.conname;
    end if;
    execute format('alter table clube_novo.%I add constraint %I %s', r.tabela, r.conname, v_def);
  end loop;
end
$foreign_keys$;

-- Replica identidade lógica de publicação, mesmo sem publicação ativa nessas tabelas.
do $replica_identity$
declare
  r record;
  v_indice text;
begin
  for r in select nome, relreplident from _clube_novo_pre order by nome loop
    if r.relreplident = 'f' then
      execute format('alter table clube_novo.%I replica identity full', r.nome);
    elsif r.relreplident = 'n' then
      execute format('alter table clube_novo.%I replica identity nothing', r.nome);
    elsif r.relreplident = 'i' then
      select ic.relname
        into v_indice
        from pg_index i
        join pg_class sc on sc.oid = i.indrelid
        join pg_namespace sn on sn.oid = sc.relnamespace
        join pg_class ic on ic.oid = i.indexrelid
       where sn.nspname = 'clube' and sc.relname = r.nome and i.indisreplident;
      if v_indice is null then
        raise exception 'Cópia abortada: índice de replica identity ausente para %', r.nome;
      end if;
      execute format('alter table clube_novo.%I replica identity using index %I', r.nome, v_indice);
    end if;
  end loop;
end
$replica_identity$;

-- Recria policies e os flags RLS exatamente como na origem.
do $policies_rls$
declare
  r record;
  v_roles text;
  v_cmd text;
  v_sql text;
begin
  for r in
    select c.relname as tabela, p.*, pg_get_expr(p.polqual, p.polrelid) as expr_using,
           pg_get_expr(p.polwithcheck, p.polrelid) as expr_check
      from pg_policy p
      join pg_class c on c.oid = p.polrelid
      join pg_namespace n on n.oid = c.relnamespace
      join _clube_novo_manifesto m on m.nome = c.relname
     where n.nspname = 'clube'
     order by c.relname, p.polname
  loop
    select string_agg(case when x.role_oid = 0 then 'public' else quote_ident(pr.rolname) end, ', ' order by x.ord)
      into v_roles
      from unnest(r.polroles) with ordinality x(role_oid, ord)
      left join pg_roles pr on pr.oid = x.role_oid;

    v_cmd := case r.polcmd
      when 'r' then 'select' when 'a' then 'insert' when 'w' then 'update'
      when 'd' then 'delete' when '*' then 'all'
      else null end;
    if v_cmd is null or v_roles is null then
      raise exception 'Cópia abortada: policy %.% possui comando/roles não reconhecidos', r.tabela, r.polname;
    end if;

    v_sql := format(
      'create policy %I on clube_novo.%I as %s for %s to %s',
      r.polname, r.tabela,
      case when r.polpermissive then 'permissive' else 'restrictive' end,
      v_cmd, v_roles
    );
    if r.expr_using is not null then v_sql := v_sql || format(' using (%s)', r.expr_using); end if;
    if r.expr_check is not null then v_sql := v_sql || format(' with check (%s)', r.expr_check); end if;
    execute v_sql;
  end loop;

  for r in select * from _clube_novo_pre order by nome loop
    if r.relrowsecurity then execute format('alter table clube_novo.%I enable row level security', r.nome); end if;
    if r.relforcerowsecurity then execute format('alter table clube_novo.%I force row level security', r.nome); end if;
  end loop;
end
$policies_rls$;

-- Recria gatilhos somente depois da carga. As funções continuam em clube por decisão de transição.
do $triggers$
declare
  r record;
  v_def text;
begin
  for r in
    select c.relname as tabela, t.tgname, t.tgenabled, pg_get_triggerdef(t.oid, true) as definicao
      from pg_trigger t
      join pg_class c on c.oid = t.tgrelid
      join pg_namespace n on n.oid = c.relnamespace
      join _clube_novo_manifesto m on m.nome = c.relname
     where n.nspname = 'clube' and not t.tgisinternal
     order by c.relname, t.tgname
  loop
    v_def := replace(
      r.definicao,
      format(' ON clube.%I ', r.tabela),
      format(' ON clube_novo.%I ', r.tabela)
    );
    if v_def = r.definicao then
      raise exception 'Cópia abortada: gatilho %.% não pôde ser redirecionado', r.tabela, r.tgname;
    end if;
    execute v_def;
    if r.tgenabled = 'D' then
      execute format('alter table clube_novo.%I disable trigger %I', r.tabela, r.tgname);
    elsif r.tgenabled = 'R' then
      execute format('alter table clube_novo.%I enable replica trigger %I', r.tabela, r.tgname);
    elsif r.tgenabled = 'A' then
      execute format('alter table clube_novo.%I enable always trigger %I', r.tabela, r.tgname);
    end if;
  end loop;
end
$triggers$;

do $postflight$
declare
  r record;
  v_oid oid;
  v_linhas bigint;
  v_fingerprint text;
begin
  if (
    select array_agg(c.relname::text order by c.relname)
      from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'clube_novo' and c.relkind in ('r', 'p')
  ) is distinct from (
    select array_agg(nome order by nome) from _clube_novo_manifesto
  ) then
    raise exception 'Cópia abortada: clube_novo não contém exatamente as 21 tabelas';
  end if;

  -- Fontes preservadas por OID e conteúdo; cópias iguais por contagem/fingerprint.
  for r in select * from _clube_novo_pre order by nome loop
    select c.oid into v_oid
      from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'clube' and c.relname = r.nome and c.relkind = 'r';
    if v_oid is distinct from r.oid_fonte then
      raise exception 'Cópia abortada: fonte clube.% mudou de identidade/local', r.nome;
    end if;

    execute format(
      'select count(*)::bigint, md5(coalesce(string_agg(md5(to_jsonb(t)::text), '''' order by md5(to_jsonb(t)::text)), '''')) from clube.%I t',
      r.nome
    ) into v_linhas, v_fingerprint;
    if v_linhas is distinct from r.linhas or v_fingerprint is distinct from r.fingerprint then
      raise exception 'Cópia abortada: fonte clube.% teve alteração de dados', r.nome;
    end if;

    execute format(
      'select count(*)::bigint, md5(coalesce(string_agg(md5(to_jsonb(t)::text), '''' order by md5(to_jsonb(t)::text)), '''')) from clube_novo.%I t',
      r.nome
    ) into v_linhas, v_fingerprint;
    if v_linhas is distinct from r.linhas or v_fingerprint is distinct from r.fingerprint then
      raise exception 'Cópia abortada: conteúdo da cópia clube_novo.% divergiu', r.nome;
    end if;
  end loop;

  -- Mesmas colunas, tipos, nulabilidade, identidades, generated e defaults.
  if exists (
    with fonte as (
      select c.relname, a.attname,
             row_number() over(partition by c.relname order by a.attnum) ordinal,
             format_type(a.atttypid, a.atttypmod) tipo,
             a.attnotnull, a.attidentity, a.attgenerated,
             case when a.attidentity<>'' then '<identity>'
                  else coalesce(pg_get_expr(d.adbin, d.adrelid), '') end default_expr
        from pg_attribute a join pg_class c on c.oid=a.attrelid
        join pg_namespace n on n.oid=c.relnamespace
        join _clube_novo_manifesto m on m.nome=c.relname
        left join pg_attrdef d on d.adrelid=a.attrelid and d.adnum=a.attnum
       where n.nspname='clube' and a.attnum>0 and not a.attisdropped
    ), nova as (
      select c.relname, a.attname,
             row_number() over(partition by c.relname order by a.attnum) ordinal,
             format_type(a.atttypid, a.atttypmod) tipo,
             a.attnotnull, a.attidentity, a.attgenerated,
             case when a.attidentity<>'' then '<identity>'
                  else coalesce(pg_get_expr(d.adbin, d.adrelid), '') end default_expr
        from pg_attribute a join pg_class c on c.oid=a.attrelid
        join pg_namespace n on n.oid=c.relnamespace
        join _clube_novo_manifesto m on m.nome=c.relname
        left join pg_attrdef d on d.adrelid=a.attrelid and d.adnum=a.attnum
       where n.nspname='clube_novo' and a.attnum>0 and not a.attisdropped
    )
    (select * from fonte except select * from nova)
    union all
    (select * from nova except select * from fonte)
  ) then
    raise exception 'Cópia abortada: assinatura de colunas/defaults divergiu';
  end if;

  -- Gate semântico de constraints: nome, tipo, colunas, expressão normalizada,
  -- alvo/colunas/regras de FK, deferrability e estado de validação.
  if exists (
    with fonte as (
      select c.relname,con.conname,con.contype,
             array(select a.attname::text from unnest(con.conkey) with ordinality k(attnum,ord)
                   join pg_attribute a on a.attrelid=con.conrelid and a.attnum=k.attnum
                   order by k.ord) colunas,
             case when con.contype='c'
                  then regexp_replace(pg_get_expr(con.conbin,con.conrelid,true),'\s+',' ','g')
                  else '' end expressao,
             case when con.contype='f' then dc.relname::text else '' end alvo_tabela,
             case when con.contype='f'
                  then array(select a.attname::text from unnest(con.confkey) with ordinality k(attnum,ord)
                             join pg_attribute a on a.attrelid=con.confrelid and a.attnum=k.attnum
                             order by k.ord)
                  else array[]::text[] end alvo_colunas,
             con.confupdtype,con.confdeltype,con.confmatchtype,
             con.condeferrable,con.condeferred,con.convalidated,
             coalesce(con.conexclop::text,'') operadores_exclusao
        from pg_constraint con join pg_class c on c.oid=con.conrelid
        join pg_namespace n on n.oid=c.relnamespace
        join _clube_novo_manifesto m on m.nome=c.relname
        left join pg_class dc on dc.oid=con.confrelid
       where n.nspname='clube'
    ), nova as (
      select c.relname,con.conname,con.contype,
             array(select a.attname::text from unnest(con.conkey) with ordinality k(attnum,ord)
                   join pg_attribute a on a.attrelid=con.conrelid and a.attnum=k.attnum
                   order by k.ord) colunas,
             case when con.contype='c'
                  then regexp_replace(pg_get_expr(con.conbin,con.conrelid,true),'\s+',' ','g')
                  else '' end expressao,
             case when con.contype='f' then dc.relname::text else '' end alvo_tabela,
             case when con.contype='f'
                  then array(select a.attname::text from unnest(con.confkey) with ordinality k(attnum,ord)
                             join pg_attribute a on a.attrelid=con.confrelid and a.attnum=k.attnum
                             order by k.ord)
                  else array[]::text[] end alvo_colunas,
             con.confupdtype,con.confdeltype,con.confmatchtype,
             con.condeferrable,con.condeferred,con.convalidated,
             coalesce(con.conexclop::text,'') operadores_exclusao
        from pg_constraint con join pg_class c on c.oid=con.conrelid
        join pg_namespace n on n.oid=c.relnamespace
        join _clube_novo_manifesto m on m.nome=c.relname
        left join pg_class dc on dc.oid=con.confrelid
       where n.nspname='clube_novo'
    )
    (select * from fonte except all select * from nova)
    union all
    (select * from nova except all select * from fonte)
  ) then
    raise exception 'Cópia abortada: constraints divergem da fonte';
  end if;

  if (select count(*) from pg_constraint con join pg_class c on c.oid=con.conrelid join pg_namespace n on n.oid=c.relnamespace join _clube_novo_manifesto m on m.nome=c.relname where n.nspname='clube')
     <> (select count(*) from pg_constraint con join pg_class c on c.oid=con.conrelid join pg_namespace n on n.oid=c.relnamespace join _clube_novo_manifesto m on m.nome=c.relname where n.nspname='clube_novo') then
    raise exception 'Cópia abortada: quantidade de constraints divergiu';
  end if;

  -- Gate semântico de índices, independente dos attnums físicos.
  if exists (
    with fonte as (
      select t.relname tabela,x.relname indice,am.amname,
             i.indisunique,i.indisprimary,i.indisexclusion,i.indimmediate,
             i.indisvalid,i.indisready,i.indislive,i.indisclustered,i.indisreplident,
             i.indnullsnotdistinct,
             array(select pg_get_indexdef(i.indexrelid,k,true)
                     from generate_series(1,i.indnatts) k order by k) itens,
             regexp_replace(coalesce(pg_get_expr(i.indpred,i.indrelid,true),''),'\s+',' ','g') predicado,
             coalesce(x.reloptions::text,'') opcoes
        from pg_index i join pg_class t on t.oid=i.indrelid
        join pg_namespace n on n.oid=t.relnamespace
        join pg_class x on x.oid=i.indexrelid join pg_am am on am.oid=x.relam
        join _clube_novo_manifesto m on m.nome=t.relname
       where n.nspname='clube'
    ), nova as (
      select t.relname tabela,x.relname indice,am.amname,
             i.indisunique,i.indisprimary,i.indisexclusion,i.indimmediate,
             i.indisvalid,i.indisready,i.indislive,i.indisclustered,i.indisreplident,
             i.indnullsnotdistinct,
             array(select pg_get_indexdef(i.indexrelid,k,true)
                     from generate_series(1,i.indnatts) k order by k) itens,
             regexp_replace(coalesce(pg_get_expr(i.indpred,i.indrelid,true),''),'\s+',' ','g') predicado,
             coalesce(x.reloptions::text,'') opcoes
        from pg_index i join pg_class t on t.oid=i.indrelid
        join pg_namespace n on n.oid=t.relnamespace
        join pg_class x on x.oid=i.indexrelid join pg_am am on am.oid=x.relam
        join _clube_novo_manifesto m on m.nome=t.relname
       where n.nspname='clube_novo'
    )
    (select * from fonte except all select * from nova)
    union all
    (select * from nova except all select * from fonte)
  ) then
    raise exception 'Cópia abortada: índices divergem da fonte';
  end if;

  if (select count(*) from pg_index i join pg_class c on c.oid=i.indrelid join pg_namespace n on n.oid=c.relnamespace join _clube_novo_manifesto m on m.nome=c.relname where n.nspname='clube')
     <> (select count(*) from pg_index i join pg_class c on c.oid=i.indrelid join pg_namespace n on n.oid=c.relnamespace join _clube_novo_manifesto m on m.nome=c.relname where n.nspname='clube_novo') then
    raise exception 'Cópia abortada: quantidade de índices divergiu';
  end if;

  -- RLS/policies e gatilhos de usuário preservados.
  if exists (
    select 1 from _clube_novo_pre p
    join pg_class c on c.relname=p.nome and c.relnamespace=to_regnamespace('clube_novo')
    where c.relrowsecurity is distinct from p.relrowsecurity
       or c.relforcerowsecurity is distinct from p.relforcerowsecurity
       or c.relreplident is distinct from p.relreplident
  ) then
    raise exception 'Cópia abortada: flags RLS/replica identity divergiram';
  end if;

  if (select count(*) from pg_policy p join pg_class c on c.oid=p.polrelid join pg_namespace n on n.oid=c.relnamespace join _clube_novo_manifesto m on m.nome=c.relname where n.nspname='clube')
     <> (select count(*) from pg_policy p join pg_class c on c.oid=p.polrelid join pg_namespace n on n.oid=c.relnamespace join _clube_novo_manifesto m on m.nome=c.relname where n.nspname='clube_novo') then
    raise exception 'Cópia abortada: quantidade de policies divergiu';
  end if;

  if (select count(*) from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace join _clube_novo_manifesto m on m.nome=c.relname where n.nspname='clube' and not t.tgisinternal)
     <> (select count(*) from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace join _clube_novo_manifesto m on m.nome=c.relname where n.nspname='clube_novo' and not t.tgisinternal) then
    raise exception 'Cópia abortada: quantidade de gatilhos divergiu';
  end if;

  -- Nenhuma FK da cópia pode apontar para fora de clube_novo.
  if exists (
    select 1 from pg_constraint con
    join pg_class o on o.oid=con.conrelid join pg_namespace ons on ons.oid=o.relnamespace
    join pg_class d on d.oid=con.confrelid join pg_namespace dns on dns.oid=d.relnamespace
    where con.contype='f' and (ons.nspname='clube_novo' or dns.nspname='clube_novo')
      and (ons.nspname<>'clube_novo' or dns.nspname<>'clube_novo')
  ) then
    raise exception 'Cópia abortada: FK do schema novo aponta para fora da cópia';
  end if;

  -- O schema nasce fechado: não é exposto automaticamente à Data API.
  if exists (
    select 1 from pg_roles role_row
     where role_row.rolname in ('anon','authenticated','service_role','authenticator')
       and has_schema_privilege(role_row.rolname,'clube_novo','USAGE')
  ) then
    raise exception 'Cópia abortada: schema novo recebeu USAGE inesperado de papel da Data API';
  end if;

  -- A cópia não é conectada ao motor nesta rodada.
  if exists (
    select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
     where p.prokind in ('f','p')
       and n.nspname not in ('pg_catalog','information_schema')
       and n.nspname not like 'pg_toast%'
       and pg_get_functiondef(p.oid) ~
         'clube_novo\.(texto_do_jogo|atributo_jogo|corpo_ordem|pe|posicao_jogo|playstyle|estilo_ia|habilidade_jogo|impeto_jogo|tecnico_jogo|carta_jogo|carta_atributo_jogo|carta_corpo_jogo|carta_habilidade_jogo|carta_estilo_ia_jogo|carta_posicao_jogo|carta_impeto_jogo|impeto_atributo_jogo|funcao_sistema|funcao_alias|mapa_do_jogo)([^[:alnum:]_]|$)'
  ) then
    raise exception 'Cópia abortada: rotina passou a apontar para clube_novo';
  end if;
end
$postflight$;

commit;
