-- Escritores declarativos do Extrator. Só clube_novo; não altera tabelas de domínio.
-- O runtime recebe esta configuração no pedido tipado e não roteia famílias/tabelas por listas locais.

create table if not exists clube_novo.contrato_leitura_escritor_dominio (
  escritor_id text primary key check (escritor_id ~ '^[a-z0-9][a-z0-9._-]{2,127}$'),
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  chave_familia text not null,
  versao_escritor text not null,
  schema_envelope jsonb not null,
  identidade_canonica jsonb not null,
  operacao text not null check (operacao in ('upsert')),
  ativo boolean not null default true,
  proveniencia text not null,
  unique (contrato_id, chave_familia),
  foreign key (contrato_id, chave_familia) references clube_novo.contrato_leitura_familia(contrato_id, chave_familia) on delete restrict
);

create table if not exists clube_novo.contrato_leitura_escritor_destino (
  destino_id bigint generated always as identity primary key,
  escritor_id text not null references clube_novo.contrato_leitura_escritor_dominio(escritor_id) on delete restrict,
  destino_schema text not null check (destino_schema = 'clube_novo'),
  destino_tabela text not null check (destino_tabela ~ '^[a-z][a-z0-9_]{1,62}$'),
  operacao text not null check (operacao = 'upsert'),
  colunas_chave text[] not null check (cardinality(colunas_chave) > 0),
  colunas_escrita text[] not null check (cardinality(colunas_escrita) > 0),
  exige_procedencia boolean not null default true,
  ordem_lote integer not null default 100 check (ordem_lote > 0),
  ativo boolean not null default true,
  proveniencia text not null,
  unique (escritor_id, destino_schema, destino_tabela)
);

alter table clube_novo.contrato_leitura_escritor_destino
  add column if not exists tipos_colunas jsonb not null default '{}'::jsonb;

-- Retificação de alvos já comprovados pelos próprios validadores e pelo schema.
update clube_novo.contrato_leitura_campo
set entidade_destino = 'carta_playstyle_jogo.playstyle_id'
where contrato_id = 'clubef-dt870-2026-r1'
  and chave_campo in ('carta.playstyle.primario', 'carta.playstyle.secundario');

update clube_novo.contrato_leitura_campo
set entidade_destino = 'tecnico_estilo_jogo.proficiencia'
where contrato_id = 'clubef-dt870-2026-r1'
  and chave_campo = 'tecnico.estilo.sobreposicao';

insert into clube_novo.contrato_leitura_escritor_dominio
  (escritor_id, contrato_id, chave_familia, versao_escritor, schema_envelope, identidade_canonica, operacao, proveniencia)
select
  'extrator.envelope.' || f.chave_familia || '.v1',
  f.contrato_id, f.chave_familia, 'v1',
  jsonb_build_object('versao','envelope_aplicacao_familia_v1','registro_obrigatorio',jsonb_build_array('identidade','valores','procedencia','destino_id')),
  f.identidade, 'upsert',
  'Contrato declarativo V1; origem: contrato_leitura_familia/campo e PK do schema clube_novo'
from clube_novo.contrato_leitura_familia f
where f.contrato_id = 'clubef-dt870-2026-r1'
on conflict (escritor_id) do update set
  versao_escritor = excluded.versao_escritor,
  schema_envelope = excluded.schema_envelope,
  identidade_canonica = excluded.identidade_canonica,
  operacao = excluded.operacao,
  ativo = true,
  proveniencia = excluded.proveniencia;

