-- Bonificador V11: ativação de estilo somente pela posição compatível do jogo.
-- Mantém corpo, pé ruim, IA, moldes, pesos e ordem da fila.
-- Os resultados V10 já calculados são reaproveitados por cópia selada: somente
-- bonus_playstyle_1/2, bonus_total e fingerprints derivados são substituídos.

begin;

select pg_advisory_xact_lock(hashtextextended('bonificador_estilo_posicao_v11',0));

do $guard$
declare
  v_lote clube_novo.bonificador_correcao_lote_v1%rowtype;
begin
  select * into v_lote
  from clube_novo.bonificador_correcao_lote_v1
  where id='0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid
  for update;

  if v_lote.id is null
     or v_lote.motor_versao<>'v10-0409-fisico-regra-aprovada-v1'
     or v_lote.formula_fingerprint<>'756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b' then
    raise exception 'V11: lote V10 esperado não encontrado ou já alterado';
  end if;

  if exists (
    select 1 from clube_novo.bonificador_correcao_item_v1
    where lote_id=v_lote.id and estado_item='processando'
      and atualizado_em>clock_timestamp()-interval '15 minutes'
  ) then
    raise exception 'V11: há worker recente; a migração não pode concorrer com ele';
  end if;
end
$guard$;

-- A única reserva pendurada está sem atividade há horas. Ela volta à mesma
-- posição lógica da fila; nenhuma linha pronta é reaberta.
update clube_novo.bonificador_correcao_item_v1
set estado_item='pendente',iniciado_em=null,erro=null,atualizado_em=clock_timestamp()
where lote_id='0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid
  and estado_item='processando'
  and atualizado_em<=clock_timestamp()-interval '15 minutes';

update clube_novo.bonificador_correcao_lote_v1
set estado='pausado',pausado_em=clock_timestamp(),atualizado_em=clock_timestamp(),
    observacao=coalesce(observacao,'')||
      ' | V11: estilo corrigido por posição; resultados preparados reaproveitados.'
where id='0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid;

-- A revisão de orçamento substituiu linhas antigas por linhas novas. A fila
-- passa a conter somente as linhas produtivas vigentes: remove ancestrais e
-- inclui suas substitutas sem alterar a ordem grupo/overall/card/função/posição.
delete from clube_novo.bonificador_correcao_item_v1 i
where i.lote_id='0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid
  and exists (
    select 1 from clube_novo.build_linha_card l
    where l.id=i.build_linha_card_id
      and (l.estado='invalida' or exists(
        select 1 from clube_novo.orcamento_revisao_linha_v1 r
        where r.linha_anterior_id=l.id
      ))
  );

alter table clube_novo.bonificador_correcao_item_v1
  disable trigger bonificador_correcao_inserir_finalizar_automatico_v1;

insert into clube_novo.bonificador_correcao_item_v1(
  lote_id,build_linha_card_id,build_bonificador_id_anterior,
  build_bonificador_id_novo,estado_item,preparado_em,
  prioridade_grupo,prioridade_overall,prioridade_card_id,
  prioridade_funcao_id,prioridade_posicao_id
)
select '0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid,l.id,null,
  case when b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
         and b.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
       then b.id end,
  case when b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
         and b.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
       then 'preparado' else 'pendente' end,
  case when b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
         and b.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
       then clock_timestamp() end,
  case when l.criado_em>=timestamptz '2026-09-04 22:00:00+00'
             and c.chave_tipo_carta in ('Any2W:360','Any2W:361')
       then 0 else 1 end::smallint,
  c.overall,l.card_id,l.funcao_id,l.posicao_id
from clube_novo.build_linha_card l
join clube_novo.carta_jogo c on c.card_id=l.card_id
left join clube_novo.build_bonificador b on b.id=l.build_bonificador_id
where l.execucao_tipo='producao' and l.lote_teste_id is null
  and not (l.pendencias @> array['teste_nao_publicado'::text])
  and c.roda_motor is true and coalesce(c.jogador_indisponivel,false)=false
  and l.carta_versao=c.extraido_em::text and l.estado<>'invalida'
  and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=l.id)
  and not exists(
    select 1 from clube_novo.bonificador_correcao_item_v1 i
    where i.lote_id='0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid
      and i.build_linha_card_id=l.id
  );

