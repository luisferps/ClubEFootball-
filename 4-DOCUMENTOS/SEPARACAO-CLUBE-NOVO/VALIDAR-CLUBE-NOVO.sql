-- Validação posterior, somente leitura, da cópia paralela clube -> clube_novo.
-- Esperado: 21 linhas conformes e todos os booleanos-resumo = true.

begin;

create temporary table _validacao_manifesto (
  nome text primary key,
  oid_fonte_antes oid not null,
  linhas_antes bigint not null,
  fingerprint_antes text not null
) on commit drop;

insert into _validacao_manifesto values
  ('atributo_jogo',279452,26,'4ac31615dede2a38de4bd96f79cd1f8c'),
  ('carta_atributo_jogo',279589,0,'d41d8cd98f00b204e9800998ecf8427e'),
  ('carta_corpo_jogo',279608,0,'d41d8cd98f00b204e9800998ecf8427e'),
  ('carta_estilo_ia_jogo',279647,0,'d41d8cd98f00b204e9800998ecf8427e'),
  ('carta_habilidade_jogo',279627,0,'d41d8cd98f00b204e9800998ecf8427e'),
  ('carta_impeto_jogo',279684,0,'d41d8cd98f00b204e9800998ecf8427e'),
  ('carta_jogo',229361,42803,'5c1c02e16c017b1585130b4662d7105a'),
  ('carta_posicao_jogo',279665,0,'d41d8cd98f00b204e9800998ecf8427e'),
  ('corpo_ordem',164771,15,'f12a85d96acae01d55d2024d5c8ea084'),
  ('estilo_ia',279394,7,'eaa0a2bf5e0270b66aa0f3fec895ec27'),
  ('funcao_alias',279732,14,'252b82f47043d89471d5783964afd998'),
  ('funcao_sistema',279556,19,'76a55530feb00aaa065792d1df31a3cc'),
  ('habilidade_jogo',279431,72,'5bcee17303efea8428aeb0fd30b4159d'),
  ('impeto_atributo_jogo',279534,1542,'3070ee6b38a0c0287963681d3dc60ed5'),
  ('impeto_jogo',279507,440,'7ac0ed51af32e06b0e85d76ecf0985ac'),
  ('mapa_do_jogo',279345,21,'01ae331913021cac3650306a2dde0a63'),
  ('pe',279377,11,'540f9f462028212ec40982b933f79935'),
  ('playstyle',279385,36,'dc92eed182b9ebb8e7574198e7862152'),
  ('posicao_jogo',279411,13,'965813a30e92d3e08e21ae34ee423091'),
  ('tecnico_jogo',279441,0,'d41d8cd98f00b204e9800998ecf8427e'),
  ('texto_do_jogo',279401,211,'52aabc077acc6b451ce7d7a568857b78');

create temporary table _validacao_dados (
  schema_nome text,
  nome text,
  linhas bigint,
  fingerprint text,
  primary key (schema_nome,nome)
) on commit drop;

do $fotografias$
declare
  v_schema text;
  v_nome text;
  v_linhas bigint;
  v_fp text;
begin
  foreach v_schema in array array['clube','clube_novo'] loop
    for v_nome in select nome from _validacao_manifesto order by nome loop
      execute format(
        'select count(*)::bigint, md5(coalesce(string_agg(md5(to_jsonb(t)::text), '''' order by md5(to_jsonb(t)::text)), '''')) from %I.%I t',
        v_schema,v_nome
      ) into v_linhas,v_fp;
      insert into _validacao_dados values(v_schema,v_nome,v_linhas,v_fp);
    end loop;
  end loop;
end
$fotografias$;

-- 1. Resultado por tabela: origem continua igual e cópia é idêntica.
select m.nome,
       sc.oid=m.oid_fonte_antes as oid_fonte_preservado,
       f.linhas as linhas_clube,
       n.linhas as linhas_clube_novo,
       f.linhas=m.linhas_antes and n.linhas=f.linhas as contagens_ok,
       f.fingerprint=m.fingerprint_antes and n.fingerprint=f.fingerprint as fingerprints_ok
  from _validacao_manifesto m
  join _validacao_dados f on f.schema_nome='clube' and f.nome=m.nome
  join _validacao_dados n on n.schema_nome='clube_novo' and n.nome=m.nome
  left join pg_class sc on sc.oid=m.oid_fonte_antes
  left join pg_namespace sn on sn.oid=sc.relnamespace and sn.nspname='clube'
 order by m.nome;