-- Cada chave abaixo é a PK efetiva do schema. As colunas graváveis vêm dos
-- campos declarados; identidade adicional exigida pelo relacionamento entra no envelope como chave, nunca por rótulo.
with chaves(familia,tabela,colunas) as (
 values
 ('cartas','carta_jogo',array['card_id']::text[]),
 ('catalogos','habilidade_jogo',array['skill_id']::text[]),
 ('catalogos','playstyle',array['id_jogo']::text[]),
 ('dimensoes','clube_jogo',array['codigo_jogo']::text[]),
 ('dimensoes','liga_jogo',array['codigo_jogo']::text[]),
 ('dimensoes','nacionalidade_jogo',array['codigo_jogo']::text[]),
 ('relacoes','carta_atributo_jogo',array['card_id','codigo_atributo']::text[]),
 ('relacoes','carta_corpo_jogo',array['card_id','codigo_corpo']::text[]),
 ('relacoes','carta_estilo_ia_jogo',array['card_id','bit_estilo_ia']::text[]),
 ('relacoes','carta_habilidade_jogo',array['card_id','skill_id']::text[]),
 ('relacoes','carta_playstyle_jogo',array['card_id','slot_fisico']::text[]),
 ('relacoes','carta_posicao_jogo',array['card_id','posicao_id']::text[]),
 ('relacoes','carta_posicao_principal_jogo',array['card_id']::text[]),
 ('impetos','carta_impeto_jogo',array['card_id','slot']::text[]),
 ('impetos','impeto_atributo_jogo',array['codigo_impeto','codigo_atributo']::text[]),
 ('impetos','impeto_classe_candidato_jogo',array['codigo_impeto']::text[]),
 ('impetos','impeto_condicao_classe_jogo',array['codigo_impeto']::text[]),
 ('impetos','impeto_condicao_clube_jogo',array['codigo_impeto','ordem']::text[]),
 ('impetos','impeto_condicao_liga_jogo',array['codigo_impeto']::text[]),
 ('impetos','impeto_condicao_liga_membro_jogo',array['codigo_impeto','codigo_liga_membro']::text[]),
 ('impetos','impeto_condicao_nacionalidade_jogo',array['codigo_impeto']::text[]),
 ('impetos','impeto_condicao_parametro_faixa_jogo',array['codigo_impeto']::text[]),
 ('impetos','impeto_jogo',array['codigo_jogo']::text[]),
 ('impetos','tipo_impeto_jogo',array['codigo_raw']::text[]),
 ('tecnicos','afinidade_tecnico_jogo',array['codigo_jogo']::text[]),
 ('tecnicos','tecnico_atributo_jogo',array['tecnico_id','ordem']::text[]),
 ('tecnicos','tecnico_estilo_jogo',array['tecnico_id','codigo_estilo']::text[]),
 ('tecnicos','tecnico_jogo',array['id']::text[]),
 ('textos','texto_do_jogo',array['secao','id_texto']::text[])
), campos as (
 select c.chave_familia, split_part(c.entidade_destino,'.',1) tabela,
        array_agg(distinct split_part(c.entidade_destino,'.',2) order by split_part(c.entidade_destino,'.',2)) filter (where position('.' in c.entidade_destino) > 0) as colunas
 from clube_novo.contrato_leitura_campo c
 where c.contrato_id='clubef-dt870-2026-r1' and c.ativo
 group by c.chave_familia, split_part(c.entidade_destino,'.',1)
)
insert into clube_novo.contrato_leitura_escritor_destino
  (escritor_id,destino_schema,destino_tabela,operacao,colunas_chave,colunas_escrita,ordem_lote,proveniencia)
select 'extrator.envelope.'||k.familia||'.v1', 'clube_novo', k.tabela, 'upsert', k.colunas,
       case when k.tabela='texto_do_jogo' then array['texto']::text[] else array(select distinct x from unnest(coalesce(c.colunas,array[]::text[]) || k.colunas) x order by x) end,
       100, 'PK efetiva do schema + campo tipado do contrato V1'
from chaves k left join campos c on c.chave_familia=k.familia and c.tabela=k.tabela
on conflict (escritor_id,destino_schema,destino_tabela) do update set
 colunas_chave=excluded.colunas_chave,colunas_escrita=excluded.colunas_escrita,ativo=true,proveniencia=excluded.proveniencia;

update clube_novo.contrato_leitura_escritor_destino d
set tipos_colunas = src.tipos
from (
 select d2.destino_id, jsonb_object_agg(c.column_name,c.data_type) tipos
 from clube_novo.contrato_leitura_escritor_destino d2
 join information_schema.columns c on c.table_schema=d2.destino_schema and c.table_name=d2.destino_tabela
 where c.column_name = any(d2.colunas_escrita)
 group by d2.destino_id
) src
where d.destino_id=src.destino_id;

