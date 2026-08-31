-- Completude física versionada por carta para Otimizador e Bonificador.
--
-- Escopo deliberado:
--   * NÃO impede inserir/exibir/publicar uma carta ou uma box;
--   * impede somente enfileirar, iniciar ou concluir trabalho dos motores;
--   * vazio fisicamente conferido é completo; ausência de prova de coleta não é;
--   * toda fila nova, de carta antiga ou nova, exige uma versão vigente;
--   * resultado terminal antigo idêntico pode continuar como histórico reconhecido;
--   * qualquer alteração de insumo invalida a versão vigente e os cálculos ativos.
--
-- Esta migração é preparada para execução posterior. Não executá-la sem antes
-- revisar o VALIDAR e o ROLLBACK que acompanham este arquivo.

do $preflight$
declare
  v_missing text;
begin
  if to_regclass('clube_novo.carta_completude_motor_versao') is not null
     or to_regclass('clube_novo.carta_completude_motor_componente') is not null
     or to_regclass('clube_novo.carta_completude_motor_decisao') is not null
     or to_regclass('clube_novo.migracao_completude_motor_build_snapshot_v1') is not null
     or to_regclass('clube_novo.migracao_gravar_bonus_grant_snapshot_v1') is not null then
    raise exception 'preflight: objetos de completude V1 já existem; nada foi sobrescrito';
  end if;

  if to_regprocedure('public.otimizador_carta_v2(text)') is null
     or to_regprocedure('public.otimizador_proxima_fila_v1(integer)') is null
     or to_regprocedure('public.bonificador_carta_v1(text)') is null
     or to_regprocedure('public.bonificador_pares_v1(integer,integer)') is null then
    raise exception 'preflight: contratos atuais de Otimizador/Bonificador não foram encontrados';
  end if;

  if to_regprocedure('public.gravar_bonus(jsonb)') is null then
    raise exception 'preflight: bypass legado public.gravar_bonus(jsonb) não foi encontrado';
  end if;
  if to_regprocedure('public.gravar_bonus_sem_completude_v1(jsonb)') is not null then
    raise exception 'preflight: função preservada gravar_bonus_sem_completude_v1 já existe';
  end if;

  if to_regprocedure('public.otimizador_carta_sem_completude_v2(text)') is not null
     or to_regprocedure('public.otimizador_proxima_fila_sem_completude_v1(integer)') is not null
     or to_regprocedure('public.bonificador_carta_sem_completude_v1(text)') is not null
     or to_regprocedure('public.bonificador_pares_sem_completude_v1(integer,integer)') is not null then
    raise exception 'preflight: funções de recuperação da completude V1 já existem';
  end if;

  select string_agg(x.objeto, ', ' order by x.objeto)
    into v_missing
  from (values
    ('clube_novo.carta_jogo'),
    ('clube_novo.carta_atributo_jogo'),
    ('clube_novo.carta_corpo_jogo'),
    ('clube_novo.carta_habilidade_jogo'),
    ('clube_novo.carta_estilo_ia_jogo'),
    ('clube_novo.carta_posicao_jogo'),
    ('clube_novo.carta_posicao_principal_jogo'),
    ('clube_novo.carta_pe_jogo'),
    ('clube_novo.carta_playstyle_jogo'),
    ('clube_novo.carta_impeto_jogo'),
    ('clube_novo.build_linha_card'),
    ('clube_novo.build_otimizador'),
    ('clube_novo.build_bonificador'),
    ('clube_novo.bonificador_par'),
    ('clube_novo.aplicacao_pacote_revisao_extrator'),
    ('clube_novo.execucao_leitura_contrato'),
    ('clube_novo.contrato_leitura_jogo')
  ) x(objeto)
  where to_regclass(x.objeto) is null;
  if v_missing is not null then
    raise exception 'preflight: tabelas operacionais ausentes: %', v_missing;
  end if;

  select string_agg(x.tabela || '.' || x.coluna, ', ' order by x.tabela, x.coluna)
    into v_missing
  from (values
    ('carta_jogo','card_id'),('carta_jogo','overall'),('carta_jogo','altura'),
    ('carta_jogo','peso'),('carta_jogo','idade'),('carta_jogo','level_cap'),
    ('carta_jogo','orcamento'),('carta_jogo','cap_estimado'),('carta_jogo','grupo_id'),
    ('carta_jogo','forma'),('carta_jogo','codigo_nacionalidade'),
    ('carta_jogo','codigo_clube'),('carta_jogo','codigo_liga'),
    ('carta_jogo','tipo_carta_id'),('carta_jogo','codigo_tipo_carta_fisico'),
    ('carta_jogo','marcador_subtipo_tipo_carta'),('carta_jogo','roda_motor'),
    ('carta_jogo','pode_rodar_vinculos'),
    ('carta_atributo_jogo','codigo_atributo'),('carta_atributo_jogo','valor'),
    ('carta_corpo_jogo','codigo_corpo'),('carta_corpo_jogo','valor'),
    ('carta_habilidade_jogo','skill_id'),('carta_habilidade_jogo','ordem'),
    ('carta_estilo_ia_jogo','bit_estilo_ia'),
    ('carta_posicao_jogo','posicao_id'),('carta_posicao_jogo','nivel_aptidao'),
    ('carta_posicao_principal_jogo','posicao_id'),
    ('carta_pe_jogo','campo'),('carta_pe_jogo','valor'),
    ('carta_playstyle_jogo','slot_fisico'),('carta_playstyle_jogo','playstyle_id'),
    ('carta_playstyle_jogo','valor_raw'),
    ('carta_impeto_jogo','slot'),('carta_impeto_jogo','codigo_impeto'),
    ('carta_impeto_jogo','vaga'),('carta_impeto_jogo','condicional'),
    ('build_linha_card','card_id'),('build_linha_card','carta_versao'),
    ('build_linha_card','carta_fingerprint'),('build_linha_card','estado'),
    ('build_linha_card','pendencias'),('build_linha_card','estado_otimizador'),
    ('build_linha_card','erro_otimizador'),('build_linha_card','build_otimizador_id'),
    ('build_linha_card','build_bonificador_id'),
    ('build_otimizador','carta_versao'),('build_otimizador','carta_fingerprint'),
    ('build_bonificador','carta_versao'),('build_bonificador','carta_fingerprint')
  ) x(tabela,coluna)
  where not exists (
    select 1
    from information_schema.columns c
    where c.table_schema='clube_novo'
      and c.table_name=x.tabela
      and c.column_name=x.coluna
  );
  if v_missing is not null then
    raise exception 'preflight: colunas reais exigidas não existem: %', v_missing;
  end if;
end
$preflight$;

-- Fotografia recuperável do estado das linhas calculadas. O rollback se recusa
-- a sobrescrever trabalho novo: só restaura se o conjunto de IDs continuar igual.
create table clube_novo.migracao_completude_motor_build_snapshot_v1 as
select id, estado, pendencias, estado_otimizador, erro_otimizador
from clube_novo.build_linha_card;

alter table clube_novo.migracao_completude_motor_build_snapshot_v1
  add primary key (id),
  add column capturado_em timestamptz not null default clock_timestamp();

alter table clube_novo.migracao_completude_motor_build_snapshot_v1 enable row level security;
revoke all on table clube_novo.migracao_completude_motor_build_snapshot_v1
  from public, anon, authenticated;

-- Captura recuperável dos grants efetivos declarados da porta legada. Inclui
-- ACL padrão quando proacl é NULL, proprietário, grantor e grant option.
create table clube_novo.migracao_gravar_bonus_grant_snapshot_v1 as
select
  p.oid::regprocedure::text funcao_identidade,
  pg_get_userbyid(p.proowner) proprietario,
  pg_get_function_result(p.oid) retorno_sql,
  pg_get_userbyid(a.grantor) grantor,
  case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end grantee,
  a.privilege_type,
  a.is_grantable
from pg_proc p
join pg_namespace n on n.oid=p.pronamespace
cross join lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
where n.nspname='public' and p.oid='public.gravar_bonus(jsonb)'::regprocedure;