-- 2. Resumo físico e de dados.
select
  to_regnamespace('clube_novo') is not null as schema_novo_existe,
  (select array_agg(c.relname::text order by c.relname)
     from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='clube_novo' and c.relkind in ('r','p'))
    = (select array_agg(nome order by nome) from _validacao_manifesto)
    as lista_nova_exata,
  (select count(*) from _validacao_manifesto m where to_regclass(format('clube.%I',m.nome)) is not null)=21
    as fontes_continuam_em_clube,
  not exists(
    select 1 from _validacao_manifesto m
    join _validacao_dados f on f.schema_nome='clube' and f.nome=m.nome
    join _validacao_dados n on n.schema_nome='clube_novo' and n.nome=m.nome
    where f.linhas<>m.linhas_antes or n.linhas<>f.linhas
       or f.fingerprint<>m.fingerprint_antes or n.fingerprint<>f.fingerprint
  ) as todos_dados_identicos;

-- 3. Quantidade estrutural por tabela nos dois schemas.
with estrutura as (
  select n.nspname schema_nome,c.relname tabela,c.relrowsecurity,c.relforcerowsecurity,c.relreplident,
         count(distinct con.oid) filter(where con.contype='p') pks,
         count(distinct con.oid) filter(where con.contype='f') fks,
         count(distinct con.oid) filter(where con.contype='c') checks,
         count(distinct i.indexrelid) indices,
         count(distinct p.oid) policies,
         count(distinct t.oid) filter(where not t.tgisinternal) gatilhos_usuario
    from pg_class c join pg_namespace n on n.oid=c.relnamespace
    join _validacao_manifesto m on m.nome=c.relname
    left join pg_constraint con on con.conrelid=c.oid
    left join pg_index i on i.indrelid=c.oid
    left join pg_policy p on p.polrelid=c.oid
    left join pg_trigger t on t.tgrelid=c.oid
   where n.nspname in ('clube','clube_novo')
   group by n.nspname,c.relname,c.relrowsecurity,c.relforcerowsecurity,c.relreplident
)
select f.tabela,
       row(f.relrowsecurity,f.relforcerowsecurity,f.relreplident,f.pks,f.fks,f.checks,f.indices,f.policies,f.gatilhos_usuario)
       is not distinct from
       row(n.relrowsecurity,n.relforcerowsecurity,n.relreplident,n.pks,n.fks,n.checks,n.indices,n.policies,n.gatilhos_usuario)
       as estrutura_resumida_igual,
       f.pks,n.pks as pks_novo,f.fks,n.fks as fks_novo,f.checks,n.checks as checks_novo,
       f.indices,n.indices as indices_novo,f.policies,n.policies as policies_novo,
       f.gatilhos_usuario,n.gatilhos_usuario as gatilhos_novo
  from estrutura f join estrutura n using(tabela)
 where f.schema_nome='clube' and n.schema_nome='clube_novo'
 order by f.tabela;

