create table clube_novo.otimizador_lote_cartas_novas_v1(
 lote_id uuid not null,card_id text not null,overall_extraido integer not null check(overall_extraido between 1 and 150),
 prova_overall jsonb not null,criado_em timestamptz not null default clock_timestamp(),
 primary key(lote_id,card_id),
 foreign key(lote_id,card_id) references clube_novo.otimizador_lote_producao_candidata_v5(lote_id,card_id));
alter table clube_novo.otimizador_lote_cartas_novas_v1 enable row level security;
revoke all on clube_novo.otimizador_lote_cartas_novas_v1 from public,anon,authenticated;
insert into clube_novo.otimizador_lote_cartas_novas_v1(lote_id,card_id,overall_extraido,prova_overall)
select k.lote_id,k.card_id,(e.prova_json->>'overallRating')::integer,e.prova_json
from clube_novo.otimizador_lote_producao_candidata_v5 k join clube_novo.efhub_nivel_atual_v1 e using(card_id)
where k.lote_id='39da8ff4-7a4a-4ec7-8641-e81b5677ad4c' and not exists(select 1 from clube_novo.recalculo_1209_entrada_antes_v1 a where a.card_id=k.card_id);
create or replace view clube_novo.otimizador_fila_prioridade_v1 as  SELECT q.lote_id,
    q.linha_id,
    q.card_id,
    q.ordem_fila,
    q.overall_snapshot,
    q.entrada_fingerprint,
    q.reserva_token,
    q.worker_id,
    q.reservada_em,
    q.finalizada_em,
    q.tentativas,
    q.resultado_fingerprint,
    l.funcao_id,
    l.posicao_id,
    l.impeto_condicional_codigo,
    l.impeto_condicional_nivel,
    case when novas.card_id is not null then 0 else p.prioridade_grupo end as prioridade_grupo,
    case when dono.coluna is not null then (dono.valor #>> '{}')::integer else coalesce(p.overall,novas.overall_extraido) end AS overall_prioridade,
    p.nivel_maximo,
    p.orcamento_real,
    p.captura_id
   FROM clube_novo.otimizador_lote_producao_linha_v3 q
     JOIN clube_novo.build_linha_card l ON l.id = q.linha_id
     JOIN clube_novo.otimizador_lote_producao_carta_v3 s ON s.lote_id = q.lote_id AND s.card_id = q.card_id
     JOIN clube_novo.otimizador_prioridade_orcamento_v1 p ON p.card_id = q.card_id
 left join clube_novo.otimizador_lote_cartas_novas_v1 novas on novas.lote_id=q.lote_id and novas.card_id=q.card_id
 left join clube_novo.valor_do_dono dono on dono.destino_schema='clube_novo' and dono.destino_tabela='carta_jogo' and dono.coluna='overall' and dono.chave=jsonb_build_object('card_id',q.card_id)
 WHERE l.estado_otimizador = 'pendente'::text AND l.estado <> 'invalida'::text AND p.prioridade_grupo IS NOT NULL AND q.entrada_fingerprint = s.entrada_fingerprint AND ((s.entrada_otimizador #>> '{escalares,orcamento}'::text[])::integer) = p.orcamento_real AND (l.impeto_condicional_codigo IS NULL) = (l.impeto_condicional_nivel IS NULL);
CREATE OR REPLACE FUNCTION public.otimizador_producao_pacote_local_manifesto_v2(p_lote_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '90s'
 SET enable_nestloop TO 'off'
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_cartas integer;
  v_linhas integer;
  v_condicionais integer;
  v_prioridade_fingerprint text;
begin
  if p_lote_id is null then
    raise exception 'pacote local v2 recusado: lote obrigatório';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'pacote local v2 recusado: lote integral inexistente';
  end if;
  if v_lote.estado not in ('pausado','concluido')
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint not in (
       '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
       'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070',
       '5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89','a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2'
     )
     or not coalesce((v_lote.regua_snapshot -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'pacote local v2 recusado: lote não está pausado e apto para fotografia selada';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'pacote local v2 recusado: há reserva ativa no lote';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and ((l.impeto_condicional_codigo is null) <> (l.impeto_condicional_nivel is null))
  ) then
    raise exception 'pacote local v2 recusado: há linha com Ímpeto condicional pela metade (código sem nível, ou o contrário)';
  end if;

  -- A fotografia de prioridade é cara nos lotes grandes. Materializar uma vez
  -- evita as quatro leituras integrais que faziam o RPC estourar 30 segundos.
  with pendentes as materialized (
    select p.*
    from clube_novo.otimizador_fila_prioridade_v1 p
    where p.lote_id = p_lote_id
  )
  select count(distinct card_id)::integer,
         count(*)::integer,
         count(*) filter(where impeto_condicional_codigo is not null)::integer,
         encode(extensions.digest(convert_to(coalesce(
           string_agg(linha_id::text||':'||ordem_fila::text||':'||prioridade_grupo::text||':'||
             coalesce(overall_prioridade::text,'null')||':'||nivel_maximo::text||':'||captura_id::text||':'||entrada_fingerprint,
             ',' order by ordem_fila),''),'UTF8'),'sha256'),'hex')
  into v_cartas,v_linhas,v_condicionais,v_prioridade_fingerprint
  from pendentes;

  return jsonb_build_object(
    'contrato','otimizador_pacote_local_v2',
    'lote_id',v_lote.id,
    'formula_fingerprint',v_lote.formula_fingerprint,
    'contrato_fingerprint',v_lote.contrato_fingerprint,
    'motor_versao',v_lote.motor_versao,
    'lote_fingerprint',v_lote.fingerprint,
    'regua',v_lote.regua_snapshot,
    'pode_publicar',false,
    'impetos_condicionais',case when v_condicionais>0 then 'por_degrau' else 'nenhum_no_lote' end,
    'linhas_condicionais',coalesce(v_condicionais,0),
    'cartas_total',coalesce(v_cartas,0),
    'linhas_total',coalesce(v_linhas,0),
    'paginacao','cursor_canonico',
    'prioridade_contrato','prioridade_orcamento_v1',
    'prioridade_ordenacao',case when exists(select 1 from clube_novo.otimizador_lote_cartas_novas_v1 n where n.lote_id=p_lote_id) then 'novos_orcamento_overall_desc_v2' else 'prioridade_orcamento_v1' end,
    'prioridade_fingerprint',v_prioridade_fingerprint,
    'fonte','clube_novo.otimizador_entrada_linha_v1'
  );
end
$function$;

CREATE OR REPLACE FUNCTION public.otimizador_producao_pacote_local_linhas_v2(p_lote_id uuid, p_depois_de_ordem bigint DEFAULT NULL::bigint, p_limite integer DEFAULT 1000)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '30s'
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_itens jsonb := '[]'::jsonb;
  v_proxima_ordem bigint;
begin
  if p_lote_id is null or coalesce(p_limite, 0) not between 1 and 1000
     or coalesce(p_depois_de_ordem, 0) < 0 then
    raise exception 'página de linhas local v2 recusada: argumentos inválidos';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint not in (
       '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
       'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070',
       '5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89','a1cc830af3366e2d0c9ac12138d892058b3e57ed216e43d68242d105b33cb9d2'
     ) then
    raise exception 'página de linhas local v2 recusada: fotografia não está estável';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'página de linhas local v2 recusada: há reserva ativa';
  end if;

  with pagina as materialized (
    select q.linha_id, q.ordem_fila, q.entrada_fingerprint,
           q.prioridade_grupo,q.overall_prioridade,q.nivel_maximo,q.orcamento_real,q.captura_id,
           l.card_id, l.funcao_id, l.posicao_id,
           l.impeto_condicional_codigo, l.impeto_condicional_nivel,
           c.nome as carta_nome, f.rotulo as funcao_rotulo, p.nome_pt as posicao_rotulo
    from clube_novo.otimizador_fila_prioridade_v1 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    left join clube_novo.carta_jogo c on c.card_id = l.card_id
    left join clube_novo.funcao_sistema f on f.id = l.funcao_id
    left join clube_novo.posicao_jogo p on p.id = l.posicao_id
    where q.lote_id = p_lote_id
      and (p_depois_de_ordem is null or q.ordem_fila > p_depois_de_ordem)
      and l.estado_otimizador = 'pendente'
      -- 03/09: a linha condicional entra. Só fica de fora a que veio pela
      -- metade, sem o par completo que identifica o degrau.
      and ((l.impeto_condicional_codigo is null) = (l.impeto_condicional_nivel is null))
    order by q.ordem_fila
    limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id', linha_id,
    'ordem_fila', ordem_fila,
    'prioridade_grupo',prioridade_grupo,
    'prioridade_ordenacao',case when exists(select 1 from clube_novo.otimizador_lote_cartas_novas_v1 n where n.lote_id=p_lote_id) then 'novos_orcamento_overall_desc_v2' else 'prioridade_orcamento_v1' end,'overall_prioridade',overall_prioridade,
    'nivel_maximo',nivel_maximo,'orcamento_real',orcamento_real,'captura_id',captura_id,
    'card_id', card_id,
    'funcao_id', funcao_id,
    'posicao_id', posicao_id,
    'carta_entrada_fingerprint', entrada_fingerprint,
    'carta_nome', carta_nome,
    'funcao_rotulo', funcao_rotulo,
    'posicao_rotulo', posicao_rotulo,
    'impeto_condicional_codigo', impeto_condicional_codigo,
    'impeto_condicional_nivel', impeto_condicional_nivel
  ) order by ordem_fila), '[]'::jsonb), max(ordem_fila)
  into v_itens, v_proxima_ordem
  from pagina;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', p_lote_id,
    'depois_de_ordem', p_depois_de_ordem,
    'proxima_ordem_fila', v_proxima_ordem,
    'limite', p_limite,
    'contagem_no_manifesto', true,
    'itens', v_itens,
    'pode_publicar', false,
    'impetos_condicionais', 'por_degrau'
  );
end
$function$;



