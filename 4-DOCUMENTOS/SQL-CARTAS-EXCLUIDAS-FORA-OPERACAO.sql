create or replace view clube_novo.carta_operacional_v1 as select * from clube_novo.carta_jogo where jogador_indisponivel is not true and tipo_carta_id is distinct from 'player_delete_list';
comment on view clube_novo.carta_operacional_v1 is 'Fonte de levantamentos operacionais: cartas excluidas nao sao pendencias. Reentrada somente por nova extracao.';
revoke all on clube_novo.carta_operacional_v1 from public,anon,authenticated;
CREATE OR REPLACE FUNCTION public.otimizador_producao_criar_lote_integral_v5(p_lote_id uuid, p_formula_fingerprint text, p_motor_versao text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_formula constant text:='a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2';
  v_regua jsonb; v_contrato_fp text; v_fingerprint text;
  v_total integer:=0; v_condicionais integer:=0; v_inseridas integer:=0;
begin
  if p_lote_id is null or p_formula_fingerprint<>v_formula
     or p_motor_versao is distinct from 'otimizador-fila-producao-v3-local-20260909-habilidades-v12' then
    raise exception 'criação integral recusada: selo de fórmula ou versão local inválidos';
  end if;
  if exists(
    select 1 from clube_novo.otimizador_lote_producao_v3 where tipo_lote='integral'
  ) then
    raise exception 'criação integral recusada: já existe lote integral V5; a recuperação exige decisão explícita';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean,false) then
    raise exception 'criação integral recusada: gate da régua do Otimizador está fechado';
  end if;
  v_contrato_fp:=clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);

  select count(*) into v_total
  from clube_novo.carta_operacional_v1 c
  join clube_novo.otimizador_prioridade_orcamento_v1 pr on pr.card_id=c.card_id and pr.prioridade_grupo is not null
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  if v_total=0 then
    raise exception 'criação integral recusada: não há candidata básica elegível';
  end if;

  select count(*) into v_condicionais
  from clube_novo.carta_operacional_v1 c
  join clube_novo.otimizador_prioridade_orcamento_v1 pr on pr.card_id=c.card_id and pr.prioridade_grupo is not null
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );

  v_fingerprint:=encode(extensions.digest(convert_to(
    'preparando:'||p_lote_id::text||':'||v_formula||':'||v_contrato_fp||':'||p_motor_versao,
    'UTF8'),'sha256'),'hex');

  insert into clube_novo.otimizador_lote_producao_v3(
    id,tipo_lote,estado,formula_fingerprint,contrato_fingerprint,motor_versao,
    regua_snapshot,fingerprint,cards,linhas,preparo_total,preparo_concluido,
    excluidas_incompletas,excluidas_impeto_condicional,excluidas_sem_linha,pode_publicar
  ) values (
    p_lote_id,'integral','preparando',v_formula,v_contrato_fp,p_motor_versao,
    v_regua,v_fingerprint,0,0,v_total,0,0,v_condicionais,0,false
  );

  insert into clube_novo.otimizador_lote_producao_candidata_v5(
    lote_id,card_id,ordem_candidata,overall_snapshot,carta_versao_snapshot
  )
  select p_lote_id,c.card_id,
         row_number() over(order by pr.prioridade_grupo,c.overall DESC NULLS FIRST,c.card_id collate "C")::bigint,
         c.overall::integer,coalesce(c.extraido_em::text,'')
  from clube_novo.carta_operacional_v1 c
  join clube_novo.otimizador_prioridade_orcamento_v1 pr on pr.card_id=c.card_id and pr.prioridade_grupo is not null
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  get diagnostics v_inseridas=row_count;
  if v_inseridas<>v_total then
    raise exception 'criação integral recusada: fotografia de candidatas não foi preservada (% de %)',v_inseridas,v_total;
  end if;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
  values(p_lote_id,'preparo_integral_criado',jsonb_build_object(
    'candidatas_basicas',v_total,
    'excluidas_impeto_condicional',v_condicionais,
    'ordem','prioridade_orcamento_v1',
    'preparo','somente snapshots e linhas; nenhum cálculo foi iniciado',
    'pode_publicar',false
  ));
  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$;