alter table clube_novo.migracao_gravar_bonus_grant_snapshot_v1
  add column capturado_em timestamptz not null default clock_timestamp(),
  add primary key (grantor,grantee,privilege_type);

alter table clube_novo.migracao_gravar_bonus_grant_snapshot_v1 enable row level security;
revoke all on table clube_novo.migracao_gravar_bonus_grant_snapshot_v1
  from public,anon,authenticated;

-- O nome antigo não é redirecionado. A implementação que escreve
-- clube.build fica preservada sem EXECUTE; o nome público passa a falhar com
-- mensagem explícita até existir conclusão segura em clube_novo.
alter function public.gravar_bonus(jsonb)
  rename to gravar_bonus_sem_completude_v1;

do $bloquear_gravar_bonus$
declare
  v_retorno text;
  v_role record;
  v_owner text;
  v_wrapper_owner text;
begin
  select retorno_sql,proprietario into v_retorno,v_owner
  from clube_novo.migracao_gravar_bonus_grant_snapshot_v1
  limit 1;
  if v_retorno is null or v_owner is null then
    raise exception 'snapshot de grants/retorno de gravar_bonus ficou vazio';
  end if;

  for v_role in
    select distinct grantee
    from clube_novo.migracao_gravar_bonus_grant_snapshot_v1
  loop
    execute format(
      'revoke all privileges on function public.gravar_bonus_sem_completude_v1(jsonb) from %s',
      case when v_role.grantee='PUBLIC' then 'PUBLIC' else quote_ident(v_role.grantee) end
    );
  end loop;
  execute 'revoke all privileges on function public.gravar_bonus_sem_completude_v1(jsonb) from service_role';

  execute format($ddl$
    create function public.gravar_bonus(p_linhas jsonb)
    returns %s
    language plpgsql
    security definer
    set search_path=''
    as $blocked$
    begin
      raise exception 'gravar_bonus bloqueada: destino clube.build é legado; nenhuma linha foi gravada'
        using errcode='55000';
    end
    $blocked$
  $ddl$,v_retorno);

  execute 'revoke all privileges on function public.gravar_bonus(jsonb) from PUBLIC';
  execute 'revoke all privileges on function public.gravar_bonus(jsonb) from service_role';
  execute 'revoke all privileges on function public.gravar_bonus(jsonb) from anon';
  execute 'revoke all privileges on function public.gravar_bonus(jsonb) from authenticated';
  select pg_get_userbyid(p.proowner) into v_wrapper_owner
  from pg_proc p where p.oid='public.gravar_bonus(jsonb)'::regprocedure;
  execute format(
    'revoke all privileges on function public.gravar_bonus(jsonb) from %I',v_owner
  );
  if v_wrapper_owner is distinct from v_owner then
    execute format(
      'revoke all privileges on function public.gravar_bonus(jsonb) from %I',v_wrapper_owner
    );
  end if;
  for v_role in
    select distinct grantee
    from clube_novo.migracao_gravar_bonus_grant_snapshot_v1
    where grantee<>'PUBLIC'
  loop
    execute format(
      'revoke all privileges on function public.gravar_bonus(jsonb) from %I',v_role.grantee
    );
  end loop;
end
$bloquear_gravar_bonus$;

create table clube_novo.carta_completude_motor_versao (
  versao_id bigint generated always as identity primary key,
  card_id text not null references clube_novo.carta_jogo(card_id) on delete restrict,
  regra_versao text not null check (btrim(regra_versao) <> ''),
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  execucao_id bigint not null references clube_novo.execucao_leitura_contrato(execucao_id) on delete restrict,
  aplicacao_id bigint not null references clube_novo.aplicacao_pacote_revisao_extrator(aplicacao_id) on delete restrict,
  estado_coleta text not null check (estado_coleta in ('completa','incompleta')),
  estado_resolucao text not null check (estado_resolucao in ('resolvida','com_pendencias')),
  apto_motor boolean not null,
  missing_inputs text[] not null,
  pendencias_resolucao text[] not null,
  motivos_bloqueio_motor text[] not null,
  input_fingerprint_sha256 text not null check (input_fingerprint_sha256 ~ '^[0-9a-f]{64}$'),
  cobertura_fingerprint_sha256 text not null check (cobertura_fingerprint_sha256 ~ '^[0-9a-f]{64}$'),
  completude_fingerprint_sha256 text not null check (completude_fingerprint_sha256 ~ '^[0-9a-f]{64}$'),
  fingerprint_entrada_legado_sha256 text not null check (fingerprint_entrada_legado_sha256 ~ '^[0-9a-f]{64}$'),
  validado_em timestamptz not null default clock_timestamp(),
  vigente boolean not null default false,
  invalidado_em timestamptz,
  motivo_invalidacao text,
  unique (card_id, aplicacao_id),
  check (array_position(missing_inputs, null) is null),
  check (array_position(pendencias_resolucao, null) is null),
  check (array_position(motivos_bloqueio_motor, null) is null),
  check (
    (estado_coleta='completa' and cardinality(missing_inputs)=0)
    or (estado_coleta='incompleta' and cardinality(missing_inputs)>0)
  ),
  check (
    (estado_resolucao='resolvida' and cardinality(pendencias_resolucao)=0)
    or (estado_resolucao='com_pendencias' and cardinality(pendencias_resolucao)>0)
  ),
  check (
    (apto_motor and cardinality(motivos_bloqueio_motor)=0 and estado_coleta='completa')
    or (not apto_motor and cardinality(motivos_bloqueio_motor)>0)
  ),
  check (
    (vigente and invalidado_em is null and motivo_invalidacao is null)
    or not vigente
  )
);

create unique index carta_completude_motor_uma_vigente_uidx
  on clube_novo.carta_completude_motor_versao(card_id)
  where vigente;

create index carta_completude_motor_estado_idx
  on clube_novo.carta_completude_motor_versao(apto_motor, estado_coleta, vigente, card_id);

create table clube_novo.carta_completude_motor_componente (
  versao_id bigint not null references clube_novo.carta_completude_motor_versao(versao_id) on delete cascade,
  componente text not null check (componente in (
    'dados_basicos','dimensoes','atributos','corpo','posicoes',
    'posicao_principal','habilidades','estilos_ia','pes','playstyles','impetos'
  )),
  estado_coleta text not null check (estado_coleta in (
    'conferido_com_valor','conferido_sem_valor','nao_conferido','leitura_com_problema'
  )),
  estado_resolucao text not null check (estado_resolucao in (
    'resolvido','pendencia_conhecida','nao_resolvido','nao_aplicavel',
    'orfao_catalogo_atual'
  )),
  apto_motor boolean not null,
  quantidade_valores integer check (quantidade_valores is null or quantidade_valores >= 0),
  proveniencia jsonb not null default '{}'::jsonb,
  evidencia jsonb not null default '{}'::jsonb,
  problema text,
  componente_fingerprint_sha256 text not null check (componente_fingerprint_sha256 ~ '^[0-9a-f]{64}$'),
  primary key (versao_id, componente),
  check (jsonb_typeof(proveniencia)='object'),
  check (jsonb_typeof(evidencia)='object'),
  check (
    (estado_coleta='conferido_com_valor'
      and quantidade_valores > 0 and proveniencia <> '{}'::jsonb)
    or (estado_coleta='conferido_sem_valor'
      and quantidade_valores = 0 and proveniencia <> '{}'::jsonb)
    or (estado_coleta='nao_conferido' and quantidade_valores is null)
    or (estado_coleta='leitura_com_problema'
      and nullif(btrim(problema),'') is not null)
  ),
  check (estado_coleta in ('conferido_com_valor','conferido_sem_valor') or not apto_motor),
  check (estado_resolucao not in ('nao_resolvido') or not apto_motor),
  check (
    estado_resolucao<>'orfao_catalogo_atual'
    or (
      componente='dimensoes'
      and estado_coleta in ('conferido_com_valor','conferido_sem_valor')
      and apto_motor
    )
  )
);