alter table clube_novo.bonificador_correcao_item_v1
  enable trigger bonificador_correcao_inserir_finalizar_automatico_v1;

with resumo as (
  select count(*)::integer quantidade,
    encode(extensions.digest(convert_to(string_agg(
      i.build_linha_card_id::text||':'||l.card_id||':'||l.funcao_id::text||':'||l.posicao_id::text,
      ',' order by i.prioridade_grupo,i.prioridade_overall desc nulls last,
        i.prioridade_card_id,i.prioridade_funcao_id,i.prioridade_posicao_id,i.build_linha_card_id
    ),'UTF8'),'sha256'),'hex') fingerprint
  from clube_novo.bonificador_correcao_item_v1 i
  join clube_novo.build_linha_card l on l.id=i.build_linha_card_id
  where i.lote_id='0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid
)
update clube_novo.bonificador_correcao_lote_v1 lo
set snapshot_quantidade=r.quantidade,snapshot_fingerprint=r.fingerprint,
    atualizado_em=clock_timestamp()
from resumo r
where lo.id='0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid;

-- Seis associações que existiam no molde interno, mas não ativam o estilo no
-- jogo. Elas permanecem registradas; apenas deixam de ligar bônus.
update clube_novo.bonificador_regra_playstyle
set da_bonus=false
where id in (9,11,12,18,67,68);

do $rules$
begin
  if (select count(*) from clube_novo.bonificador_regra_playstyle
      where id in (9,11,12,18,67,68) and da_bonus=false)<>6 then
    raise exception 'V11: as seis ativações oficiais não foram corrigidas';
  end if;
end
$rules$;

alter table clube_novo.bonificador_correcao_lote_v1
  drop constraint bonificador_correcao_lote_v1_motor_versao_check,
  drop constraint bonificador_correcao_lote_v1_formula_fingerprint_check;

update clube_novo.bonificador_correcao_lote_v1
set motor_versao='v11-0709-estilo-posicao-oficial-v1',
    formula_fingerprint='2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879',
    atualizado_em=clock_timestamp()
where id='0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid;

alter table clube_novo.bonificador_correcao_lote_v1
  add constraint bonificador_correcao_lote_v1_motor_versao_check
    check (motor_versao='v11-0709-estilo-posicao-oficial-v1'),
  add constraint bonificador_correcao_lote_v1_formula_fingerprint_check
    check (formula_fingerprint='2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879');

-- Atualiza de forma mecânica todos os gates que selam a identidade vigente.
-- O corpo das funções e suas permissões permanecem iguais.
do $contracts$
declare
  r record;
  v_def text;
begin
  for r in
    select p.oid
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where p.prokind='f' and n.nspname in ('public','clube_novo')
      and (pg_get_functiondef(p.oid) like '%v10-0409-fisico-regra-aprovada-v1%'
        or pg_get_functiondef(p.oid) like '%756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b%')
  loop
    v_def:=pg_get_functiondef(r.oid);
    v_def:=replace(v_def,
      'v10-0409-fisico-regra-aprovada-v1',
      'v11-0709-estilo-posicao-oficial-v1');
    v_def:=replace(v_def,
      '756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b',
      '2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879');
    v_def:=replace(v_def,'fisico-v10-regra-aprovada','fisico-v10-estilo-posicao-v11');
    execute v_def;
  end loop;
end
$contracts$;

-- O editor de builds mostrava a mesma dependência incorreta da função.
do $editor$
declare
  v_oid oid;
  v_def text;
begin
  select p.oid into v_oid
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='build_editor' and p.proname='avaliar_v1'
    and pg_get_function_identity_arguments(p.oid)='p_entrada jsonb';
  v_def:=pg_get_functiondef(v_oid);
  if position('playstyle_id=main_style and posicao_id=pos and funcao_id=fid and da_bonus' in v_def)=0 then
    raise exception 'V11: condição antiga do Editor Build não foi localizada';
  end if;
  v_def:=replace(v_def,
    'playstyle_id=main_style and posicao_id=pos and funcao_id=fid and da_bonus',
    'playstyle_id=main_style and posicao_id=pos and da_bonus');
  execute v_def;
