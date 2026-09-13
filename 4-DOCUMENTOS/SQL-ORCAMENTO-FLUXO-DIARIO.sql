alter table clube_novo.efhub_nivel_lote_item_v1 drop constraint efhub_nivel_lote_item_v1_estado_check;
alter table clube_novo.efhub_nivel_lote_item_v1 add constraint efhub_nivel_lote_item_v1_estado_check check(estado in ('planejado','coletado','aplicado','inalterado','falhou','conflito_fisico','aguardando_orcamento'));
create index if not exists efhub_nivel_aguardando_reconsulta_idx on clube_novo.efhub_nivel_lote_item_v1(card_id,coletado_em) where estado='aguardando_orcamento';
create or replace view clube_novo.carta_orcamento_pendente_automatico_v1 as
select c.card_id,c.nome,'aguardando_divulgacao'::text estado
from clube_novo.carta_operacional_v1 c
left join clube_novo.carta_nivel_evidencia_v1 e on e.card_id=c.card_id
where coalesce(c.roda_motor,false)
and not (coalesce(e.nivel_maximo>=1 and e.orcamento_real=2*(e.nivel_maximo-1),false)
 and coalesce(c.level_cap>=1 and c.orcamento=2*(c.level_cap-1) and c.cap_estimado=false,false))
and (coalesce(c.level_cap,0)<1 or c.cap_estimado is true
 or exists(select 1 from clube_novo.efhub_nivel_lote_item_v1 i where i.card_id=c.card_id and i.estado='aguardando_orcamento'))
and not exists(select 1 from clube_novo.valor_do_dono d where d.destino_schema='clube_novo' and d.destino_tabela='carta_jogo'
 and d.chave=jsonb_build_object('card_id',c.card_id) and d.coluna in ('level_cap','orcamento')
 and c.level_cap>=1 and c.orcamento=2*(c.level_cap-1) and c.cap_estimado=false);
revoke all on clube_novo.carta_orcamento_pendente_automatico_v1 from public,anon,authenticated;