create or replace function clube_novo.obter_pedido_leitura_tipado_ativo()
returns jsonb language plpgsql set search_path = clube_novo, pg_temp as $$
declare pedido jsonb; cid text;
begin
 pedido:=clube_novo.obter_pedido_leitura_tipado_sem_revisao_v1(); cid:=pedido->>'contrato_id';
 if cid is null or cid='' then raise exception 'pedido tipado sem contrato_id'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_politica_revisao where contrato_id=cid) then raise exception 'pedido tipado sem política de aprovação interna'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid) then raise exception 'pedido tipado sem cobertura de catálogo'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid) then raise exception 'pedido tipado sem projeção canônica de cartas'; end if;
 if exists (
   select 1 from clube_novo.contrato_leitura_familia f left join clube_novo.contrato_leitura_escritor_dominio e
     on e.contrato_id=f.contrato_id and e.chave_familia=f.chave_familia and e.ativo
   where f.contrato_id=cid and f.obrigatoria and e.escritor_id is null
 ) then raise exception 'pedido tipado sem escritor declarativo para família obrigatória'; end if;
 if exists (
   select 1 from clube_novo.contrato_leitura_escritor_dominio e
   where e.contrato_id=cid and e.ativo and not exists (select 1 from clube_novo.contrato_leitura_escritor_destino d where d.escritor_id=e.escritor_id and d.ativo)
 ) then raise exception 'pedido tipado com escritor sem destino declarado'; end if;
 return pedido || jsonb_build_object(
  'politica_revisao',(select jsonb_build_object('revisao_humana_obrigatoria',p.revisao_humana_obrigatoria,'cobertura_aprovada',p.cobertura_aprovada,'carga_autorizada',p.carga_autorizada,'promocao_snapshot_autorizada',p.promocao_snapshot_autorizada,'decisao',p.decisao,'proveniencia',p.proveniencia,'atualizado_em',p.atualizado_em) from clube_novo.contrato_leitura_politica_revisao p where p.contrato_id=cid),
  'catalogos_fisicos',(select coalesce(jsonb_agg(jsonb_build_object('schema',catalogo_schema,'table',catalogo_tabela,'modo_validacao',modo_validacao,'artefato_fisico',artefato_fisico,'coluna_chave_fisica',coluna_chave_fisica,'colunas_chave_canonica',colunas_chave_canonica,'papel_fonte',papel_fonte,'familia_dependencia',familia_dependencia,'check_dependencia',check_dependencia,'proveniencia',proveniencia) order by catalogo_tabela),'[]'::jsonb) from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid),
  'projecoes_cartas',(select coalesce(jsonb_agg(jsonb_build_object('chave_campo',chave_campo,'artefato_fisico',artefato_fisico,'coluna_fisica',coluna_fisica,'destino_schema',destino_schema,'destino_tabela',destino_tabela,'destino_coluna',destino_coluna,'tipo_valor',tipo_valor,'proveniencia',proveniencia) order by chave_campo),'[]'::jsonb) from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid),
  'escritores_dominio',(select coalesce(jsonb_agg(jsonb_build_object('escritor_id',e.escritor_id,'familia',e.chave_familia,'versao',e.versao_escritor,'schema_envelope',e.schema_envelope,'identidade_canonica',e.identidade_canonica,'operacao',e.operacao,'destinos',(select coalesce(jsonb_agg(jsonb_build_object('destino_id',d.destino_id,'schema',d.destino_schema,'tabela',d.destino_tabela,'operacao',d.operacao,'colunas_chave',d.colunas_chave,'colunas_escrita',d.colunas_escrita,'tipos_colunas',d.tipos_colunas,'exige_procedencia',d.exige_procedencia,'ordem_lote',d.ordem_lote,'proveniencia',d.proveniencia) order by d.ordem_lote,d.destino_tabela),'[]'::jsonb) from clube_novo.contrato_leitura_escritor_destino d where d.escritor_id=e.escritor_id and d.ativo),'proveniencia',e.proveniencia) order by e.chave_familia),'[]'::jsonb) from clube_novo.contrato_leitura_escritor_dominio e where e.contrato_id=cid and e.ativo)
 );
end; $$;

comment on table clube_novo.contrato_leitura_escritor_dominio is 'Escritor por família escolhido pelo pedido tipado, nunca por lista local.';
comment on table clube_novo.contrato_leitura_escritor_destino is 'Alvos e chaves de upsert autorizados pelo contrato. O runtime só aceita envelopes declarados aqui.';

