CREATE OR REPLACE FUNCTION clube_novo.site_novo_box_card_identidade_v1(p_card jsonb)
RETURNS jsonb LANGUAGE sql STABLE SET search_path TO '' AS $$
with pos as (
 select p.id,p.nome_pt from clube_novo.posicao_jogo p
 where p.codigo_pt=coalesce(nullif(p_card#>>'{analises,0,posicao}',''),p_card->>'posicao')
)
select jsonb_build_object('posicao_nome',(select nome_pt from pos limit 1),
 'estilos',coalesce((select jsonb_agg(jsonb_build_object('id',s.playstyle_id,'nome',ps.nome_tela) order by s.slot_fisico)
 from clube_novo.carta_playstyle_jogo s join clube_novo.playstyle ps on ps.id_jogo=s.playstyle_id
 where s.card_id=p_card->>'card_id' and ps.nome_tela is not null and s.playstyle_id<>256
 and exists(select 1 from clube_novo.bonificador_regra_playstyle r join pos on pos.id=r.posicao_id where r.playstyle_id=s.playstyle_id and r.da_bonus)), '[]'::jsonb));
$$;
REVOKE ALL ON FUNCTION clube_novo.site_novo_box_card_identidade_v1(jsonb) FROM PUBLIC;
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
              (c.item-'analises') || clube_novo.site_novo_box_card_identidade_v1(c.item) || jsonb_build_object(
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
        (i.item-'analises') || clube_novo.site_novo_box_card_identidade_v1(i.item) || jsonb_build_object(
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
$function$
;