CREATE OR REPLACE FUNCTION public.extrator_efhub_aplicar_lote_v1(p_lote uuid, p_manifesto_sha256 text, p_itens jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_l clube_novo.efhub_nivel_lote_v1%rowtype; v_item jsonb; v_i clube_novo.efhub_nivel_lote_item_v1%rowtype;
 v_e clube_novo.carta_nivel_evidencia_v1%rowtype; v_n integer; v_ok integer:=0; v_falhas integer:=0;
 v_aguardando integer:=0; v_conflitos integer:=0; v_alteradas integer:=0; v_inalteradas integer:=0; v_linhas integer:=0;
 v_nivel integer; v_orcamento integer; v_instante timestamptz; v_url text; v_estado text; v_tem_evidencia boolean;
 v_linhas_por_card jsonb;
begin
  if p_lote is null or p_manifesto_sha256 !~ '^[0-9a-f]{64}$' or jsonb_typeof(p_itens) is distinct from 'array' then
    raise exception 'efhub_nivel: manifesto invalido';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('clubef-efhub-nivel-lote-v1',0));
  select * into v_l from clube_novo.efhub_nivel_lote_v1 where lote_id=p_lote for update;
  if not found then raise exception 'efhub_nivel: lote inexistente'; end if;
  if v_l.estado<>'planejado' then
    if v_l.manifesto_sha256=p_manifesto_sha256 then
      return v_l.resumo||jsonb_build_object('ok',true,'idempotente',true,'lote_id',p_lote);
    end if;
    raise exception 'efhub_nivel: lote ja consumido por outro manifesto';
  end if;
  if jsonb_array_length(p_itens)<>v_l.planejadas
     or (select count(distinct x->>'card_id') from jsonb_array_elements(p_itens)x)<>v_l.planejadas
     or exists(select 1 from clube_novo.efhub_nivel_lote_item_v1 i where i.lote_id=p_lote
       and not exists(select 1 from jsonb_array_elements(p_itens)x where x->>'card_id'=i.card_id))
  then raise exception 'efhub_nivel: resposta nao corresponde ao lote planejado'; end if;
  if exists(select 1 from jsonb_array_elements(p_itens)x where x->>'estado' not in ('coletado','falhou','aguardando_orcamento')) then
    raise exception 'efhub_nivel: estado de item invalido';
  end if;
  if exists(select 1 from jsonb_array_elements(p_itens)x where x->>'estado'='coletado' and (
    (x->>'card_id')!~'^[0-9]+$' or (x->>'level_cap')!~'^[0-9]+$' or (x->>'level_cap')::integer not between 1 and 99
    or x->>'source_url'<>'https://efhub.com/api/public/players/'||(x->>'card_id')
    or coalesce(x->>'response_sha256','')!~'^[0-9a-f]{64}$'
    or x->>'id'<>x->>'card_id' or x->>'player_id'<>x->>'card_id'
    or jsonb_typeof(x->'prova_json') is distinct from 'object')) then
    raise exception 'efhub_nivel: resposta coletada reprovada na validacao';
  end if;
  v_instante:=clock_timestamp();
  select count(*) into v_n from jsonb_array_elements(p_itens)x where x->>'estado'='coletado';
  if v_n>0 then
    insert into clube_novo.nivel_runtime_captura_v1(captura_id,contrato_id,executavel_sha256,executavel_versao,leitor_versao,capturado_em,quantidade,manifesto_sha256,prova_json)
    values(p_lote,'clubef-efhub-level-v1','ff138ffcce0757d9e6d57659ef231de75a2f16515639241c847e56e768cd8da3',
      'api-public-v1','efhub-level-v1',v_instante,v_n,p_manifesto_sha256,jsonb_build_object('lote_id',p_lote,'source','efhub','itens',v_n));
  end if;
  for v_item in select value from jsonb_array_elements(p_itens) order by (value->>'ordem')::integer loop
    select * into v_i from clube_novo.efhub_nivel_lote_item_v1 where lote_id=p_lote and card_id=v_item->>'card_id' for update;
    if v_item->>'estado'='aguardando_orcamento' then
 if v_item->>'id' is distinct from v_i.card_id or v_item->>'player_id' is distinct from v_i.card_id
 or v_item->>'source_url' is distinct from 'https://efhub.com/api/public/players/'||v_i.card_id
 or coalesce(v_item->>'response_sha256','') !~ '^[0-9a-f]{64}$'
 or v_item#>'{prova_json,levelCap}' is distinct from '0'::jsonb or v_item->>'http_status' is distinct from '200'
 then raise exception 'efhub_nivel: prova de orcamento nao divulgado invalida'; end if;
 update clube_novo.efhub_nivel_lote_item_v1 set estado='aguardando_orcamento',tentativas=1,http_status=200,source_url=v_item->>'source_url',response_sha256=v_item->>'response_sha256',prova_json=v_item->'prova_json',nome_efhub=v_item->>'name',erro=null,coletado_em=v_instante where lote_id=p_lote and card_id=v_i.card_id;
 v_aguardando:=v_aguardando+1; continue;
 end if;
 if v_item->>'estado'='falhou' then
      update clube_novo.efhub_nivel_lote_item_v1 set estado='falhou',tentativas=greatest(1,coalesce((v_item->>'tentativas')::integer,1)),
        http_status=nullif(v_item->>'http_status','')::integer,erro=left(coalesce(v_item->>'erro','falha sem detalhe'),1000),coletado_em=v_instante
       where lote_id=p_lote and card_id=v_i.card_id;
      v_falhas:=v_falhas+1; continue;
    end if;
    perform 1 from clube_novo.carta_jogo where card_id=v_i.card_id for update;
    perform 1 from clube_novo.build_linha_card where card_id=v_i.card_id and execucao_tipo='producao' and estado<>'invalida' for update;
    if exists(select 1 from clube_novo.build_linha_card where card_id=v_i.card_id and execucao_tipo='producao' and estado_otimizador='processando') then
      update clube_novo.efhub_nivel_lote_item_v1 set estado='falhou',tentativas=greatest(1,coalesce((v_item->>'tentativas')::integer,1)),
        erro='card entrou em processamento durante a coleta; nivel nao alterado',coletado_em=v_instante
       where lote_id=p_lote and card_id=v_i.card_id;
      v_falhas:=v_falhas+1; continue;
    end if;
    v_nivel:=(v_item->>'level_cap')::integer; v_orcamento:=2*v_nivel-2; v_url:=v_item->>'source_url';
    insert into clube_novo.efhub_nivel_atual_v1(card_id,lote_id,nivel_maximo,orcamento_real,response_sha256,source_url,prova_json,comprovado_em)
    values(v_i.card_id,p_lote,v_nivel,v_orcamento,v_item->>'response_sha256',v_url,v_item->'prova_json',v_instante)
    on conflict(card_id) do update set lote_id=excluded.lote_id,nivel_maximo=excluded.nivel_maximo,orcamento_real=excluded.orcamento_real,
      response_sha256=excluded.response_sha256,source_url=excluded.source_url,prova_json=excluded.prova_json,comprovado_em=excluded.comprovado_em,atualizado_em=clock_timestamp();
    select * into v_e from clube_novo.carta_nivel_evidencia_v1 where card_id=v_i.card_id for update;
    v_tem_evidencia:=found;
    if v_tem_evidencia and v_e.fonte=any(array['memoria_jogo','tipo_carta_fisico']) and (v_e.nivel_maximo<>v_nivel or v_e.orcamento_real<>v_orcamento) then
      v_estado:='conflito_fisico'; v_conflitos:=v_conflitos+1;
    else
      if v_i.nivel_anterior is distinct from v_nivel or v_i.orcamento_anterior is distinct from v_orcamento or v_i.cap_estimado_anterior is distinct from false
        then v_estado:='aplicado'; v_alteradas:=v_alteradas+1; else v_estado:='inalterado'; v_inalteradas:=v_inalteradas+1; end if;
      insert into clube_novo.carta_nivel_historico_v1(captura_id,card_id,nivel_anterior,orcamento_anterior,cap_estimado_anterior,nivel_maximo,orcamento_real,prova_json)
      select p_lote,c.card_id,c.level_cap,c.orcamento,c.cap_estimado,v_nivel,v_orcamento,v_item->'prova_json'
      from clube_novo.carta_jogo c where c.card_id=v_i.card_id;
      if not v_tem_evidencia or not (v_e.fonte=any(array['memoria_jogo','tipo_carta_fisico'])) then
        insert into clube_novo.carta_nivel_evidencia_v1(card_id,nivel_maximo,orcamento_real,fonte,contrato_id,captura_id,prova_json,comprovado_em)
        values(v_i.card_id,v_nivel,v_orcamento,'efhub','clubef-efhub-level-v1',p_lote,v_item->'prova_json',v_instante)
        on conflict(card_id) do update set nivel_maximo=excluded.nivel_maximo,orcamento_real=excluded.orcamento_real,fonte=excluded.fonte,
          contrato_id=excluded.contrato_id,captura_id=excluded.captura_id,prova_json=excluded.prova_json,comprovado_em=excluded.comprovado_em,atualizado_em=clock_timestamp();
      end if;
      update clube_novo.carta_jogo set level_cap=v_nivel,orcamento=v_orcamento,cap_estimado=false where card_id=v_i.card_id;
    end if;
    update clube_novo.efhub_nivel_lote_item_v1 set estado=v_estado,tentativas=greatest(1,coalesce((v_item->>'tentativas')::integer,1)),
      source_url=v_url,http_status=(v_item->>'http_status')::integer,response_sha256=v_item->>'response_sha256',nome_efhub=v_item->>'name',
      player_type=nullif(v_item->>'player_type','')::integer,datapack_id=nullif(v_item->>'datapack_id','')::integer,nivel_maximo=v_nivel,
      orcamento_real=v_orcamento,prova_json=v_item->'prova_json',erro=null,coletado_em=v_instante,aplicado_em=case when v_estado<>'conflito_fisico' then v_instante else null end
    where lote_id=p_lote and card_id=v_i.card_id;
    v_ok:=v_ok+1;
  end loop;
  select count(*) into v_linhas from clube_novo.build_linha_card b
    join clube_novo.otimizador_lote_producao_carta_v3 s on s.lote_id=b.lote_producao_id and s.card_id=b.card_id
    join clube_novo.carta_nivel_evidencia_v1 e on e.card_id=b.card_id
    where b.execucao_tipo='producao' and b.estado<>'invalida' and b.estado_otimizador<>'processando'
      and b.card_id in(select i.card_id from clube_novo.efhub_nivel_lote_item_v1 i where i.lote_id=p_lote and i.estado in('aplicado','inalterado'))
      and (s.entrada_otimizador#>>'{escalares,orcamento}')::integer is distinct from e.orcamento_real
      and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=b.id);
  select coalesce(jsonb_agg(jsonb_build_object('card_id',z.card_id,'linhas',z.linhas) order by z.card_id collate "C"),'[]'::jsonb)
    into v_linhas_por_card from (
      select b.card_id,jsonb_agg(b.id order by b.id) linhas from clube_novo.build_linha_card b
      join clube_novo.otimizador_lote_producao_carta_v3 s on s.lote_id=b.lote_producao_id and s.card_id=b.card_id
      join clube_novo.carta_nivel_evidencia_v1 e on e.card_id=b.card_id
      where b.execucao_tipo='producao' and b.estado<>'invalida' and b.estado_otimizador<>'processando'
        and b.card_id in(select i.card_id from clube_novo.efhub_nivel_lote_item_v1 i where i.lote_id=p_lote and i.estado in('aplicado','inalterado'))
        and (s.entrada_otimizador#>>'{escalares,orcamento}')::integer is distinct from e.orcamento_real
        and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=b.id)
      group by b.card_id)z;
  update clube_novo.efhub_nivel_lote_v1 set estado='comparado',coletadas=v_ok,falhas=v_falhas,conflitos_fisicos=v_conflitos,
    alteradas=v_alteradas,inalteradas=v_inalteradas,linhas_divergentes=v_linhas,manifesto_sha256=p_manifesto_sha256,
    resumo=jsonb_build_object('ok',true,'idempotente',false,'lote_id',p_lote,'coletadas',v_ok,'falhas',v_falhas,'aguardando_orcamento',v_aguardando,
      'conflitos_fisicos',v_conflitos,'cartas_alteradas',v_alteradas,'cartas_inalteradas',v_inalteradas,
      'linhas_divergentes',v_linhas,'linhas_por_card',v_linhas_por_card),
    atualizado_em=clock_timestamp(),aplicado_em=v_instante where lote_id=p_lote;
  return (select resumo from clube_novo.efhub_nivel_lote_v1 where lote_id=p_lote);