-- O fingerprint do contrato deve reagir a qualquer mudança estrutural do
-- pedido. A política de aprovação fica fora desse material para que o aceite
-- não invalide o pacote que ela própria sela.
create or replace function clube_novo.fingerprint_material_contrato_leitura(p_contrato_id text)
returns text language sql stable set search_path = clube_novo, pg_temp as $$
 with material as (
  select jsonb_build_object(
   'familias',(select coalesce(jsonb_agg(to_jsonb(x) order by x.chave_familia),'[]'::jsonb) from contrato_leitura_familia x where x.contrato_id=p_contrato_id),
   'arquivos',(select coalesce(jsonb_agg(to_jsonb(x) order by x.arquivo_id),'[]'::jsonb) from contrato_leitura_arquivo x where x.contrato_id=p_contrato_id),
   'campos',(select coalesce(jsonb_agg(to_jsonb(x) order by x.chave_campo),'[]'::jsonb) from contrato_leitura_campo x where x.contrato_id=p_contrato_id),
   'requisitos',(select coalesce(jsonb_agg(to_jsonb(x) order by x.chave_requisito),'[]'::jsonb) from contrato_leitura_requisito x where x.contrato_id=p_contrato_id),
   'localizadores',(select coalesce(jsonb_agg(to_jsonb(x) order by x.papel_fonte,x.ordem),'[]'::jsonb) from contrato_leitura_fonte_localizador x where x.contrato_id=p_contrato_id),
   'expectativas',(select coalesce(jsonb_agg(to_jsonb(x) order by x.chave_familia,x.chave_metrica),'[]'::jsonb) from contrato_leitura_expectativa x where x.contrato_id=p_contrato_id),
   'catalogos_fisicos',(select coalesce(jsonb_agg(to_jsonb(x) order by x.catalogo_schema,x.catalogo_tabela),'[]'::jsonb) from contrato_leitura_catalogo_fisico x where x.contrato_id=p_contrato_id),
   'projecoes_cartas',(select coalesce(jsonb_agg(to_jsonb(x) order by x.chave_campo),'[]'::jsonb) from contrato_leitura_projecao_cartas x where x.contrato_id=p_contrato_id),
   'cadeia',(select coalesce(jsonb_agg(to_jsonb(x) order by x.elo_id),'[]'::jsonb) from contrato_leitura_cadeia x where x.contrato_id=p_contrato_id),
   'escritores',(select coalesce(jsonb_agg(jsonb_build_object('escritor',to_jsonb(e),'destinos',(select coalesce(jsonb_agg(to_jsonb(d) order by d.destino_id),'[]'::jsonb) from contrato_leitura_escritor_destino d where d.escritor_id=e.escritor_id)) order by e.chave_familia),'[]'::jsonb) from contrato_leitura_escritor_dominio e where e.contrato_id=p_contrato_id)
  ) dados
 ) select encode(extensions.digest(convert_to(dados::text,'UTF8'),'sha256'),'hex') from material;
$$;

create or replace function clube_novo.atualizar_fingerprint_contrato_leitura_trigger()
returns trigger language plpgsql set search_path = clube_novo, pg_temp as $$
declare cid text;
begin
 cid := coalesce(new.contrato_id, old.contrato_id);
 update contrato_leitura_jogo set fingerprint_contrato_sha256=fingerprint_material_contrato_leitura(cid) where contrato_id=cid;
 return null;
end; $$;

create or replace function clube_novo.atualizar_fingerprint_contrato_leitura_destino_trigger()
returns trigger language plpgsql set search_path = clube_novo, pg_temp as $$
declare eid text; cid text;
begin
 eid := coalesce(new.escritor_id, old.escritor_id);
 select contrato_id into cid from contrato_leitura_escritor_dominio where escritor_id=eid;
 if cid is not null then update contrato_leitura_jogo set fingerprint_contrato_sha256=fingerprint_material_contrato_leitura(cid) where contrato_id=cid; end if;
 return null;
end; $$;

do $$
declare t text;
begin
 foreach t in array array['contrato_leitura_familia','contrato_leitura_arquivo','contrato_leitura_campo','contrato_leitura_requisito','contrato_leitura_fonte_localizador','contrato_leitura_expectativa','contrato_leitura_catalogo_fisico','contrato_leitura_projecao_cartas','contrato_leitura_cadeia','contrato_leitura_escritor_dominio'] loop
  execute format('drop trigger if exists contrato_leitura_fingerprint_au on clube_novo.%I',t);
  execute format('create trigger contrato_leitura_fingerprint_au after insert or update or delete on clube_novo.%I for each row execute function clube_novo.atualizar_fingerprint_contrato_leitura_trigger()',t);
 end loop;
end $$;
drop trigger if exists contrato_leitura_fingerprint_destino_au on clube_novo.contrato_leitura_escritor_destino;
create trigger contrato_leitura_fingerprint_destino_au after insert or update or delete on clube_novo.contrato_leitura_escritor_destino
for each row execute function clube_novo.atualizar_fingerprint_contrato_leitura_destino_trigger();

update clube_novo.contrato_leitura_jogo
set fingerprint_contrato_sha256=clube_novo.fingerprint_material_contrato_leitura(contrato_id)
where contrato_id='clubef-dt870-2026-r1';