CREATE OR REPLACE FUNCTION public.otimizador_producao_criar_lote_integral_v6(p_lote_id uuid, p_formula_fingerprint text, p_motor_versao text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_formula constant text:='a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2';
  v_regua jsonb; v_contrato_fp text; v_fingerprint text;
  v_total integer:=0; v_condicionais integer:=0; v_inseridas integer:=0;
begin
  if p_lote_id is null or p_formula_fingerprint<>v_formula
     or p_motor_versao is distinct from 'otimizador-fila-producao-v3-local-20260909-habilidades-v12' then
    raise exception 'criação integral recusada: selo de fórmula ou versão local inválidos';
  end if;
  if exists(
    select 1 from clube_novo.otimizador_lote_producao_v3 l
    where l.tipo_lote='integral'
      and not exists(select 1 from clube_novo.otimizador_lote_aposentado_v1 a where a.lote_id=l.id)
  ) then
    raise exception 'criação integral recusada: já existe lote integral vivo; aposente-o antes';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean,false) then
    raise exception 'criação integral recusada: gate da régua do Otimizador está fechado';
  end if;
  v_contrato_fp:=clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);

  select count(*) into v_total
  from clube_novo.carta_operacional_v1 c
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and not exists(select 1 from clube_novo.carta_impeto_jogo ci
                   where ci.card_id=c.card_id and coalesce(ci.condicional,false));
  if v_total=0 then
    raise exception 'criação integral recusada: não há candidata básica elegível';
  end if;

  select count(*) into v_condicionais
  from clube_novo.carta_operacional_v1 c
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and exists(select 1 from clube_novo.carta_impeto_jogo ci
               where ci.card_id=c.card_id and coalesce(ci.condicional,false));

  v_fingerprint:=encode(extensions.digest(convert_to(
    'preparando:'||p_lote_id::text||':'||v_formula||':'||v_contrato_fp||':'||p_motor_versao,
    'UTF8'),'sha256'),'hex');

  insert into clube_novo.otimizador_lote_producao_v3(
    id,tipo_lote,estado,formula_fingerprint,contrato_fingerprint,motor_versao,
    regua_snapshot,fingerprint,cards,linhas,preparo_total,preparo_concluido,
    excluidas_incompletas,excluidas_impeto_condicional,excluidas_sem_linha,pode_publicar
  ) values (
    p_lote_id,'integral','preparando',v_formula,v_contrato_fp,p_motor_versao,
    v_regua,v_fingerprint,0,0,v_total,0,0,v_condicionais,0,false
  );

  insert into clube_novo.otimizador_lote_producao_candidata_v5(
    lote_id,card_id,ordem_candidata,overall_snapshot,carta_versao_snapshot
  )
  select p_lote_id,c.card_id,
         row_number() over(
           order by case when coalesce(c.orcamento,0) > 0 then 0 else 1 end,
                    c.overall desc nulls last,
                    c.card_id collate "C")::bigint,
         c.overall::integer, coalesce(c.extraido_em::text,'')
  from clube_novo.carta_operacional_v1 c
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and not exists(select 1 from clube_novo.carta_impeto_jogo ci
                   where ci.card_id=c.card_id and coalesce(ci.condicional,false));
  get diagnostics v_inseridas=row_count;
  if v_inseridas<>v_total then
    raise exception 'criação integral recusada: fotografia de candidatas não foi preservada (% de %)',v_inseridas,v_total;
  end if;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
  values(p_lote_id,'preparo_integral_criado',jsonb_build_object(
    'candidatas_basicas',v_total,
    'excluidas_impeto_condicional',v_condicionais,
    'ordem','bloco1_com_orcamento_depois_bloco2_sem_orcamento_cada_um_por_overall_desc',
    'preparo','somente snapshots e linhas; nenhum cálculo foi iniciado',
    'pode_publicar',false
  ));
  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$;
create or replace view clube_novo.pendencia_nivel_operacional_v1 as
select b.lote_producao_id,b.card_id,c.nome,count(*) as linhas
from clube_novo.build_linha_card b join clube_novo.carta_operacional_v1 c using(card_id)
where b.execucao_tipo='producao' and b.estado='pendente' and b.estado_otimizador='interrompido'
and not exists(select 1 from clube_novo.otimizador_lote_aposentado_v1 a where a.lote_id=b.lote_producao_id)
and (not exists(select 1 from clube_novo.carta_nivel_evidencia_v1 e where e.card_id=b.card_id) or c.level_cap is null or c.orcamento is null or c.level_cap<1 or c.orcamento<>2*c.level_cap-2)
group by b.lote_producao_id,b.card_id,c.nome;
revoke all on clube_novo.pendencia_nivel_operacional_v1 from public,anon,authenticated;
