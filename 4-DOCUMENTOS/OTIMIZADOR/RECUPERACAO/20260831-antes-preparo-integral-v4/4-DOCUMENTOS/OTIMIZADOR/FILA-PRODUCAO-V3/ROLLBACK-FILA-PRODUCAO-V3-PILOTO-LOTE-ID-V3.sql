-- Rollback V3.3: restaura exatamente a definição V3.2 anterior.
-- ou do caminho de produção completo (p_limite_cards = 0).
--
-- Problema corrigido: a V3 calculava as projeções de todas as candidatas antes
-- Não remove lote, linha, build ou evento já gravado.

create or replace function public.otimizador_producao_criar_lote_v3(
  p_lote_id uuid,
  p_formula_fingerprint text,
  p_motor_versao text,
  p_limite_cards integer default 0
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_formula constant text := '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad';
  v_regua jsonb; v_contrato_fp text; v_fingerprint text;
  v_cards integer; v_linhas integer; v_incompletas integer;
  v_condicionais integer; v_sem_linha integer; v_janela_consulta integer;
begin
  if p_lote_id is null or p_formula_fingerprint<>v_formula
     or nullif(btrim(coalesce(p_motor_versao,'')),'') is null then
    raise exception 'criação recusada: selo de fórmula ou versão do worker inválidos';
  end if;
  if coalesce(p_limite_cards,0)<0 or coalesce(p_limite_cards,0)>50000 then
    raise exception 'criação recusada: limite de cartas fora da faixa 0..50000';
  end if;
  if exists(select 1 from clube_novo.otimizador_lote_producao_v3) then
    raise exception 'criação recusada: já existe lote V3; arquivamento explícito é obrigatório antes de outro';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean,false) then
    raise exception 'criação recusada: gate da régua do Otimizador está fechado';
  end if;
  v_contrato_fp:=clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);
  -- Produção integral preserva a janela original. O piloto lê somente a
  -- quantidade pedida e duas sobras determinísticas, sem inferir resultado.
  v_janela_consulta:=case when coalesce(p_limite_cards,0)=0 then 50000
                           else least(50000,p_limite_cards+2) end;

  select count(*) into v_condicionais
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false) and coalesce(c.pode_rodar_vinculos,false)
    and exists(select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false));

  create temporary table _otimizador_producao_candidatas_base_v3 on commit drop as
  select c.card_id,c.overall,c.extraido_em
  from clube_novo.carta_jogo c
  where coalesce(c.roda_motor,false) and coalesce(c.pode_rodar_vinculos,false)
    and c.overall is not null
    and not exists(select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false))
  order by c.overall desc,c.card_id
  limit v_janela_consulta;

  create temporary table _otimizador_producao_candidatas_v3 on commit drop as
  select c.card_id,c.overall,c.extraido_em,
         public.otimizador_carta_v3(c.card_id) entrada_otimizador,
         public.bonificador_carta_v2(c.card_id) entrada_bonificador
  from _otimizador_producao_candidatas_base_v3 c;

  create temporary table _otimizador_producao_aptas_v3 on commit drop as
  select * from _otimizador_producao_candidatas_v3 x
  where coalesce((x.entrada_otimizador->'gate'->>'pode_rodar')::boolean,false)
    and coalesce((x.entrada_bonificador->>'pode_rodar')::boolean,false)
    and x.entrada_bonificador ? 'carta_versao'
    and x.entrada_bonificador ? 'carta_fingerprint';

  select (select count(*) from _otimizador_producao_candidatas_v3)-count(*)
  into v_incompletas from _otimizador_producao_aptas_v3;

  create temporary table _otimizador_producao_linhas_base_v3 on commit drop as
  select distinct a.card_id,a.overall,a.extraido_em,a.entrada_otimizador,a.entrada_bonificador,
    fp.funcao_id,fp.posicao_id
  from _otimizador_producao_aptas_v3 a
  join lateral (
    select cpp.posicao_id
    from clube_novo.carta_posicao_principal_jogo cpp where cpp.card_id=a.card_id
    union
    select cp.posicao_id
    from clube_novo.carta_posicao_jogo cp
    where cp.card_id=a.card_id and cp.nivel_aptidao>0
  ) px on true
  join clube_novo.otimizador_funcao_posicao fp on fp.posicao_id=px.posicao_id
  join clube_novo.funcao_sistema fs on fs.id=fp.funcao_id and fs.ativa and fs.pode_rodar
  join clube_novo.posicao_jogo p on p.id=fp.posicao_id and p.pode_rodar;

  select count(*) into v_sem_linha
  from _otimizador_producao_aptas_v3 a
  where not exists(select 1 from _otimizador_producao_linhas_base_v3 l where l.card_id=a.card_id);

  create temporary table _otimizador_producao_cards_v3 on commit drop as
  select distinct on (card_id) card_id,overall,extraido_em,entrada_otimizador,entrada_bonificador
  from _otimizador_producao_linhas_base_v3
  order by card_id,overall desc;

  create temporary table _otimizador_producao_selecionadas_v3 on commit drop as
  select * from _otimizador_producao_cards_v3
  order by overall desc,card_id
  limit case when coalesce(p_limite_cards,0)=0 then 50000 else p_limite_cards end;

  create temporary table _otimizador_producao_linhas_v3 on commit drop as
  select b.*,
    row_number() over(order by b.overall desc,b.card_id,b.funcao_id,b.posicao_id)::bigint ordem_fila
  from _otimizador_producao_linhas_base_v3 b
  join _otimizador_producao_selecionadas_v3 s using(card_id);

  select count(distinct card_id),count(*) into v_cards,v_linhas
  from _otimizador_producao_linhas_v3;
  if v_cards=0 or v_linhas=0 then
    raise exception 'criação recusada: não há carta apta com posição e função canônicas';
  end if;

  select encode(extensions.digest(convert_to(
    p_lote_id::text||':'||v_formula||':'||v_contrato_fp||':'||p_motor_versao||':'||
    string_agg(card_id||':'||funcao_id::text||':'||posicao_id::text||':'||ordem_fila::text,
               ',' order by ordem_fila),'UTF8'),'sha256'),'hex')
  into v_fingerprint
  from _otimizador_producao_linhas_v3;

  insert into clube_novo.otimizador_lote_producao_v3(
    id,formula_fingerprint,contrato_fingerprint,motor_versao,regua_snapshot,fingerprint,
    cards,linhas,excluidas_incompletas,excluidas_impeto_condicional,excluidas_sem_linha
  ) values (
    p_lote_id,v_formula,v_contrato_fp,p_motor_versao,v_regua,v_fingerprint,
    v_cards,v_linhas,v_incompletas,v_condicionais,v_sem_linha
  );

  insert into clube_novo.otimizador_lote_producao_carta_v3(
    lote_id,card_id,overall_snapshot,entrada_otimizador,entrada_fingerprint,
    carta_versao_bonificador,carta_fingerprint_bonificador
  )
  select s_card.lote_id,s_card.card_id,s_card.overall,s_card.entrada_otimizador,
    encode(extensions.digest(convert_to(s_card.entrada_otimizador::text,'UTF8'),'sha256'),'hex'),
    s_card.entrada_bonificador->>'carta_versao',s_card.entrada_bonificador->>'carta_fingerprint'
  from _otimizador_producao_selecionadas_v3 s_card;

  with inseridas as (
    insert into clube_novo.build_linha_card(
      card_id,funcao_id,posicao_id,carta_versao,carta_fingerprint,
      estado,pendencias,execucao_tipo,estado_otimizador,
      otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
      otimizador_motor_versao_esperada,impeto_condicional_codigo,impeto_condicional_nivel
    )
    select l.card_id,l.funcao_id,l.posicao_id,
      l.entrada_bonificador->>'carta_versao',l.entrada_bonificador->>'carta_fingerprint',
      'pendente','{}'::text[],'producao','pendente',v_formula,v_contrato_fp,p_motor_versao,
      null::integer,null::smallint
    from _otimizador_producao_linhas_v3 l
    order by l.ordem_fila
    returning id,card_id,funcao_id,posicao_id
  )
  insert into clube_novo.otimizador_lote_producao_linha_v3(
    lote_id,linha_id,card_id,ordem_fila,overall_snapshot,entrada_fingerprint
  )
  select p_lote_id,i.id,l.card_id,l.ordem_fila,l.overall,
    encode(extensions.digest(convert_to(l.entrada_otimizador::text,'UTF8'),'sha256'),'hex')
  from inseridas i
  join _otimizador_producao_linhas_v3 l
    on l.card_id=i.card_id and l.funcao_id=i.funcao_id and l.posicao_id=i.posicao_id;

  if (select count(*) from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=p_lote_id)<>v_linhas then
    raise exception 'criação recusada: a fila não preservou todas as linhas';
  end if;
  if exists(
    select 1
    from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id=q.linha_id
    where q.lote_id=p_lote_id
      and (l.impeto_condicional_codigo is not null or l.impeto_condicional_nivel is not null)
  ) then
    raise exception 'criação recusada: uma linha habilitou Ímpeto condicional';
  end if;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
  values(p_lote_id,'lote_criado',jsonb_build_object(
    'cards',v_cards,'linhas',v_linhas,'ordem','overall_desc_card_id_funcao_id_posicao_id',
    'limite_cards_solicitado',coalesce(p_limite_cards,0),
    'janela_candidatas_consultada',v_janela_consulta,
    'impetos_condicionais','desligados','pode_publicar',false
  ));
  return public.otimizador_producao_status_v3(p_lote_id);
end
$function$;