end
$editor$;

-- Durante a migração em massa, os dois gatilhos de finalização apenas deixam a
-- fila durável ser preenchida. Fora dessa transação, continuam automáticos.
do $trigger_guards$
declare
  v_def text;
begin
  v_def:=pg_get_functiondef('clube_novo.disparar_finalizacao_linha_v1()'::regprocedure);
  v_def:=replace(v_def,E'AS $function$\nbegin\n',
    E'AS $function$\nbegin\n  if current_setting(''clube_novo.migracao_estilo_v11'',true)=''1'' then return new; end if;\n');
  execute v_def;

  v_def:=pg_get_functiondef('clube_novo.disparar_finalizacao_correcao_v1()'::regprocedure);
  v_def:=replace(v_def,E'begin\n  if new.estado_item',
    E'begin\n  if current_setting(''clube_novo.migracao_estilo_v11'',true)=''1'' then return new; end if;\n  if new.estado_item');
  execute v_def;
end
$trigger_guards$;

create or replace function public.bonificador_migrar_estilo_v11_tick_v1(
  p_limite integer default 500
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_limite integer:=least(greatest(coalesce(p_limite,500),1),2000);
  v_regua jsonb;
  v_inseridos integer:=0;
  v_tocados integer:=0;
  v_restantes bigint:=0;
begin
  perform pg_advisory_xact_lock(hashtextextended('bonificador_estilo_posicao_v11_tick',0));
  perform set_config('clube_novo.migracao_estilo_v11','1',true);
  v_regua:=public.bonificador_regua_v3();
  if v_regua->>'formula_fingerprint'<>'2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879'
     or not coalesce((v_regua->>'pode_rodar')::boolean,false) then
    raise exception 'V11: régua nova não está apta';
  end if;

  drop table if exists pg_temp._bonus_v11_alvos;
  create temporary table _bonus_v11_alvos on commit drop as
  with referencias as (
    select l.build_bonificador_id as antigo_id,l.id as linha_id,l.card_id,l.posicao_id
    from clube_novo.build_linha_card l
    where l.build_bonificador_id is not null and l.estado<>'invalida'
      and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=l.id)
    union all
    select i.build_bonificador_id_novo,l.id,l.card_id,l.posicao_id
    from clube_novo.bonificador_correcao_item_v1 i
    join clube_novo.build_linha_card l on l.id=i.build_linha_card_id
    where i.build_bonificador_id_novo is not null and l.estado<>'invalida'
      and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=l.id)
  ), unicas as (
    select distinct on (r.antigo_id)
      r.antigo_id,r.linha_id,r.card_id,r.posicao_id
    from referencias r
    join clube_novo.build_bonificador b on b.id=r.antigo_id
    where b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
      and b.formula_fingerprint='756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b'
    order by r.antigo_id,r.linha_id
    limit v_limite
  ), estilos as (
    select u.*,
      case when s.slot='ofensivo' then 1 else 2 end as slot_principal,
      nullif(max(cp.playstyle_id) filter(where cp.slot_fisico=1),0) as estilo_1,
      nullif(max(cp.playstyle_id) filter(where cp.slot_fisico=2),0) as estilo_2
    from unicas u
    join clube_novo.bonificador_posicao_slot s on s.posicao_id=u.posicao_id
    left join clube_novo.carta_playstyle_jogo cp on cp.card_id=u.card_id
    group by u.antigo_id,u.linha_id,u.card_id,u.posicao_id,s.slot
  ), papeis as (
    select e.*,
      case
        when slot_principal=1 and estilo_1 is not null then 1
        when slot_principal=2 and estilo_2 is not null then 2
        when slot_principal=1 and estilo_2 is not null then 2
        when slot_principal=2 and estilo_1 is not null then 1
      end as slot_dono,
      case
        when slot_principal=1 and estilo_1 is not null then estilo_1
        when slot_principal=2 and estilo_2 is not null then estilo_2
        when slot_principal=1 then estilo_2 else estilo_1
      end as estilo_dono,
      case when slot_principal=1 and estilo_1 is not null then 2
           when slot_principal=2 and estilo_2 is not null then 1 end as slot_outro,
      case when slot_principal=1 and estilo_1 is not null then estilo_2
           when slot_principal=2 and estilo_2 is not null then estilo_1 end as estilo_outro
    from estilos e
  ), valores as (
    select p.*,
      (select valor from clube_novo.bonificador_parametro where codigo='estilo_ativo')::numeric as principal,
      (select valor from clube_novo.bonificador_parametro where codigo='estilo_ativo_secundario')::numeric as secundario
    from papeis p
  ), parcelas as (
    select v.*,
      round(
        case when v.slot_dono=1 and exists(
          select 1 from clube_novo.bonificador_regra_playstyle r
          where r.playstyle_id=v.estilo_dono and r.posicao_id=v.posicao_id and r.da_bonus
        ) then v.principal else 0 end
        + case when v.slot_outro=1 and exists(
          select 1 from clube_novo.bonificador_regra_playstyle r
          where r.playstyle_id=v.estilo_outro and r.posicao_id=v.posicao_id and r.da_bonus
        ) then v.secundario else 0 end,4) as novo_1,
      round(
        case when v.slot_dono=2 and exists(
          select 1 from clube_novo.bonificador_regra_playstyle r
          where r.playstyle_id=v.estilo_dono and r.posicao_id=v.posicao_id and r.da_bonus
        ) then v.principal else 0 end
        + case when v.slot_outro=2 and exists(
          select 1 from clube_novo.bonificador_regra_playstyle r
          where r.playstyle_id=v.estilo_outro and r.posicao_id=v.posicao_id and r.da_bonus
        ) then v.secundario else 0 end,4) as novo_2
    from valores v
  )
  select p.*,
    encode(extensions.digest(convert_to(jsonb_build_object(
      'migracao','bonificador-estilo-posicao-v11','resultado_anterior',b.resultado_fingerprint,
      'linha_id',p.linha_id,'bonus_playstyle_1',p.novo_1,
      'bonus_playstyle_2',p.novo_2,'regua',v_regua->>'contrato_fingerprint',
      'formula','2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879'
    )::text,'UTF8'),'sha256'),'hex') as novo_fingerprint,
    null::bigint as novo_id
  from parcelas p join clube_novo.build_bonificador b on b.id=p.antigo_id;

  get diagnostics v_tocados=row_count;
  if v_tocados=0 then
    select count(*) into v_restantes
    from clube_novo.build_bonificador b
    where b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
      and (exists(select 1 from clube_novo.build_linha_card l where l.build_bonificador_id=b.id)
        or exists(select 1 from clube_novo.bonificador_correcao_item_v1 i where i.build_bonificador_id_novo=b.id));
    return jsonb_build_object('ok',true,'processados',0,'restantes',v_restantes);
  end if;

  insert into clube_novo.build_bonificador(
    bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,
    bonus_ia,bonus_outros,bonus_total,contrato_versao,contrato_fingerprint,
    carta_versao,carta_fingerprint,formula_fingerprint,resultado_fingerprint,
    concluido_em,bonus_fisico_detalhe,criado_em,motor_versao,b_corpo,b_pe_ruim,
    b_estilo,b_total,faltou,corpo_soma,corpo_pct,entrada_bonificador_fingerprint
  )
  select b.bonus_pe,b.bonus_fisico_total,b.bonus_posicao,t.novo_1,t.novo_2,
    b.bonus_ia,b.bonus_outros,
    round(b.bonus_total-coalesce(b.bonus_playstyle_1,0)-coalesce(b.bonus_playstyle_2,0)+t.novo_1+t.novo_2,4),
    'bonificador-regua-v3',v_regua->>'contrato_fingerprint',b.carta_versao,b.carta_fingerprint,
    '2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879',
    t.novo_fingerprint,clock_timestamp(),b.bonus_fisico_detalhe,clock_timestamp(),
    'v11-0709-estilo-posicao-oficial-v1',b.b_corpo,b.b_pe_ruim,
    round(t.novo_1+t.novo_2,4),
    round(b.b_total-coalesce(b.b_estilo,0)+t.novo_1+t.novo_2,4),
    b.faltou,b.corpo_soma,b.corpo_pct,b.entrada_bonificador_fingerprint
  from _bonus_v11_alvos t
  join clube_novo.build_bonificador b on b.id=t.antigo_id
  on conflict(resultado_fingerprint) do nothing;
  get diagnostics v_inseridos=row_count;

  update _bonus_v11_alvos t set novo_id=b.id
  from clube_novo.build_bonificador b
  where b.resultado_fingerprint=t.novo_fingerprint;
  if exists(select 1 from _bonus_v11_alvos where novo_id is null) then
    raise exception 'V11: resultado novo não localizado após insert';
  end if;

  update clube_novo.bonificador_correcao_item_v1 i
  set build_bonificador_id_novo=t.novo_id,atualizado_em=clock_timestamp()
  from _bonus_v11_alvos t where i.build_bonificador_id_novo=t.antigo_id;

  update clube_novo.bonificador_correcao_item_v1 i
  set build_bonificador_id_anterior=t.novo_id,atualizado_em=clock_timestamp()
  from _bonus_v11_alvos t where i.build_bonificador_id_anterior=t.antigo_id;

  update clube_novo.bonificador_lote_item_v1 i
  set build_bonificador_id=t.novo_id
  from _bonus_v11_alvos t where i.build_bonificador_id=t.antigo_id;

  update clube_novo.bonificador_promocao_publicacao_snapshot_v1 s
  set build_bonificador_id=t.novo_id
  from _bonus_v11_alvos t where s.build_bonificador_id=t.antigo_id;

  -- Esta troca dispara a finalização normal somente nas linhas já vinculadas.
  update clube_novo.build_linha_card l
  set build_bonificador_id=t.novo_id,
      bonificador_motor_versao='v11-0709-estilo-posicao-oficial-v1',
      bonificador_contrato_versao='bonificador-regua-v3',
      snapshot_bonificador_fingerprint=t.novo_fingerprint,
      atualizado_em=clock_timestamp()
  from _bonus_v11_alvos t where l.build_bonificador_id=t.antigo_id;

  -- Linhas que usam staging também entram na finalização durável, sem esperar
  -- o Bonificador recalcular corpo/pé/IA.
  insert into clube_novo.build_finalizacao_fila_v1(
    linha_id,estado,prioridade,overall_origem,tentativas,origem_ultima,
    motivo,proxima_tentativa_em,concluido_em,publicacao_fingerprint,atualizado_em
  )
  select distinct t.linha_id,'aguardando',
    coalesce(i.prioridade_grupo::integer,10),c.overall,0,
    'migracao_estilo_posicao_v11',null::text,clock_timestamp(),
    null::timestamptz,null::text,clock_timestamp()
  from _bonus_v11_alvos t
  join clube_novo.carta_jogo c on c.card_id=t.card_id
  left join clube_novo.bonificador_correcao_item_v1 i
    on i.build_linha_card_id=t.linha_id
   and i.lote_id='0ddaa775-24c1-4293-86ca-77fe698aa044'::uuid
  on conflict(linha_id) do update set
    estado='aguardando',prioridade=least(clube_novo.build_finalizacao_fila_v1.prioridade,excluded.prioridade),
    overall_origem=excluded.overall_origem,origem_ultima=excluded.origem_ultima,
    motivo=null,proxima_tentativa_em=clock_timestamp(),concluido_em=null,
    publicacao_fingerprint=null,atualizado_em=clock_timestamp();

  select count(*) into v_restantes
  from clube_novo.build_bonificador b
  where b.motor_versao='v10-0409-fisico-regra-aprovada-v1'
    and (exists(select 1 from clube_novo.build_linha_card l where l.build_bonificador_id=b.id)
      or exists(select 1 from clube_novo.bonificador_correcao_item_v1 i where i.build_bonificador_id_novo=b.id));

  return jsonb_build_object('ok',true,'processados',v_tocados,
    'inseridos',v_inseridos,'restantes',v_restantes);
end
$function$;

revoke all on function public.bonificador_migrar_estilo_v11_tick_v1(integer)
  from public,anon,authenticated;
grant execute on function public.bonificador_migrar_estilo_v11_tick_v1(integer)
  to postgres,service_role;

commit;