-- 3b. Gate semântico completo de constraints, sem comparar a string DDL inteira.
with assinatura as (
  select n.nspname schema_nome,c.relname,con.conname,con.contype,
         array(select a.attname::text
                 from unnest(con.conkey) with ordinality k(attnum,ord)
                 join pg_attribute a on a.attrelid=con.conrelid and a.attnum=k.attnum
                order by k.ord) colunas,
         case when con.contype='c'
              then regexp_replace(pg_get_expr(con.conbin,con.conrelid,true),'\s+',' ','g')
              else '' end expressao,
         case when con.contype='f' then dc.relname::text else '' end alvo_tabela,
         case when con.contype='f'
              then array(select a.attname::text
                           from unnest(con.confkey) with ordinality k(attnum,ord)
                           join pg_attribute a on a.attrelid=con.confrelid and a.attnum=k.attnum
                          order by k.ord)
              else array[]::text[] end alvo_colunas,
         con.confupdtype,con.confdeltype,con.confmatchtype,
         con.condeferrable,con.condeferred,con.convalidated,
         coalesce(con.conexclop::text,'') operadores_exclusao
    from pg_constraint con join pg_class c on c.oid=con.conrelid
    join pg_namespace n on n.oid=c.relnamespace
    join _validacao_manifesto m on m.nome=c.relname
    left join pg_class dc on dc.oid=con.confrelid
   where n.nspname in ('clube','clube_novo')
), diffs as (
  (select relname,conname,contype,colunas,expressao,alvo_tabela,alvo_colunas,
          confupdtype,confdeltype,confmatchtype,condeferrable,condeferred,
          convalidated,operadores_exclusao
     from assinatura where schema_nome='clube'
   except all
   select relname,conname,contype,colunas,expressao,alvo_tabela,alvo_colunas,
          confupdtype,confdeltype,confmatchtype,condeferrable,condeferred,
          convalidated,operadores_exclusao
     from assinatura where schema_nome='clube_novo')
  union all
  (select relname,conname,contype,colunas,expressao,alvo_tabela,alvo_colunas,
          confupdtype,confdeltype,confmatchtype,condeferrable,condeferred,
          convalidated,operadores_exclusao
     from assinatura where schema_nome='clube_novo'
   except all
   select relname,conname,contype,colunas,expressao,alvo_tabela,alvo_colunas,
          confupdtype,confdeltype,confmatchtype,condeferrable,condeferred,
          convalidated,operadores_exclusao
     from assinatura where schema_nome='clube')
)
select (select count(*) from assinatura where schema_nome='clube')=74 as constraints_fonte_74,
       (select count(*) from assinatura where schema_nome='clube_novo')=74 as constraints_novas_74,
       count(*)=0 as nenhuma_diferenca_semantica
  from diffs;

-- 3c. Gate semântico de índices por nome, método, propriedades, itens e predicado.
with assinatura as (
  select n.nspname schema_nome,t.relname tabela,x.relname indice,am.amname,
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
    join _validacao_manifesto m on m.nome=t.relname
   where n.nspname in ('clube','clube_novo')
), diffs as (
  (select tabela,indice,amname,indisunique,indisprimary,indisexclusion,
          indimmediate,indisvalid,indisready,indislive,indisclustered,
          indisreplident,indnullsnotdistinct,itens,predicado,opcoes
     from assinatura where schema_nome='clube'
   except all
   select tabela,indice,amname,indisunique,indisprimary,indisexclusion,
          indimmediate,indisvalid,indisready,indislive,indisclustered,
          indisreplident,indnullsnotdistinct,itens,predicado,opcoes
     from assinatura where schema_nome='clube_novo')
  union all
  (select tabela,indice,amname,indisunique,indisprimary,indisexclusion,
          indimmediate,indisvalid,indisready,indislive,indisclustered,
          indisreplident,indnullsnotdistinct,itens,predicado,opcoes
     from assinatura where schema_nome='clube_novo'
   except all
   select tabela,indice,amname,indisunique,indisprimary,indisexclusion,
          indimmediate,indisvalid,indisready,indislive,indisclustered,
          indisreplident,indnullsnotdistinct,itens,predicado,opcoes
     from assinatura where schema_nome='clube')
)
select (select count(*) from assinatura where schema_nome='clube')=41 as indices_fonte_41,
       (select count(*) from assinatura where schema_nome='clube_novo')=41 as indices_novos_41,
       count(*)=0 as nenhuma_diferenca_semantica
  from diffs;