end $function$;
CREATE OR REPLACE FUNCTION public.extrator_efhub_planejar_lote_v1(p_limite integer DEFAULT 1000)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
          when c.codigo_tipo_carta_fisico=any(array[1,4,5,6,7]) and coalesce(c.level_cap,0)<>1 then 1
          when c.codigo_tipo_carta_fisico=any(array[1,4,5,6,7]) and c.level_cap=1 then 2
          when c.codigo_tipo_carta_fisico=0 and c.tipo_carta_id='player_type_0_subtype_0' then 3
          else null
        end grupo,
        exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 pub
          where pub.card_id=c.card_id) publicada,
        exists(select 1 from clube_novo.build_linha_card bo
          where bo.card_id=c.card_id and bo.execucao_tipo='producao'
            and bo.estado_otimizador='concluido') ja_otimizada,
        exists(select 1 from clube_novo.build_linha_card b where b.card_id=c.card_id and b.execucao_tipo='producao' and b.estado<>'invalida') no_motor
      from clube_novo.carta_operacional_v1 c
      where c.tipo_carta_id<>'player_delete_list'
        and c.roda_motor is not false
        and not exists(select 1 from clube_novo.build_linha_card bp where bp.card_id=c.card_id and bp.execucao_tipo='producao' and bp.estado_otimizador='processando')
        and not exists(select 1 from clube_novo.efhub_nivel_lote_item_v1 ultimo
          where ultimo.card_id=c.card_id and ultimo.estado='aguardando_orcamento'
          and ultimo.coletado_em >= date_trunc('day',now() at time zone 'America/Sao_Paulo') at time zone 'America/Sao_Paulo')
 and not exists(select 1 from clube_novo.efhub_nivel_atual_v1 a where a.card_id=c.card_id)
    ), escolhidas as (
      select *,row_number() over(order by publicada desc,ja_otimizada desc,no_motor desc,
        grupo,overall DESC NULLS FIRST,card_id collate "C") ordem
      from candidatos where grupo is not null
      order by publicada desc,ja_otimizada desc,no_motor desc,
        grupo,overall DESC NULLS FIRST,card_id collate "C"
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
  select count(*) into v_restantes from clube_novo.carta_operacional_v1 c
   where c.tipo_carta_id<>'player_delete_list' and c.roda_motor is not false
     and (c.codigo_tipo_carta_fisico=any(array[1,4,5,6,7]) or (c.codigo_tipo_carta_fisico=0 and c.tipo_carta_id='player_type_0_subtype_0'))
     and not exists(select 1 from clube_novo.efhub_nivel_lote_item_v1 ultimo
          where ultimo.card_id=c.card_id and ultimo.estado='aguardando_orcamento'
          and ultimo.coletado_em >= date_trunc('day',now() at time zone 'America/Sao_Paulo') at time zone 'America/Sao_Paulo')
 and not exists(select 1 from clube_novo.efhub_nivel_atual_v1 a where a.card_id=c.card_id);
  if v_lote is null then
    return jsonb_build_object('ok',true,'concluido',v_restantes=0,'restantes',v_restantes,'itens','[]'::jsonb);
  end if;
  return jsonb_build_object('ok',true,'concluido',false,'lote_id',v_lote,'restantes',v_restantes,
    'ordem_contrato','publicadas__ja_otimizadas__demais__evolucao__sem_evolucao__base__overall_desc',
    'itens',(select jsonb_agg(jsonb_build_object('ordem',i.ordem,'card_id',i.card_id,'grupo',i.grupo_snapshot,
      'overall',i.overall_snapshot,'nivel_anterior',i.nivel_anterior,'orcamento_anterior',i.orcamento_anterior) order by i.ordem)
      from clube_novo.efhub_nivel_lote_item_v1 i where i.lote_id=v_lote));
end $function$;
CREATE OR REPLACE FUNCTION public.site_novo_ficha_v2(p_card_id text, p_linha_id bigint DEFAULT NULL::bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare d jsonb; ids integer[]; linha bigint; hs jsonb; v_selo boolean;
begin
  d := public.site_novo_ficha_sem_complemento_v14(p_card_id, p_linha_id);
  linha := (d#>>'{dados,build,linha_id}')::bigint;
  if linha is null then
    if exists(select 1 from clube_novo.carta_orcamento_pendente_automatico_v1 a where a.card_id=p_card_id)
    then d:=d || jsonb_build_object('mensagem','Orçamento ainda não divulgado. Aguardando uma próxima atualização do eFootball.','pendencia_orcamento','aguardando_divulgacao'); end if;
    return d;
  end if;

  select v.regua_vigente into v_selo from clube_novo.build_publicacao_exibivel_v3 v where v.linha_id = linha limit 1;
  d := jsonb_set(d, '{dados,build,regua_vigente}', to_jsonb(coalesce(v_selo,false)));


  select coalesce(c.habilidades, r.complementares) into ids
  from clube_novo.build_publicacao_exibivel_v3 v
  left join clube_novo.build_complemento_v14 c on c.build_id = v.build_otimizador_id
  left join clube_novo.complemento_recibo_v14 r on r.build_novo_id = v.build_otimizador_id
  where v.linha_id = linha
  limit 1;

  if coalesce(cardinality(ids),0) = 0 then return d; end if;

  select jsonb_agg(x || jsonb_build_object('complementar',(x->>'id')::integer = any(ids)) order by ord)
  into hs
  from jsonb_array_elements(d#>'{dados,build,habilidades_adicionadas}') with ordinality t(x,ord);

  return jsonb_set(d,'{dados,build,habilidades_adicionadas}', coalesce(hs,'[]'::jsonb));
end $function$;
