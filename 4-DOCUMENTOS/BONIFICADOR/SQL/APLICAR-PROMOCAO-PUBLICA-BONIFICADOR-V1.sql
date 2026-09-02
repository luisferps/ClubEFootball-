-- Promove somente linhas de teste já seladas pelos dois motores.
-- Não calcula nem altera resultados; registra somente a proveniência da promoção.
begin;

create table clube_novo.bonificador_lote_publicacao_v1 (
  id uuid primary key default extensions.gen_random_uuid(),
  contrato text not null check (contrato = 'bonificador_promocao_publicacao_v1'),
  estado text not null check (estado in ('concluido', 'revertido')),
  linhas integer not null check (linhas >= 0),
  fingerprint text not null unique check (fingerprint ~ '^[0-9a-f]{64}$'),
  proveniencia jsonb not null check (jsonb_typeof(proveniencia) = 'object'),
  criado_em timestamp with time zone not null default clock_timestamp(),
  concluido_em timestamp with time zone
);

alter table clube_novo.bonificador_lote_publicacao_v1 enable row level security;
revoke all on clube_novo.bonificador_lote_publicacao_v1 from public, anon, authenticated;
grant select on clube_novo.bonificador_lote_publicacao_v1 to service_role;
comment on table clube_novo.bonificador_lote_publicacao_v1 is
  'Lote de proveniencia da promocao autorizada de resultados ja calculados. Nao e fila nem inicia motor.';

alter table clube_novo.build_linha_card
  add column bonificador_lote_publicacao_id uuid;
alter table clube_novo.build_linha_card
  add constraint build_linha_card_bonificador_lote_publicacao_v1_fk
  foreign key (bonificador_lote_publicacao_id)
  references clube_novo.bonificador_lote_publicacao_v1(id);
alter table clube_novo.build_linha_card
  drop constraint build_linha_teste_campos_v1_check;
alter table clube_novo.build_linha_card
  add constraint build_linha_teste_campos_v2_check check (
    (execucao_tipo = 'producao'
      and lote_teste_id is null
      and lote_teste_semente is null
      and lote_teste_fingerprint is null
      and amostra_ordem is null
      and sorteada_em is null
      and (lote_producao_id is not null or bonificador_lote_publicacao_id is not null))
    or
    (execucao_tipo = 'teste_isolado'
      and lote_teste_id is not null
      and lote_teste_semente is not null
      and btrim(lote_teste_semente) <> ''
      and lote_teste_fingerprint ~ '^[0-9a-f]{64}$'
      and amostra_ordem between 1 and 100
      and sorteada_em is not null
      and lote_producao_id is null
      and bonificador_lote_publicacao_id is null)
  );

create table clube_novo.bonificador_promocao_publicacao_snapshot_v1 (
  linha_id bigint primary key references clube_novo.build_linha_card(id),
  build_otimizador_id bigint not null references clube_novo.build_otimizador(id),
  build_bonificador_id bigint not null references clube_novo.build_bonificador(id),
  promovida_em timestamp with time zone not null,
  promocao_fingerprint text not null unique,
  selo_final_fingerprint text not null,
  pontuacao_final_candidata numeric not null,
  anterior_execucao_tipo text not null,
  anterior_lote_teste_id uuid,
  anterior_lote_teste_semente text,
  anterior_lote_teste_fingerprint text,
  anterior_amostra_ordem smallint,
  anterior_sorteada_em timestamp with time zone,
  anterior_pendencias text[] not null,
  anterior_publicada_em timestamp with time zone,
  anterior_publicacao_fingerprint text,
  anterior_bonificador_lote_publicacao_id uuid,
  lote_promocao_id uuid not null references clube_novo.bonificador_lote_publicacao_v1(id),
  evidencia jsonb not null,
  criado_em timestamp with time zone not null default clock_timestamp()
);

alter table clube_novo.bonificador_promocao_publicacao_snapshot_v1 enable row level security;
revoke all on clube_novo.bonificador_promocao_publicacao_snapshot_v1 from public, anon, authenticated;
grant select on clube_novo.bonificador_promocao_publicacao_snapshot_v1 to service_role;
comment on table clube_novo.bonificador_promocao_publicacao_snapshot_v1 is
  'Snapshot imutavel da promocao autorizada de resultados de teste selados. Serve para auditoria e rollback; nao e fonte operacional.';

do $$
declare
  v_previsto integer;
  v_snapshot integer;
  v_atualizadas integer;
  v_lote_id uuid;
  v_lote_fingerprint text;