-- Decisão humana/política é um objeto separado da coleta. Ela não altera o
-- valor físico; apenas registra por que uma pendência conhecida pode ou não
-- bloquear o motor naquela versão.
create table clube_novo.carta_completude_motor_decisao (
  decisao_id bigint generated always as identity primary key,
  versao_id bigint not null,
  componente text not null,
  aplicacao_id bigint not null references clube_novo.aplicacao_pacote_revisao_extrator(aplicacao_id) on delete restrict,
  tipo text not null check (btrim(tipo)<>''),
  motivo text not null check (btrim(motivo)<>''),
  evidencia jsonb not null,
  decidido_em timestamptz not null default clock_timestamp(),
  unique (versao_id,componente),
  foreign key (versao_id,componente)
    references clube_novo.carta_completude_motor_componente(versao_id,componente)
    on delete cascade,
  check (jsonb_typeof(evidencia)='object')
);

alter table clube_novo.carta_completude_motor_versao enable row level security;
alter table clube_novo.carta_completude_motor_componente enable row level security;
alter table clube_novo.carta_completude_motor_decisao enable row level security;
revoke all on table
  clube_novo.carta_completude_motor_versao,
  clube_novo.carta_completude_motor_componente,
  clube_novo.carta_completude_motor_decisao
from public, anon, authenticated;
grant select on table
  clube_novo.carta_completude_motor_versao,
  clube_novo.carta_completude_motor_componente,
  clube_novo.carta_completude_motor_decisao
to service_role;

comment on table clube_novo.carta_completude_motor_versao is
  'Coleta, resolução e aptidão dos motores em estados separados. Não controla inserção, Home, box nem publicação da carta.';
comment on table clube_novo.carta_completude_motor_componente is
  'Prova por componente. Vazio conferido, resolução de catálogo e aptidão do motor são fatos distintos.';
comment on table clube_novo.carta_completude_motor_decisao is
  'Registro separado de decisão manual/política; nunca substitui a prova de coleta física.';

create view clube_novo.carta_completude_motor_atual as
select v.*
from clube_novo.carta_completude_motor_versao v
where v.vigente;

revoke all on table clube_novo.carta_completude_motor_atual
  from public, anon, authenticated;
grant select on table clube_novo.carta_completude_motor_atual to service_role;

-- JSON canônico dos insumos realmente consumidos. Campos de apresentação,
-- foto, box e publicação não entram no fingerprint do motor.
create function clube_novo.carta_input_motor_canonico_v1(p_card_id text)
returns jsonb
language sql
stable
security definer
set search_path=''
as $function$
select jsonb_build_object(
  'card_id',c.card_id,
  'dados_basicos',jsonb_build_object(
    'overall',c.overall,'altura',c.altura,'peso',c.peso,'idade',c.idade,
    'level_cap',c.level_cap,'orcamento',c.orcamento,'cap_estimado',c.cap_estimado,
    'grupo_id',c.grupo_id,'forma',c.forma,'roda_motor',c.roda_motor,
    'pode_rodar_vinculos',c.pode_rodar_vinculos
  ),
  'dimensoes',jsonb_build_object(
    'codigo_nacionalidade',c.codigo_nacionalidade,'codigo_clube',c.codigo_clube,
    'codigo_liga',c.codigo_liga,'tipo_carta_id',c.tipo_carta_id,
    'codigo_tipo_carta_fisico',c.codigo_tipo_carta_fisico,
    'marcador_subtipo_tipo_carta',c.marcador_subtipo_tipo_carta
  ),
  'atributos',coalesce((
    select jsonb_agg(jsonb_build_object(
      'codigo_atributo',x.codigo_atributo,'valor',x.valor
    ) order by x.codigo_atributo)
    from clube_novo.carta_atributo_jogo x where x.card_id=c.card_id
  ),'[]'::jsonb),
  'corpo',coalesce((
    select jsonb_agg(jsonb_build_object(
      'codigo_corpo',x.codigo_corpo,'valor',x.valor
    ) order by x.codigo_corpo)
    from clube_novo.carta_corpo_jogo x where x.card_id=c.card_id
  ),'[]'::jsonb),
  'posicoes',coalesce((
    select jsonb_agg(jsonb_build_object(
      'posicao_id',x.posicao_id,'nivel_aptidao',x.nivel_aptidao
    ) order by x.posicao_id)
    from clube_novo.carta_posicao_jogo x where x.card_id=c.card_id
  ),'[]'::jsonb),
  'posicao_principal',(
    select jsonb_build_object('posicao_id',x.posicao_id)
    from clube_novo.carta_posicao_principal_jogo x where x.card_id=c.card_id
  ),
  'habilidades',coalesce((
    select jsonb_agg(jsonb_build_object(
      'skill_id',x.skill_id,'ordem',x.ordem
    ) order by x.skill_id)
    from clube_novo.carta_habilidade_jogo x where x.card_id=c.card_id
  ),'[]'::jsonb),
  'estilos_ia',coalesce((
    select jsonb_agg(jsonb_build_object('bit_estilo_ia',x.bit_estilo_ia)
      order by x.bit_estilo_ia)
    from clube_novo.carta_estilo_ia_jogo x where x.card_id=c.card_id
  ),'[]'::jsonb),
  'pes',coalesce((
    select jsonb_agg(jsonb_build_object('campo',x.campo,'valor',x.valor)
      order by x.campo)
    from clube_novo.carta_pe_jogo x where x.card_id=c.card_id
  ),'[]'::jsonb),
  'playstyles',coalesce((
    select jsonb_agg(jsonb_build_object(
      'slot_fisico',x.slot_fisico,'playstyle_id',x.playstyle_id,'valor_raw',x.valor_raw
    ) order by x.slot_fisico)
    from clube_novo.carta_playstyle_jogo x where x.card_id=c.card_id
  ),'[]'::jsonb),
  'impetos',coalesce((
    select jsonb_agg(jsonb_build_object(
      'slot',x.slot,'codigo_impeto',x.codigo_impeto,'vaga',x.vaga,'condicional',x.condicional
    ) order by x.slot)
    from clube_novo.carta_impeto_jogo x where x.card_id=c.card_id
  ),'[]'::jsonb)
)
from clube_novo.carta_jogo c
where c.card_id=p_card_id;
$function$;

revoke all on function clube_novo.carta_input_motor_canonico_v1(text)
  from public, anon, authenticated;
grant execute on function clube_novo.carta_input_motor_canonico_v1(text) to service_role;

-- As definições atuais ficam preservadas sob nomes explícitos para rollback.
alter function public.otimizador_carta_v2(text)
  rename to otimizador_carta_sem_completude_v2;
alter function public.otimizador_proxima_fila_v1(integer)
  rename to otimizador_proxima_fila_sem_completude_v1;
alter function public.bonificador_carta_v1(text)
  rename to bonificador_carta_sem_completude_v1;
alter function public.bonificador_pares_v1(integer,integer)
  rename to bonificador_pares_sem_completude_v1;

-- Os originais só existem para compor os wrappers e permitir rollback. Nenhum
-- cliente pode contornar os novos gates chamando os nomes preservados.
revoke all on function public.otimizador_carta_sem_completude_v2(text)
  from public,anon,authenticated,service_role;
revoke all on function public.otimizador_proxima_fila_sem_completude_v1(integer)
  from public,anon,authenticated,service_role;
revoke all on function public.bonificador_carta_sem_completude_v1(text)
  from public,anon,authenticated,service_role;
revoke all on function public.bonificador_pares_sem_completude_v1(integer,integer)
  from public,anon,authenticated,service_role;

