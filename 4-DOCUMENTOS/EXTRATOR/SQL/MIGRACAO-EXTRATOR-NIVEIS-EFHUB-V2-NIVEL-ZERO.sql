-- V2: level_cap=0 significa nível ainda desconhecido e precisa entrar na coleta.
-- A função também deixa de declarar catálogo concluído quando restam cartas
-- elegíveis sem evidência, mantendo a operação fechada em caso de recusa.

begin;

create or replace function public.extrator_efhub_planejar_lote_v1(p_limite integer default 1000)
returns jsonb language plpgsql security definer set search_path='' as $fn$
declare v_lote uuid; v_total integer; v_restantes integer;
begin
  if p_limite is null or p_limite not between 1 and 1000 then
    raise exception 'efhub_nivel: limite deve estar entre 1 e 1000';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('clubef-efhub-nivel-lote-v1',0));
  select lote_id into v_lote from clube_novo.efhub_nivel_lote_v1
   where estado='planejado' order by criado_em limit 1 for update;
  if not found then
    insert into clube_novo.efhub_nivel_lote_v1(estado,limite,contrato_id)
    values('planejado',p_limite,'clubef-efhub-level-v1') returning lote_id into v_lote;
    with candidatos as (
      select c.card_id,c.overall,c.level_cap,c.orcamento,c.cap_estimado,
        case
          when c.codigo_tipo_carta_fisico=any(array[1,3,4,5,6,7]) and coalesce(c.level_cap,0)<>1 then 1
          when c.codigo_tipo_carta_fisico=any(array[1,3,4,5,6,7]) and c.level_cap=1 then 2
          when c.codigo_tipo_carta_fisico=0 and c.tipo_carta_id='player_type_0_subtype_0' then 3
          else null
        end grupo,
        exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 pub
          where pub.card_id=c.card_id) publicada,
        exists(select 1 from clube_novo.build_linha_card bo
          where bo.card_id=c.card_id and bo.execucao_tipo='producao'
            and bo.estado_otimizador='concluido') ja_otimizada,
        exists(select 1 from clube_novo.build_linha_card b where b.card_id=c.card_id and b.execucao_tipo='producao' and b.estado<>'invalida') no_motor
      from clube_novo.carta_jogo c
      where c.tipo_carta_id<>'player_delete_list'
        and c.roda_motor is not false
        and not exists(select 1 from clube_novo.build_linha_card bp where bp.card_id=c.card_id and bp.execucao_tipo='producao' and bp.estado_otimizador='processando')
        and not exists(select 1 from clube_novo.efhub_nivel_atual_v1 a where a.card_id=c.card_id)
    ), escolhidas as (
      select *,row_number() over(order by publicada desc,ja_otimizada desc,no_motor desc,
        grupo,overall desc nulls first,card_id collate "C") ordem
      from candidatos where grupo is not null
      order by publicada desc,ja_otimizada desc,no_motor desc,
        grupo,overall desc nulls first,card_id collate "C"
      limit p_limite
    )
    insert into clube_novo.efhub_nivel_lote_item_v1
      (lote_id,ordem,card_id,grupo_snapshot,overall_snapshot,nivel_anterior,orcamento_anterior,cap_estimado_anterior)
    select v_lote,ordem,card_id,grupo,overall,level_cap,orcamento,cap_estimado from escolhidas;
    get diagnostics v_total=row_count;
    if v_total=0 then
      delete from clube_novo.efhub_nivel_lote_v1 where lote_id=v_lote;
      v_lote:=null;
    else
      update clube_novo.efhub_nivel_lote_v1 set planejadas=v_total,atualizado_em=clock_timestamp() where lote_id=v_lote;
    end if;
  end if;
  select count(*) into v_restantes from clube_novo.carta_jogo c
   where c.tipo_carta_id<>'player_delete_list' and c.roda_motor is not false
     and (c.codigo_tipo_carta_fisico=any(array[1,3,4,5,6,7]) or (c.codigo_tipo_carta_fisico=0 and c.tipo_carta_id='player_type_0_subtype_0'))
     and not exists(select 1 from clube_novo.efhub_nivel_atual_v1 a where a.card_id=c.card_id);
  if v_lote is null then
    return jsonb_build_object('ok',true,'concluido',v_restantes=0,'restantes',v_restantes,'itens','[]'::jsonb);
  end if;
  return jsonb_build_object('ok',true,'concluido',false,'lote_id',v_lote,'restantes',v_restantes,
    'ordem_contrato','publicadas__ja_otimizadas__demais__evolucao__sem_evolucao__base__overall_desc',
    'itens',(select jsonb_agg(jsonb_build_object('ordem',i.ordem,'card_id',i.card_id,'grupo',i.grupo_snapshot,
      'overall',i.overall_snapshot,'nivel_anterior',i.nivel_anterior,'orcamento_anterior',i.orcamento_anterior) order by i.ordem)
      from clube_novo.efhub_nivel_lote_item_v1 i where i.lote_id=v_lote));
end $fn$;

comment on function public.extrator_efhub_planejar_lote_v1(integer) is
  'V2: planeja cartas do Otimizador por prioridade; level_cap zero permanece elegível até comprovação e catálogo só conclui com zero restante.';

notify pgrst,'reload schema';
commit;