-- 4. As 15 FKs da cópia têm as duas pontas no schema novo.
select con.conname,
       o.relname as origem,d.relname as destino,
       ons.nspname='clube_novo' and dns.nspname='clube_novo' as interna_ao_novo,
       pg_get_constraintdef(con.oid,true) as definicao
  from pg_constraint con
  join pg_class o on o.oid=con.conrelid join pg_namespace ons on ons.oid=o.relnamespace
  join pg_class d on d.oid=con.confrelid join pg_namespace dns on dns.oid=d.relnamespace
 where con.contype='f' and (ons.nspname='clube_novo' or dns.nspname='clube_novo')
 order by o.relname,con.conname;

select count(*)=15 as quinze_fks_internas
  from pg_constraint con
  join pg_class o on o.oid=con.conrelid join pg_namespace ons on ons.oid=o.relnamespace
  join pg_class d on d.oid=con.confrelid join pg_namespace dns on dns.oid=d.relnamespace
 where con.contype='f' and ons.nspname='clube_novo' and dns.nspname='clube_novo';

-- 5. Policies e gatilhos clonados; funções dos gatilhos permanecem em clube.
select schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check
  from pg_policies where schemaname in ('clube','clube_novo')
 order by tablename,schemaname,policyname;

select n.nspname schema_nome,c.relname tabela,t.tgname,t.tgenabled,
       pn.nspname as schema_funcao,p.proname as funcao,
       pg_get_triggerdef(t.oid,true) as definicao
  from pg_trigger t
  join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace
  join pg_proc p on p.oid=t.tgfoid join pg_namespace pn on pn.oid=p.pronamespace
 where n.nspname in ('clube','clube_novo') and not t.tgisinternal
   and c.relname in (select nome from _validacao_manifesto)
 order by c.relname,n.nspname,t.tgname;

-- 6. Motor/rotinas continuam no schema antigo; nenhuma passou a ler clube_novo.
select n.nspname as schema_rotina,p.proname,
       pg_get_function_identity_arguments(p.oid) as argumentos
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where p.prokind in ('f','p')
   and n.nspname not in ('pg_catalog','information_schema')
   and n.nspname not like 'pg_toast%'
   and pg_get_functiondef(p.oid) ~
     'clube\.(texto_do_jogo|atributo_jogo|corpo_ordem|pe|posicao_jogo|playstyle|estilo_ia|habilidade_jogo|impeto_jogo|tecnico_jogo|carta_jogo|carta_atributo_jogo|carta_corpo_jogo|carta_habilidade_jogo|carta_estilo_ia_jogo|carta_posicao_jogo|carta_impeto_jogo|impeto_atributo_jogo|funcao_sistema|funcao_alias|mapa_do_jogo)([^[:alnum:]_]|$)'
 order by n.nspname,p.proname,argumentos;

select count(*)=0 as nenhuma_rotina_le_clube_novo
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where p.prokind in ('f','p')
   and n.nspname not in ('pg_catalog','information_schema')
   and n.nspname not like 'pg_toast%'
   and pg_get_functiondef(p.oid) ~
     'clube_novo\.(texto_do_jogo|atributo_jogo|corpo_ordem|pe|posicao_jogo|playstyle|estilo_ia|habilidade_jogo|impeto_jogo|tecnico_jogo|carta_jogo|carta_atributo_jogo|carta_corpo_jogo|carta_habilidade_jogo|carta_estilo_ia_jogo|carta_posicao_jogo|carta_impeto_jogo|impeto_atributo_jogo|funcao_sistema|funcao_alias|mapa_do_jogo)([^[:alnum:]_]|$)';

select to_regclass('clube.insumo_incompleto') is not null as view_legada_permaneceu,
       (select count(*) from clube.insumo_incompleto)>=0 as view_legada_consultavel,
       pg_get_viewdef('clube.insumo_incompleto'::regclass,true) not like '%clube_novo.%'
         as view_legada_nao_foi_redirecionada;

-- 7. O schema novo permanece privado até uma futura migração de consumidores.
select r.rolname,
       has_schema_privilege(r.rolname,'clube_novo','USAGE') as uso,
       has_schema_privilege(r.rolname,'clube_novo','CREATE') as cria
  from pg_roles r
 where r.rolname in ('postgres','anon','authenticated','service_role','authenticator')
 order by r.rolname;

rollback;