-- Registro de evidência física. O cliente informa fatos por componente; o
-- banco deriva coleta, resolução, aptidão e os fingerprints. NULL/[]/0 das
-- tabelas de dados nunca substituem a prova de que a fonte foi conferida.
create function clube_novo.registrar_completude_motor_v1(
  p_card_id text,
  p_aplicacao_id bigint,
  p_componentes jsonb
)
returns bigint
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_required constant text[] := array[
    'atributos','corpo','dados_basicos','dimensoes','estilos_ia','habilidades',
    'impetos','pes','playstyles','posicao_principal','posicoes'
  ];
  v_seen text[] := '{}'::text[];
  v_sorted text[];
  v_item jsonb;
  v_name text;
  v_collection_state text;
  v_resolution text;
  v_component_apto boolean;
  v_qty integer;
  v_problem text;
  v_app record;
  v_input jsonb;
  v_coverage jsonb;
  v_otim jsonb;
  v_bonus jsonb;
  v_missing text[];
  v_resolution_pending text[];
  v_motor_blockers text[];
  v_otim_motivos text[];
  v_bonus_faltas text[];
  v_orphan_current boolean;
  v_input_fp text;
  v_coverage_fp text;
  v_complete_fp text;
  v_legacy_fp text;
  v_collection_final text;
  v_resolution_final text;
  v_apto boolean;
  v_id bigint;
