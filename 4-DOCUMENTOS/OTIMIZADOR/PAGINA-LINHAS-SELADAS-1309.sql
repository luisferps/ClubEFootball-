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
  v_candidatas integer;
begin
  -- Esta pagina otimizada conserva exatamente a vista canonica validada.
  if pg_catalog.md5(pg_catalog.pg_get_viewdef('clube_novo.otimizador_fila_prioridade_v1'::regclass,true)) <> 'a63c58b70b12b3893b29df9e47af6100' then
    raise exception 'contrato de prioridade mudou: atualizar pagina otimizada antes de exportar';
  end if;
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

  with proximas as materialized (
    select q.* from clube_novo.otimizador_lote_producao_linha_v3 q
    join clube_novo.build_linha_card l on l.id=q.linha_id
    where q.lote_id=p_lote_id
      and (p_depois_de_ordem is null or q.ordem_fila>p_depois_de_ordem)
      and l.estado_otimizador='pendente' and l.estado<>'invalida'
    order by q.ordem_fila
    limit case when v_lote.preparo_fingerprint_final is not null then p_limite else null end
  ), aptas as (
 SELECT q.lote_id,
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
        CASE
            WHEN novas.card_id IS NOT NULL THEN 0
            ELSE p.prioridade_grupo
        END AS prioridade_grupo,
        CASE
            WHEN dono.coluna IS NOT NULL THEN (dono.valor #>> '{}'::text[])::integer
            ELSE COALESCE(p.overall, novas.overall_extraido)
        END AS overall_prioridade,
    p.nivel_maximo,
    p.orcamento_real,
    p.captura_id
   FROM proximas q
     JOIN clube_novo.build_linha_card l ON l.id = q.linha_id
     JOIN clube_novo.otimizador_lote_producao_carta_v3 s ON s.lote_id = q.lote_id AND s.card_id = q.card_id
     JOIN clube_novo.otimizador_prioridade_orcamento_v1 p ON p.card_id = q.card_id
     LEFT JOIN clube_novo.otimizador_lote_cartas_novas_v1 novas ON novas.lote_id = q.lote_id AND novas.card_id = q.card_id
     LEFT JOIN clube_novo.valor_do_dono dono ON dono.destino_schema = 'clube_novo'::text AND dono.destino_tabela = 'carta_jogo'::text AND dono.coluna = 'overall'::text AND dono.chave = jsonb_build_object('card_id', q.card_id)
  WHERE l.estado_otimizador = 'pendente'::text AND l.estado <> 'invalida'::text AND p.prioridade_grupo IS NOT NULL AND q.entrada_fingerprint = s.entrada_fingerprint AND ((s.entrada_otimizador #>> '{escalares,orcamento}'::text[])::integer) = p.orcamento_real AND (l.impeto_condicional_codigo IS NULL) = (l.impeto_condicional_nivel IS NULL)
  ), pagina as materialized (
    select q.linha_id, q.ordem_fila, q.entrada_fingerprint,
           q.prioridade_grupo,q.overall_prioridade,q.nivel_maximo,q.orcamento_real,q.captura_id,
           l.card_id, l.funcao_id, l.posicao_id,
           l.impeto_condicional_codigo, l.impeto_condicional_nivel,
           c.nome as carta_nome, f.rotulo as funcao_rotulo, p.nome_pt as posicao_rotulo
    from aptas q
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
  ) order by ordem_fila), '[]'::jsonb), max(ordem_fila), (select count(*) from proximas)
  into v_itens, v_proxima_ordem, v_candidatas
  from pagina;

  if v_lote.preparo_fingerprint_final is not null and jsonb_array_length(v_itens)<>v_candidatas then
    raise exception 'pagina recusada: elegibilidade mudou depois da selagem; renove a fila';
  end if;
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
$function$
;