begin
  perform pg_advisory_xact_lock(hashtextextended('bonificador_promocao_publicacao_v1', 0));

  select count(*) into v_previsto
  from clube_novo.build_pontuacao_final_v1 f
  join clube_novo.build_linha_card l on l.id = f.linha_id
  where f.estado_final = 'bloqueada_lote_de_teste'
    and f.build_otimizador_id is not null
    and f.build_bonificador_id is not null
    and f.pontuacao_final_candidata is not null
    and f.selo_final_fingerprint is not null
    and l.lote_teste_id is not null
    and l.pendencias @> array['teste_nao_publicado']::text[]
    and l.publicada_em is null;
  if v_previsto <> 613 then
    raise exception 'promocao V1 interrompida: esperadas 613 linhas seladas, encontradas %', v_previsto;
  end if;

  v_lote_fingerprint := encode(extensions.digest(convert_to(jsonb_build_object(
    'contrato', 'bonificador_promocao_publicacao_v1',
    'linhas', v_previsto,
    'origem', 'teste_validado_com_dois_motores'
  )::text, 'UTF8'), 'sha256'), 'hex');
  insert into clube_novo.bonificador_lote_publicacao_v1 (
    contrato, estado, linhas, fingerprint, proveniencia, concluido_em
  ) values (
    'bonificador_promocao_publicacao_v1', 'concluido', v_previsto, v_lote_fingerprint,
    jsonb_build_object('origem', 'lote_teste_validado', 'regras',
      jsonb_build_array('dois_resultados', 'selos_validos', 'paridade', 'sem_bloqueio_factual')),
    transaction_timestamp()
  ) returning id into v_lote_id;

  with candidatas as materialized (
    select
      l.id as linha_id, l.build_otimizador_id, l.build_bonificador_id,
      l.execucao_tipo, l.lote_teste_id, l.lote_teste_semente,
      l.lote_teste_fingerprint, l.amostra_ordem, l.sorteada_em,
      l.pendencias, l.publicada_em, l.publicacao_fingerprint, l.bonificador_lote_publicacao_id,
      f.card_id, f.funcao_id, f.posicao_id, f.pontuacao_final_candidata,
      f.selo_final_fingerprint, f.otimizador_resultado_fingerprint,
      f.bonificador_resultado_fingerprint
    from clube_novo.build_linha_card l
    join clube_novo.build_pontuacao_final_v1 f on f.linha_id = l.id
    where f.estado_final = 'bloqueada_lote_de_teste'
      and f.build_otimizador_id is not null
      and f.build_bonificador_id is not null
      and f.pontuacao_final_candidata is not null
      and f.selo_final_fingerprint is not null
      and l.lote_teste_id is not null
      and l.pendencias @> array['teste_nao_publicado']::text[]
      and l.publicada_em is null
    for update of l
  )
  insert into clube_novo.bonificador_promocao_publicacao_snapshot_v1 (
    linha_id, build_otimizador_id, build_bonificador_id, promovida_em,
    promocao_fingerprint, selo_final_fingerprint, pontuacao_final_candidata,
    anterior_execucao_tipo, anterior_lote_teste_id, anterior_lote_teste_semente,
    anterior_lote_teste_fingerprint, anterior_amostra_ordem, anterior_sorteada_em,
    anterior_pendencias, anterior_publicada_em, anterior_publicacao_fingerprint,
    anterior_bonificador_lote_publicacao_id, lote_promocao_id,
    evidencia
  )
  select
    c.linha_id, c.build_otimizador_id, c.build_bonificador_id, transaction_timestamp(),
    encode(extensions.digest(convert_to(jsonb_build_object(
      'contrato', 'bonificador-promocao-publicacao-v1',
      'linha_id', c.linha_id, 'selo_final', c.selo_final_fingerprint
    )::text, 'UTF8'), 'sha256'), 'hex'),
    c.selo_final_fingerprint, c.pontuacao_final_candidata,
    c.execucao_tipo, c.lote_teste_id, c.lote_teste_semente,
    c.lote_teste_fingerprint, c.amostra_ordem, c.sorteada_em,
    c.pendencias, c.publicada_em, c.publicacao_fingerprint,
    c.bonificador_lote_publicacao_id, v_lote_id,
    jsonb_build_object(
      'contrato', 'bonificador-promocao-publicacao-v1',
      'card_id', c.card_id, 'funcao_id', c.funcao_id, 'posicao_id', c.posicao_id,
      'otimizador_resultado_fingerprint', c.otimizador_resultado_fingerprint,
      'bonificador_resultado_fingerprint', c.bonificador_resultado_fingerprint
    )
  from candidatas c;
  get diagnostics v_snapshot = row_count;

  if v_snapshot <> 613 then
    raise exception 'promocao V1 interrompida: esperadas 613 linhas seladas, encontradas %', v_snapshot;
  end if;

  update clube_novo.build_linha_card l
     set execucao_tipo = 'producao',
         lote_teste_id = null,
         lote_teste_semente = null,
         lote_teste_fingerprint = null,
         amostra_ordem = null,
         sorteada_em = null,
         pendencias = array_remove(l.pendencias, 'teste_nao_publicado'),
         publicada_em = s.promovida_em,
         publicacao_fingerprint = s.selo_final_fingerprint,
         bonificador_lote_publicacao_id = s.lote_promocao_id,
         atualizado_em = s.promovida_em
    from clube_novo.bonificador_promocao_publicacao_snapshot_v1 s
   where l.id = s.linha_id;
  get diagnostics v_atualizadas = row_count;

  if v_atualizadas <> v_snapshot then
    raise exception 'promocao V1 interrompida: snapshot=% atualizadas=%', v_snapshot, v_atualizadas;
  end if;
end
$$;

notify pgrst, 'reload schema';
commit;