begin
  if nullif(btrim(p_card_id),'') is null then
    raise exception 'completude recusada: card_id é obrigatório';
  end if;
  if jsonb_typeof(p_componentes) is distinct from 'array' then
    raise exception 'completude recusada: componentes devem formar um array';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(p_card_id,0));

  select a.aplicacao_id,a.execucao_id,a.contrato_id,a.estado
    into v_app
  from clube_novo.aplicacao_pacote_revisao_extrator a
  where a.aplicacao_id=p_aplicacao_id;
  if v_app.aplicacao_id is null or v_app.estado<>'aplicado' then
    raise exception 'completude recusada: aplicação auditada inexistente ou não aplicada';
  end if;

  select v.versao_id into v_id
  from clube_novo.carta_completude_motor_versao v
  where v.card_id=p_card_id and v.aplicacao_id=p_aplicacao_id;
  if v_id is not null then
    return v_id;
  end if;

  for v_item in select value from jsonb_array_elements(p_componentes)
  loop
    if jsonb_typeof(v_item)<>'object' then
      raise exception 'completude recusada: componente não é objeto';
    end if;
    v_name:=nullif(btrim(v_item->>'componente'),'');
    v_collection_state:=nullif(btrim(v_item->>'estado_coleta'),'');
    v_resolution:=nullif(btrim(v_item->>'estado_resolucao'),'');
    v_problem:=nullif(btrim(v_item->>'problema'),'');
    if not (v_item ? 'apto_motor')
       or jsonb_typeof(v_item->'apto_motor') is distinct from 'boolean' then
      raise exception 'completude recusada: % exige apto_motor booleano explícito',
        coalesce(v_name,'componente desconhecido');
    end if;
    v_component_apto:=(v_item->>'apto_motor')::boolean;
    v_qty:=case when v_item ? 'quantidade_valores'
                and v_item->>'quantidade_valores' is not null
                then (v_item->>'quantidade_valores')::integer end;

    if v_name is null or not (v_name=any(v_required)) then
      raise exception 'completude recusada: componente desconhecido: %', coalesce(v_name,'NULL');
    end if;
    if v_name=any(v_seen) then
      raise exception 'completude recusada: componente duplicado: %',v_name;
    end if;
    if v_collection_state is null or v_collection_state not in (
      'conferido_com_valor','conferido_sem_valor','nao_conferido','leitura_com_problema'
    ) then
      raise exception 'completude recusada: estado de coleta inválido em %',v_name;
    end if;
    if v_resolution is null or v_resolution not in (
      'resolvido','pendencia_conhecida','nao_resolvido','nao_aplicavel',
      'orfao_catalogo_atual'
    ) then
      raise exception 'completude recusada: estado de resolução inválido em %',v_name;
    end if;
    if v_collection_state='conferido_com_valor' and (
      coalesce(v_qty,0)<=0 or coalesce(v_item->'proveniencia','{}'::jsonb)='{}'::jsonb
    ) then
      raise exception 'completude recusada: % com valor exige quantidade e proveniência',v_name;
    end if;
    if v_collection_state='conferido_sem_valor' and (
      v_qty is distinct from 0 or coalesce(v_item->'proveniencia','{}'::jsonb)='{}'::jsonb
    ) then
      raise exception 'completude recusada: % sem valor exige zero explícito e proveniência',v_name;
    end if;
    if v_collection_state='nao_conferido' and v_qty is not null then
      raise exception 'completude recusada: % não conferido não pode inventar contagem',v_name;
    end if;
    if v_collection_state='leitura_com_problema' and v_problem is null then
      raise exception 'completude recusada: % com problema exige explicação',v_name;
    end if;
    if v_collection_state not in ('conferido_com_valor','conferido_sem_valor')
       and v_component_apto then
      raise exception 'completude recusada: % não conferido não pode ficar apto ao motor',v_name;
    end if;
    if v_resolution='nao_resolvido' and v_component_apto then
      raise exception 'completude recusada: % não resolvido não pode ficar apto ao motor',v_name;
    end if;
    if v_resolution='orfao_catalogo_atual' and v_name<>'dimensoes' then
      raise exception 'completude recusada: órfão de catálogo atual só se aplica às dimensões da carta';
    end if;
    if jsonb_typeof(coalesce(v_item->'proveniencia','{}'::jsonb))<>'object'
       or jsonb_typeof(coalesce(v_item->'evidencia','{}'::jsonb))<>'object' then
      raise exception 'completude recusada: proveniência/evidência inválida em %',v_name;
    end if;
    if jsonb_typeof(v_item#>'{evidencia,decisao_motor}')='object'
       and coalesce(v_item#>'{evidencia,decisao_motor}','{}'::jsonb)<>'{}'::jsonb
       and (
         nullif(btrim(v_item#>>'{evidencia,decisao_motor,tipo}'),'') is null
         or nullif(btrim(v_item#>>'{evidencia,decisao_motor,motivo}'),'') is null
       ) then
      raise exception 'completude recusada: decisão de % exige tipo e motivo',v_name;
    end if;
    if v_resolution in ('pendencia_conhecida','orfao_catalogo_atual')
       and v_component_apto
       and (
         jsonb_typeof(v_item#>'{evidencia,decisao_motor}') is distinct from 'object'
         or coalesce(v_item#>'{evidencia,decisao_motor}','{}'::jsonb)='{}'::jsonb
         or nullif(btrim(v_item#>>'{evidencia,decisao_motor,tipo}'),'') is null
         or nullif(btrim(v_item#>>'{evidencia,decisao_motor,motivo}'),'') is null
       ) then
      raise exception 'completude recusada: % com pendência não bloqueante exige evidencia.decisao_motor',v_name;
    end if;
    v_seen:=array_append(v_seen,v_name);
  end loop;

  select array_agg(x order by x) into v_sorted from unnest(v_seen) x;
  if v_sorted is distinct from v_required then
    raise exception 'completude recusada: componentes obrigatórios divergentes; recebidos=%',v_sorted;
  end if;

  v_input:=clube_novo.carta_input_motor_canonico_v1(p_card_id);
  if v_input is null then
    raise exception 'completude recusada: carta inexistente em clube_novo.carta_jogo';
  end if;

  select jsonb_agg(value order by value->>'componente')
    into v_coverage
  from jsonb_array_elements(p_componentes);

  v_otim:=public.otimizador_carta_sem_completude_v2(p_card_id);
  v_bonus:=public.bonificador_carta_sem_completude_v1(p_card_id);

  select coalesce(array_agg(m order by ord),'{}'::text[])
    into v_otim_motivos
  from jsonb_array_elements_text(coalesce(v_otim#>'{gate,motivos}','[]'::jsonb))
       with ordinality q(m,ord);

  select coalesce(array_agg(m order by ord),'{}'::text[])
    into v_bonus_faltas
  from jsonb_array_elements_text(coalesce(v_bonus->'falta_o_que','[]'::jsonb))
       with ordinality q(m,ord);

  select coalesce(bool_or(
    (x->>'componente')='dimensoes'
    and (x->>'estado_resolucao')='orfao_catalogo_atual'
    and (x->>'apto_motor')::boolean
  ),false)
    into v_orphan_current
  from jsonb_array_elements(p_componentes) x;

  -- missing_inputs descreve somente aquilo que não foi coletado. Pendência
  -- de catálogo e bloqueio computacional ficam em campos separados.
  select coalesce(array_agg(distinct motivo order by motivo),'{}'::text[])
    into v_missing
  from (
    select 'coleta:'||(x->>'componente')||':'||(x->>'estado_coleta') motivo
    from jsonb_array_elements(p_componentes) x
    where x->>'estado_coleta' not in ('conferido_com_valor','conferido_sem_valor')
  ) faltas;

  select coalesce(array_agg(distinct motivo order by motivo),'{}'::text[])
    into v_resolution_pending
  from (
    select 'resolucao:'||(x->>'componente')||':'||(x->>'estado_resolucao') motivo
    from jsonb_array_elements(p_componentes) x
    where x->>'estado_resolucao' not in ('resolvido','nao_aplicavel')
    union all select 'otimizador:'||m from unnest(v_otim_motivos) m
    union all select 'otimizador:contrato_sem_carta' where v_otim is null
    union all select 'bonificador:'||m from unnest(v_bonus_faltas) m
    union all select 'bonificador:contrato_sem_carta' where v_bonus is null
  ) pendencias;

  select coalesce(array_agg(distinct motivo order by motivo),'{}'::text[])
    into v_motor_blockers
  from (
    select m motivo from unnest(v_missing) m
    union all
    select 'componente:'||(x->>'componente')||':nao_apto_motor'
    from jsonb_array_elements(p_componentes) x
    where not (x->>'apto_motor')::boolean
    union all
    select 'otimizador:'||m
    from unnest(v_otim_motivos) m
    where not (
      v_orphan_current and m in (
        'carta.roda_motor=false','carta.pode_rodar_vinculos=false',
        'clube_bloqueado','liga_bloqueada'
      )
    )
    union all select 'otimizador:contrato_sem_carta' where v_otim is null
    union all select 'bonificador:'||m from unnest(v_bonus_faltas) m
    union all select 'bonificador:contrato_sem_carta' where v_bonus is null
  ) bloqueios;

  v_input_fp:=encode(extensions.digest(v_input::text,'sha256'),'hex');
  v_coverage_fp:=encode(extensions.digest(v_coverage::text,'sha256'),'hex');
  v_legacy_fp:=encode(extensions.digest(coalesce(v_otim,'null'::jsonb)::text,'sha256'),'hex');
  v_collection_final:=case when cardinality(v_missing)=0 then 'completa' else 'incompleta' end;
  v_resolution_final:=case when cardinality(v_resolution_pending)=0
                           then 'resolvida' else 'com_pendencias' end;
  v_apto:=cardinality(v_motor_blockers)=0;
  v_complete_fp:=encode(extensions.digest(
    jsonb_build_object(
      'regra','completude-motores-carta-v1',
      'contrato_id',v_app.contrato_id,
      'input_fingerprint',v_input_fp,
      'cobertura_fingerprint',v_coverage_fp,
      'estado_coleta',v_collection_final,
      'estado_resolucao',v_resolution_final,
      'apto_motor',v_apto,
      'motivos_bloqueio_motor',to_jsonb(v_motor_blockers)
    )::text,
    'sha256'
  ),'hex');

  update clube_novo.carta_completude_motor_versao
  set vigente=false,
      invalidado_em=clock_timestamp(),
      motivo_invalidacao='nova_validacao_fisica'
  where card_id=p_card_id and vigente;

  insert into clube_novo.carta_completude_motor_versao(
    card_id,regra_versao,contrato_id,execucao_id,aplicacao_id,
    estado_coleta,estado_resolucao,apto_motor,missing_inputs,
    pendencias_resolucao,motivos_bloqueio_motor,
    input_fingerprint_sha256,cobertura_fingerprint_sha256,completude_fingerprint_sha256,
    fingerprint_entrada_legado_sha256,vigente
  ) values(
    p_card_id,'completude-motores-carta-v1',v_app.contrato_id,v_app.execucao_id,
    p_aplicacao_id,v_collection_final,v_resolution_final,v_apto,v_missing,
    v_resolution_pending,v_motor_blockers,v_input_fp,v_coverage_fp,v_complete_fp,
    v_legacy_fp,true
  ) returning versao_id into v_id;

  insert into clube_novo.carta_completude_motor_componente(
    versao_id,componente,estado_coleta,estado_resolucao,apto_motor,
    quantidade_valores,proveniencia,evidencia,problema,componente_fingerprint_sha256
  )
  select v_id,
    x->>'componente',x->>'estado_coleta',x->>'estado_resolucao',
    (x->>'apto_motor')::boolean,
    case when x ? 'quantidade_valores' and x->>'quantidade_valores' is not null
         then (x->>'quantidade_valores')::integer end,
    coalesce(x->'proveniencia','{}'::jsonb),
    coalesce(x->'evidencia','{}'::jsonb),
    nullif(btrim(x->>'problema'),''),
    encode(extensions.digest(jsonb_build_object(
      'componente',x->>'componente','estado_coleta',x->>'estado_coleta',
      'estado_resolucao',x->>'estado_resolucao',
      'apto_motor',(x->>'apto_motor')::boolean,
      'quantidade_valores',x->'quantidade_valores',
      'proveniencia',coalesce(x->'proveniencia','{}'::jsonb),
      'evidencia',coalesce(x->'evidencia','{}'::jsonb),
      'problema',x->'problema'
    )::text,'sha256'),'hex')
  from jsonb_array_elements(p_componentes) x;

  insert into clube_novo.carta_completude_motor_decisao(
    versao_id,componente,aplicacao_id,tipo,motivo,evidencia
  )
  select v_id,x->>'componente',p_aplicacao_id,
         x#>>'{evidencia,decisao_motor,tipo}',
         x#>>'{evidencia,decisao_motor,motivo}',
         x#>'{evidencia,decisao_motor}'
  from jsonb_array_elements(p_componentes) x
  where jsonb_typeof(x#>'{evidencia,decisao_motor}')='object'
    and coalesce(x#>'{evidencia,decisao_motor}','{}'::jsonb)<>'{}'::jsonb;

  -- Um resultado terminal da base continua historicamente reconhecido quando
  -- o fingerprint antigo ainda corresponde exatamente ao mesmo input. Qualquer
  -- linha pendente, divergente ou incompleta vira trabalho novo.
  update clube_novo.build_linha_card l
  set estado='invalida',
      pendencias=case
        when 'completude_motor_desatualizada'=any(l.pendencias) then l.pendencias
        else array_append(l.pendencias,'completude_motor_desatualizada') end,
      estado_otimizador=case
        when l.estado_otimizador in ('bloqueado','interrompido') then l.estado_otimizador
        else 'bloqueado' end,
      erro_otimizador=coalesce(l.erro_otimizador,'completude física da carta mudou; exige novo trabalho')
  where l.card_id=p_card_id
    and l.estado<>'invalida'
    and (l.carta_versao,l.carta_fingerprint) is distinct from
        ('completude-motores-carta-v1',v_complete_fp)
    and not (
      v_apto
      and l.estado in ('pronta','publicada')
      and l.carta_fingerprint=v_legacy_fp
      and l.build_otimizador_id is not null
      and l.build_bonificador_id is not null
      and exists (
        select 1 from clube_novo.build_otimizador o
        where o.id=l.build_otimizador_id and o.carta_fingerprint=v_legacy_fp
      )
      and exists (
        select 1 from clube_novo.build_bonificador b
        where b.id=l.build_bonificador_id and b.carta_fingerprint=v_legacy_fp
      )
    );

  return v_id;
end
$function$;

revoke all on function clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)
  from public, anon, authenticated;
grant execute on function clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)
  to service_role;

-- Planejamento incremental. O seed inicial passa todos os card_ids uma vez;
-- depois o Extrator passa somente IDs novos ou tocados pelo pacote aplicado.
-- A função calcula o hash dentro do banco e nunca confia em um hash enviado
-- pelo cliente. Pendência conhecida com input idêntico vira revisão manual,
-- não upsert automático repetido a cada varredura.
create function clube_novo.planejar_completude_motor_v1(p_card_ids text[])
returns table(
  card_id text,
  acao text,
  motivo text,
  input_fingerprint_sha256 text,
  versao_id bigint,
  completude_fingerprint_sha256 text
)
language sql
stable
security definer
set search_path=''
as $function$
with ids as (
  select x.card_id,min(x.ord) ord
  from unnest(coalesce(p_card_ids,'{}'::text[])) with ordinality x(card_id,ord)
  where nullif(btrim(x.card_id),'') is not null
  group by x.card_id
), entrada as (
  select ids.card_id,ids.ord,ci.input_json,
         case when ci.input_json is not null then
           encode(extensions.digest(ci.input_json::text,'sha256'),'hex')
         end input_fp
  from ids
  left join lateral (
    select clube_novo.carta_input_motor_canonico_v1(ids.card_id) input_json
  ) ci on true
), atual as (
  select e.*,v.versao_id,v.input_fingerprint_sha256 atual_input_fp,
         v.completude_fingerprint_sha256,v.apto_motor
  from entrada e
  left join clube_novo.carta_completude_motor_versao v
    on v.card_id=e.card_id and v.vigente
)
select a.card_id,
  case
    when a.input_json is null then 'erro'
    when a.versao_id is null then 'materializar'
    when a.input_fp is distinct from a.atual_input_fp then 'materializar'
    when not a.apto_motor then 'revisao_manual'
    else 'nenhuma'
  end acao,
  case
    when a.input_json is null then 'carta_ausente'
    when a.versao_id is null then 'seed_ou_carta_nova_sem_validacao'
    when a.input_fp is distinct from a.atual_input_fp then 'input_motor_alterado'
    when not a.apto_motor then 'input_igual_com_bloqueio_ja_registrado'
    else 'input_igual_e_validacao_vigente'
  end motivo,
  a.input_fp,a.versao_id,a.completude_fingerprint_sha256
from atual a
order by a.ord;
$function$;

revoke all on function clube_novo.planejar_completude_motor_v1(text[])
  from public,anon,authenticated;
grant execute on function clube_novo.planejar_completude_motor_v1(text[])
  to service_role;

-- Contrato de carta do Otimizador: mantém o payload atual e acrescenta o gate
-- físico. O vazio legítimo não gera falta; a ausência de versão vigente gera.
create function public.otimizador_carta_v2(p_card_id text)
returns jsonb
language plpgsql
stable
security definer
set search_path=''
as $function$
declare
  v_base jsonb;
  v_comp clube_novo.carta_completude_motor_versao%rowtype;
  v_motivos text[];
  v_orphan_current boolean;
begin
  v_base:=public.otimizador_carta_sem_completude_v2(p_card_id);
  if v_base is null then return null; end if;

  select * into v_comp
  from clube_novo.carta_completude_motor_versao
  where card_id=p_card_id and vigente;

  select exists(
    select 1
    from clube_novo.carta_completude_motor_componente c
    where c.versao_id=v_comp.versao_id
      and c.componente='dimensoes'
      and c.estado_resolucao='orfao_catalogo_atual'
      and c.apto_motor
  ) into v_orphan_current;

  select coalesce(array_agg(distinct motivo order by motivo),'{}'::text[])
    into v_motivos
  from (
    select m motivo
    from jsonb_array_elements_text(coalesce(v_base#>'{gate,motivos}','[]'::jsonb)) m
    where not (
      v_orphan_current and m in (
        'carta.roda_motor=false','carta.pode_rodar_vinculos=false',
        'clube_bloqueado','liga_bloqueada'
      )
    )
    union all
    select 'completude_motor_sem_validacao' where v_comp.versao_id is null
    union all
    select 'completude:'||m
    from unnest(coalesce(v_comp.motivos_bloqueio_motor,'{}'::text[])) m
  ) q;

  return (v_base-'gate') || jsonb_build_object(
    'gate',coalesce(v_base->'gate','{}'::jsonb) || jsonb_build_object(
      'pode_rodar',coalesce(v_comp.apto_motor,false) and cardinality(v_motivos)=0,
      'motivos',to_jsonb(v_motivos)
    ),
    'completude_motor',jsonb_build_object(
      'estado_coleta',coalesce(v_comp.estado_coleta,'incompleta'),
      'estado_resolucao',coalesce(v_comp.estado_resolucao,'com_pendencias'),
      'apto_motor',coalesce(v_comp.apto_motor,false),
      'missing_inputs',to_jsonb(coalesce(v_comp.missing_inputs,array['completude_motor_sem_validacao']::text[])),
      'pendencias_resolucao',to_jsonb(coalesce(v_comp.pendencias_resolucao,'{}'::text[])),
      'motivos_bloqueio_motor',to_jsonb(coalesce(v_comp.motivos_bloqueio_motor,array['completude_motor_sem_validacao']::text[])),
      'regra_versao',v_comp.regra_versao,
      'validated_at',v_comp.validado_em,
      'fingerprint',v_comp.completude_fingerprint_sha256
    )
  );
end
$function$;

-- Contrato de carta do Bonificador com a mesma prova vigente.
create function public.bonificador_carta_v1(p_card_id text)
returns jsonb
language plpgsql
stable
security definer
set search_path=''
as $function$
declare
  v_base jsonb;
  v_comp clube_novo.carta_completude_motor_versao%rowtype;
  v_faltas text[];
begin
  v_base:=public.bonificador_carta_sem_completude_v1(p_card_id);
  if v_base is null then return null; end if;

  select * into v_comp
  from clube_novo.carta_completude_motor_versao
  where card_id=p_card_id and vigente;

  select coalesce(array_agg(distinct motivo order by motivo),'{}'::text[])
    into v_faltas
  from (
    select m motivo from jsonb_array_elements_text(coalesce(v_base->'falta_o_que','[]'::jsonb)) m
    union all
    select 'completude_motor_sem_validacao' where v_comp.versao_id is null
    union all
    select 'completude:'||m
    from unnest(coalesce(v_comp.motivos_bloqueio_motor,'{}'::text[])) m
  ) q;

  return v_base || jsonb_build_object(
    'pode_rodar',coalesce(v_comp.apto_motor,false) and cardinality(v_faltas)=0,
    'falta_o_que',to_jsonb(v_faltas),
    'contrato_versao','bonificador-regua-v1+bonificador-carta-v1',
    'carta_versao',v_comp.regra_versao,
    'carta_fingerprint',v_comp.completude_fingerprint_sha256,
    'completude_motor',jsonb_build_object(
      'estado_coleta',coalesce(v_comp.estado_coleta,'incompleta'),
      'estado_resolucao',coalesce(v_comp.estado_resolucao,'com_pendencias'),
      'apto_motor',coalesce(v_comp.apto_motor,false),
      'missing_inputs',to_jsonb(coalesce(v_comp.missing_inputs,array['completude_motor_sem_validacao']::text[])),
      'pendencias_resolucao',to_jsonb(coalesce(v_comp.pendencias_resolucao,'{}'::text[])),
      'motivos_bloqueio_motor',to_jsonb(coalesce(v_comp.motivos_bloqueio_motor,array['completude_motor_sem_validacao']::text[])),
      'validated_at',v_comp.validado_em,
      'fingerprint',v_comp.completude_fingerprint_sha256
    )
  );
end
$function$;

-- A fila V1 lia clube.fila, que é histórica e não é autoridade operacional.
-- Ela fica explicitamente fechada. As filas V12 em build_linha_card passam
-- pelo contrato de carta e pelo trigger universal abaixo.
create function public.otimizador_proxima_fila_v1(p_limite integer default 200)
returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
begin
  raise exception 'fila V1 desativada: clube.fila é histórica; use a fila V12 selada em clube_novo.build_linha_card';
end
$function$;

-- Fila do Bonificador: somente pares cuja carta continua pronta no instante da
-- consulta. O contrato de carta faz a segunda conferência antes do cálculo.
create function public.bonificador_pares_v1(
  p_limit integer default 1000,
  p_offset integer default 0
)
returns table(card_id text, funcao_id bigint, funcao_codigo text)
language sql
stable
security definer
set search_path=''
as $function$
  select p.card_id,p.funcao_id,f.codigo_legado
  from clube_novo.bonificador_par p
  join clube_novo.funcao_sistema f
    on f.id=p.funcao_id and f.pode_rodar
  join clube_novo.carta_completude_motor_versao cm
    on cm.card_id=p.card_id and cm.vigente and cm.apto_motor
  cross join lateral (select public.bonificador_carta_v1(p.card_id) pacote) g
  where coalesce((g.pacote->>'pode_rodar')::boolean,false)
  order by p.card_id,p.funcao_id
  limit least(greatest(coalesce(p_limit,1000),1),5000)
  offset greatest(coalesce(p_offset,0),0);
$function$;

revoke all on function public.otimizador_carta_v2(text) from public,anon,authenticated;
revoke all on function public.otimizador_proxima_fila_v1(integer) from public,anon,authenticated;
revoke all on function public.bonificador_carta_v1(text) from public,anon,authenticated;
revoke all on function public.bonificador_pares_v1(integer,integer) from public,anon,authenticated;
grant execute on function public.otimizador_carta_v2(text) to service_role;
grant execute on function public.otimizador_proxima_fila_v1(integer) to service_role;
grant execute on function public.bonificador_carta_v1(text) to service_role;
grant execute on function public.bonificador_pares_v1(integer,integer) to service_role;

-- Gate universal da fila e da conclusão. Ele cobre produtores atuais e futuros
-- porque mora na única linha operacional dos motores, não só numa UI/RPC.
create function clube_novo.validar_build_linha_completude_motor_v1()
returns trigger
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_comp clube_novo.carta_completude_motor_versao%rowtype;
  v_otim clube_novo.build_otimizador%rowtype;
  v_bonus clube_novo.build_bonificador%rowtype;
  v_gate jsonb;
begin
  if new.estado='invalida' then
    if new.estado_otimizador is null
       or new.estado_otimizador not in ('bloqueado','interrompido') then
      raise exception 'motor recusado: linha inválida precisa permanecer bloqueada/interrompida';
    end if;
    if tg_op='INSERT' and (
      new.build_otimizador_id is not null or new.build_bonificador_id is not null
    ) then
      raise exception 'motor recusado: nova linha inválida não pode receber resultado';
    end if;
    if tg_op='UPDATE' and (
      new.build_otimizador_id is distinct from old.build_otimizador_id
      or new.build_bonificador_id is distinct from old.build_bonificador_id
    ) then
      raise exception 'motor recusado: linha inválida não pode ligar novo resultado';
    end if;
    return new;
  end if;

  select * into v_comp
  from clube_novo.carta_completude_motor_versao
  where card_id=new.card_id and vigente and apto_motor;
  if v_comp.versao_id is null then
    raise exception 'motor recusado: carta % sem completude vigente e apta',new.card_id;
  end if;

  if tg_op='INSERT' then
    new.carta_versao:=v_comp.regra_versao;
    new.carta_fingerprint:=v_comp.completude_fingerprint_sha256;
  elsif old.estado in ('pronta','publicada')
     and old.carta_fingerprint=v_comp.fingerprint_entrada_legado_sha256
     and new.card_id is not distinct from old.card_id
     and new.carta_versao is not distinct from old.carta_versao
     and new.carta_fingerprint is not distinct from old.carta_fingerprint
     and new.build_otimizador_id is not distinct from old.build_otimizador_id
     and new.build_bonificador_id is not distinct from old.build_bonificador_id
     and new.estado_otimizador is not distinct from old.estado_otimizador
     and new.estado in ('pronta','publicada') then
    -- Publicar/despublicar um resultado terminal antigo idêntico não é uma
    -- nova execução. Qualquer mudança de motor cai nas conferências abaixo.
    v_gate:=public.otimizador_carta_v2(new.card_id);
    if not coalesce((v_gate#>>'{gate,pode_rodar}')::boolean,false) then
      raise exception 'resultado histórico recusado: gate atual do Otimizador fechou';
    end if;
    v_gate:=public.bonificador_carta_v1(new.card_id);
    if not coalesce((v_gate->>'pode_rodar')::boolean,false) then
      raise exception 'resultado histórico recusado: gate atual do Bonificador fechou';
    end if;
    return new;
  elsif new.carta_versao is distinct from v_comp.regra_versao
     or new.carta_fingerprint is distinct from v_comp.completude_fingerprint_sha256 then
    raise exception 'motor recusado: versão/fingerprint da carta % ficou obsoleto',new.card_id;
  end if;

  if new.estado_otimizador in ('processando','concluido') then
    v_gate:=public.otimizador_carta_v2(new.card_id);
    if not coalesce((v_gate#>>'{gate,pode_rodar}')::boolean,false) then
      raise exception 'Otimizador recusado: gate atual da carta % fechou: %',
        new.card_id,v_gate#>'{gate,motivos}';
    end if;
  end if;

  if new.build_otimizador_id is not null then
    select * into v_otim from clube_novo.build_otimizador where id=new.build_otimizador_id;
    if v_otim.id is null
       or v_otim.carta_versao is distinct from v_comp.regra_versao
       or v_otim.carta_fingerprint is distinct from v_comp.completude_fingerprint_sha256 then
      raise exception 'conclusão recusada: resultado do Otimizador não usa a completude vigente';
    end if;
  end if;

  if new.build_bonificador_id is not null then
    v_gate:=public.bonificador_carta_v1(new.card_id);
    if not coalesce((v_gate->>'pode_rodar')::boolean,false) then
      raise exception 'Bonificador recusado: gate atual da carta % fechou: %',
        new.card_id,v_gate->'falta_o_que';
    end if;
    select * into v_bonus from clube_novo.build_bonificador where id=new.build_bonificador_id;
    if v_bonus.id is null
       or v_bonus.carta_versao is distinct from v_comp.regra_versao
       or v_bonus.carta_fingerprint is distinct from v_comp.completude_fingerprint_sha256 then
      raise exception 'conclusão recusada: resultado do Bonificador não usa a completude vigente';
    end if;
  end if;

  return new;
end
$function$;

-- Invalidação imediata: nenhuma mutação de insumo pode deixar um selo antigo
-- parecendo atual. Não bloqueia a própria mutação da carta.
create function clube_novo.invalidar_completude_motor_por_insumo_v1()
returns trigger
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_card_id text;
begin
  v_card_id:=case when tg_op='DELETE' then old.card_id else new.card_id end;

  update clube_novo.carta_completude_motor_versao
  set vigente=false,
      invalidado_em=clock_timestamp(),
      motivo_invalidacao='insumo_motor_alterado:'||tg_table_name
  where card_id=v_card_id and vigente;

  update clube_novo.build_linha_card l
  set estado='invalida',
      pendencias=case
        when 'completude_motor_desatualizada'=any(l.pendencias) then l.pendencias
        else array_append(l.pendencias,'completude_motor_desatualizada') end,
      estado_otimizador=case
        when l.estado_otimizador in ('bloqueado','interrompido') then l.estado_otimizador
        else 'bloqueado' end,
      erro_otimizador=coalesce(l.erro_otimizador,'insumo físico mudou; exige nova validação e novo trabalho')
  where l.card_id=v_card_id and l.estado<>'invalida';

  return case when tg_op='DELETE' then old else new end;
end
$function$;

create trigger build_linha_completude_motor_v1
before insert or update of
  card_id,carta_versao,carta_fingerprint,estado,estado_otimizador,
  build_otimizador_id,build_bonificador_id
on clube_novo.build_linha_card
for each row execute function clube_novo.validar_build_linha_completude_motor_v1();

create trigger carta_jogo_invalidar_completude_motor_v1
after insert or delete or update of
  overall,altura,peso,idade,level_cap,orcamento,cap_estimado,grupo_id,forma,
  codigo_nacionalidade,codigo_clube,codigo_liga,tipo_carta_id,
  codigo_tipo_carta_fisico,marcador_subtipo_tipo_carta,roda_motor,pode_rodar_vinculos
on clube_novo.carta_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();

create trigger carta_atributo_invalidar_completude_motor_v1
after insert or update or delete on clube_novo.carta_atributo_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();
create trigger carta_corpo_invalidar_completude_motor_v1
after insert or update or delete on clube_novo.carta_corpo_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();
create trigger carta_habilidade_invalidar_completude_motor_v1
after insert or update or delete on clube_novo.carta_habilidade_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();
create trigger carta_estilo_ia_invalidar_completude_motor_v1
after insert or update or delete on clube_novo.carta_estilo_ia_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();
create trigger carta_posicao_invalidar_completude_motor_v1
after insert or update or delete on clube_novo.carta_posicao_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();
create trigger carta_posicao_principal_invalidar_completude_motor_v1
after insert or update or delete on clube_novo.carta_posicao_principal_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();
create trigger carta_pe_invalidar_completude_motor_v1
after insert or update or delete on clube_novo.carta_pe_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();
create trigger carta_playstyle_invalidar_completude_motor_v1
after insert or update or delete on clube_novo.carta_playstyle_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();
create trigger carta_impeto_invalidar_completude_motor_v1
after insert or update or delete on clube_novo.carta_impeto_jogo
for each row execute function clube_novo.invalidar_completude_motor_por_insumo_v1();

revoke all on function clube_novo.validar_build_linha_completude_motor_v1()
  from public,anon,authenticated;
revoke all on function clube_novo.invalidar_completude_motor_por_insumo_v1()
  from public,anon,authenticated;
grant execute on function clube_novo.validar_build_linha_completude_motor_v1() to service_role;
grant execute on function clube_novo.invalidar_completude_motor_por_insumo_v1() to service_role;

do $readback$
declare
  v_n bigint;
  v_role record;
  v_can boolean;
begin
  if to_regclass('clube_novo.carta_completude_motor_versao') is null
     or to_regclass('clube_novo.carta_completude_motor_componente') is null
     or to_regclass('clube_novo.carta_completude_motor_decisao') is null
     or to_regclass('clube_novo.migracao_gravar_bonus_grant_snapshot_v1') is null
     or to_regclass('clube_novo.carta_completude_motor_atual') is null then
    raise exception 'readback: objetos de completude ausentes';
  end if;
  if to_regprocedure('public.otimizador_carta_v2(text)') is null
     or to_regprocedure('public.bonificador_carta_v1(text)') is null
     or to_regprocedure('public.otimizador_proxima_fila_v1(integer)') is null
     or to_regprocedure('public.bonificador_pares_v1(integer,integer)') is null
     or to_regprocedure('clube_novo.planejar_completude_motor_v1(text[])') is null then
    raise exception 'readback: contratos públicos protegidos ausentes';
  end if;
  if not has_function_privilege('service_role','clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)','EXECUTE')
     or has_function_privilege('anon','clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)','EXECUTE')
     or has_function_privilege('authenticated','clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)','EXECUTE') then
    raise exception 'readback: privilégios do registrador estão incorretos';
  end if;
  if to_regprocedure('public.gravar_bonus(jsonb)') is null
     or to_regprocedure('public.gravar_bonus_sem_completude_v1(jsonb)') is null
     or pg_get_functiondef('public.gravar_bonus(jsonb)'::regprocedure)
        not like '%gravar_bonus bloqueada:%nenhuma linha foi gravada%' then
    raise exception 'readback: bypass gravar_bonus não ficou explicitamente bloqueado';
  end if;
  if has_function_privilege('service_role','public.gravar_bonus(jsonb)','EXECUTE')
     or has_function_privilege('service_role','public.gravar_bonus_sem_completude_v1(jsonb)','EXECUTE')
     or has_function_privilege('anon','public.gravar_bonus(jsonb)','EXECUTE')
     or has_function_privilege('authenticated','public.gravar_bonus(jsonb)','EXECUTE') then
    raise exception 'readback: role de runtime ainda pode executar o bypass gravar_bonus';
  end if;
  select count(*) into v_n
  from pg_proc p
  cross join lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
  where p.oid in (
    'public.gravar_bonus(jsonb)'::regprocedure,
    'public.gravar_bonus_sem_completude_v1(jsonb)'::regprocedure
  ) and a.privilege_type='EXECUTE';
  if v_n<>0 then
    raise exception 'readback: ainda existem % grants EXECUTE declarados nas portas gravar_bonus',v_n;
  end if;
  for v_role in
    select distinct grantee
    from clube_novo.migracao_gravar_bonus_grant_snapshot_v1
    where grantee<>'PUBLIC' and grantee<>
      (select proprietario from clube_novo.migracao_gravar_bonus_grant_snapshot_v1 limit 1)
  loop
    if exists(select 1 from pg_roles where rolname=v_role.grantee) then
      select has_function_privilege(v_role.grantee,'public.gravar_bonus(jsonb)','EXECUTE')
          or has_function_privilege(v_role.grantee,'public.gravar_bonus_sem_completude_v1(jsonb)','EXECUTE')
        into v_can;
      if v_can then
        raise exception 'readback: grant capturado de % ainda alcança gravar_bonus',v_role.grantee;
      end if;
    end if;
  end loop;
  if has_function_privilege('service_role','public.otimizador_carta_sem_completude_v2(text)','EXECUTE')
     or has_function_privilege('service_role','public.otimizador_proxima_fila_sem_completude_v1(integer)','EXECUTE')
     or has_function_privilege('service_role','public.bonificador_carta_sem_completude_v1(text)','EXECUTE')
     or has_function_privilege('service_role','public.bonificador_pares_sem_completude_v1(integer,integer)','EXECUTE') then
    raise exception 'readback: contrato preservado pode contornar o gate';
  end if;
  select count(*) into v_n
  from pg_trigger t
  join pg_class c on c.oid=t.tgrelid
  join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='clube_novo' and not t.tgisinternal
    and t.tgname in (
      'build_linha_completude_motor_v1','carta_jogo_invalidar_completude_motor_v1',
      'carta_atributo_invalidar_completude_motor_v1','carta_corpo_invalidar_completude_motor_v1',
      'carta_habilidade_invalidar_completude_motor_v1','carta_estilo_ia_invalidar_completude_motor_v1',
      'carta_posicao_invalidar_completude_motor_v1','carta_posicao_principal_invalidar_completude_motor_v1',
      'carta_pe_invalidar_completude_motor_v1','carta_playstyle_invalidar_completude_motor_v1',
      'carta_impeto_invalidar_completude_motor_v1'
    );
  if v_n<>11 then
    raise exception 'readback: esperados 11 gates/invalidações; encontrados %',v_n;
  end if;
  if exists(
    select 1 from clube_novo.carta_completude_motor_versao
    where vigente and apto_motor and (
      estado_coleta<>'completa' or cardinality(missing_inputs)<>0
      or cardinality(motivos_bloqueio_motor)<>0
    )
  ) then
    raise exception 'readback: versão apta com coleta/bloqueios incompatíveis';
  end if;
  if exists(
    select 1
    from clube_novo.carta_completude_motor_versao v
    left join lateral (
      select count(*) n
      from clube_novo.carta_completude_motor_componente c
      where c.versao_id=v.versao_id
    ) q on true
    where q.n<>11
  ) then
    raise exception 'readback: versão sem os 11 componentes obrigatórios';
  end if;
end
$readback$;
