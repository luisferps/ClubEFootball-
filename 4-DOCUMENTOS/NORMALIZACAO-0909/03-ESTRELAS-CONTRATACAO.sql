-- Equivalência visual das seis etiquetas. Faixas e snapshots preservados.
alter table clube_novo.regua_contratacao_faixa_v1 add column estrelas smallint;
update clube_novo.regua_contratacao_faixa_v1 set estrelas=case codigo
 when 'nao_pagar' then 0 when 'muito_pouco' then 1 when 'pouco' then 2
 when 'pagar' then 3 when 'caro' then 4 when 'qualquer_preco' then 5 end;
alter table clube_novo.regua_contratacao_faixa_v1 alter column estrelas set not null;
alter table clube_novo.regua_contratacao_faixa_v1 add constraint contratacao_estrelas_0_5 check(estrelas between 0 and 5);
comment on column clube_novo.regua_contratacao_faixa_v1.estrelas is
 'Quantidade de estrelas preenchidas dentre cinco. Equivalência de apresentação da etiqueta, sem alterar seus limites ou reclassificar snapshots.';
create function clube_novo.contratacao_estrelas_v1(p_codigo text)
returns smallint language sql stable strict security definer set search_path='' as $fn$
 select f.estrelas from clube_novo.regua_contratacao_faixa_v1 f
 join clube_novo.regua_contratacao_versao_v1 v on v.versao=f.regua_versao and v.estado='vigente'
 where f.codigo=p_codigo;
$fn$;
revoke all on function clube_novo.contratacao_estrelas_v1(text) from public,anon,authenticated;
grant execute on function clube_novo.contratacao_estrelas_v1(text) to service_role;
CREATE OR REPLACE FUNCTION clube_novo.contratacoes_por_box_build_v1(p_card_id text, p_funcao_rotulo text, p_percentual_topo_dinamico numeric)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  with faixa_vigente as (
    select f.regua_versao, f.codigo, f.percentual_minimo, f.rotulo
    from clube_novo.regua_contratacao_faixa_v1 f
    join clube_novo.regua_contratacao_versao_v1 v
      on v.versao = f.regua_versao and v.estado = 'vigente'
  ), dinamicas as (
    select
      c.box_id, c.box_nome, c.estado_box,
      'dinamica'::text as origem_percentual,
      p_percentual_topo_dinamico as percentual_topo,
      faixa.codigo as etiqueta_codigo,
      faixa.rotulo as etiqueta_rotulo,
      faixa.regua_versao,
      null::timestamptz as congelado_em
    from clube_novo.box_card_em_andamento_v1 m
    join clube_novo.box_contexto_contratacao_v1 c
      on c.box_id = m.box_id and c.estado_box = 'em_andamento'
    join lateral (
      select f.*
      from faixa_vigente f
      where p_percentual_topo_dinamico >= f.percentual_minimo
      order by f.percentual_minimo desc
      limit 1
    ) faixa on true
    where m.card_id = p_card_id
  ), historicas as (
    select
      c.box_id, c.box_nome, c.estado_box,
      'snapshot'::text as origem_percentual,
      s.percentual_topo_snapshot as percentual_topo,
      s.etiqueta_codigo,
      s.etiqueta_rotulo,
      s.regua_versao_snapshot as regua_versao,
      s.congelado_em
    from clube_novo.box_card_contratacao_snapshot_v1 s
    join clube_novo.box_contexto_contratacao_v1 c
      on c.box_id = s.box_id and c.estado_box = 'finalizada'
    where s.card_id = p_card_id
      and lower(btrim(s.funcao_rotulo)) = lower(btrim(p_funcao_rotulo))
  ), contextos as (
    select * from dinamicas
    union all
    select * from historicas
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'box_id', box_id,
    'box_nome', box_nome,
    'estado_box', estado_box,
    'origem_percentual', origem_percentual,
    'percentual_topo', percentual_topo,
    'etiqueta_codigo', etiqueta_codigo,
    'estrelas', clube_novo.contratacao_estrelas_v1(etiqueta_codigo),
    'etiqueta_rotulo', etiqueta_rotulo,
    'regua_versao', regua_versao,
    'congelado_em', congelado_em
  ) order by estado_box, box_nome, box_id), '[]'::jsonb)
  from contextos;
$function$;
CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_resposta_publica_v1(p_resposta jsonb)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  with itens as (
    select coalesce(jsonb_agg(
      case when p_resposta->>'modo'='boxes' then
        (i.item-'melhor_percentual'-'cards') || jsonb_build_object(
          'cards',(
            select coalesce(jsonb_agg(
              (c.item-'analises') || jsonb_build_object(
                'analises',(
                  select coalesce(jsonb_agg((a.item-'percentual_topo') || jsonb_build_object('estrelas',clube_novo.contratacao_estrelas_v1(a.item->>'codigo')) order by a.ord),'[]'::jsonb)
                  from jsonb_array_elements(coalesce(c.item->'analises','[]'::jsonb))
                    with ordinality as a(item,ord)
                )
              ) order by c.ord),'[]'::jsonb)
            from jsonb_array_elements(coalesce(i.item->'cards','[]'::jsonb))
              with ordinality as c(item,ord)
          )
        )
      else
        (i.item-'analises') || jsonb_build_object(
          'analises',(
            select coalesce(jsonb_agg((a.item-'percentual_topo') || jsonb_build_object('estrelas',clube_novo.contratacao_estrelas_v1(a.item->>'codigo')) order by a.ord),'[]'::jsonb)
            from jsonb_array_elements(coalesce(i.item->'analises','[]'::jsonb))
              with ordinality as a(item,ord)
          )
        )
      end order by i.ord
    ),'[]'::jsonb) valor
    from jsonb_array_elements(coalesce(p_resposta->'itens','[]'::jsonb))
      with ordinality as i(item,ord)
  ),
  regua as (
    select coalesce(jsonb_agg((f.item-'percentual_minimo') || jsonb_build_object('estrelas',clube_novo.contratacao_estrelas_v1(f.item->>'codigo')) order by f.ord),'[]'::jsonb) valor
    from jsonb_array_elements(coalesce(p_resposta->'regua','[]'::jsonb))
      with ordinality as f(item,ord)
  )
  select jsonb_set(jsonb_set(p_resposta,'{itens}',itens.valor),'{regua}',regua.valor)
  from itens cross join regua;
$function$;
