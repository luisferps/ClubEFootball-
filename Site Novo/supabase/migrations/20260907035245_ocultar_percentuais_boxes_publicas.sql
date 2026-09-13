-- O cálculo e a ordenação continuam internos. A resposta pública expõe somente
-- a etiqueta resultante, sem percentual do card nem limites da régua.
alter function public.site_novo_boxes_em_andamento_v1(text,text,integer,integer,integer)
  rename to site_novo_boxes_em_andamento_calculo_v1;
alter function public.site_novo_boxes_em_andamento_calculo_v1(text,text,integer,integer,integer)
  set schema clube_novo;

alter function public.site_novo_boxes_v1(text,text,integer,integer,text,integer)
  rename to site_novo_boxes_calculo_v1;
alter function public.site_novo_boxes_calculo_v1(text,text,integer,integer,text,integer)
  set schema clube_novo;

revoke all on function clube_novo.site_novo_boxes_em_andamento_calculo_v1(text,text,integer,integer,integer) from public,anon,authenticated;
revoke all on function clube_novo.site_novo_boxes_calculo_v1(text,text,integer,integer,text,integer) from public,anon,authenticated;
grant execute on function clube_novo.site_novo_boxes_em_andamento_calculo_v1(text,text,integer,integer,integer) to service_role;
grant execute on function clube_novo.site_novo_boxes_calculo_v1(text,text,integer,integer,text,integer) to service_role;

create or replace function clube_novo.site_novo_boxes_resposta_publica_v1(p_resposta jsonb)
returns jsonb
language sql
immutable
security definer
set search_path to ''
as $function$
  with itens as (
    select coalesce(jsonb_agg(
      case when p_resposta->>'modo'='boxes' then
        (i.item-'melhor_percentual'-'cards') || jsonb_build_object(
          'cards',(
            select coalesce(jsonb_agg(
              (c.item-'analises') || jsonb_build_object(
                'analises',(
                  select coalesce(jsonb_agg(a.item-'percentual_topo' order by a.ord),'[]'::jsonb)
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
            select coalesce(jsonb_agg(a.item-'percentual_topo' order by a.ord),'[]'::jsonb)
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
    select coalesce(jsonb_agg(f.item-'percentual_minimo' order by f.ord),'[]'::jsonb) valor
    from jsonb_array_elements(coalesce(p_resposta->'regua','[]'::jsonb))
      with ordinality as f(item,ord)
  )
  select jsonb_set(jsonb_set(p_resposta,'{itens}',itens.valor),'{regua}',regua.valor)
  from itens cross join regua;
$function$;

revoke all on function clube_novo.site_novo_boxes_resposta_publica_v1(jsonb) from public,anon,authenticated;
grant execute on function clube_novo.site_novo_boxes_resposta_publica_v1(jsonb) to service_role;

create or replace function public.site_novo_boxes_em_andamento_v1(
  p_box text default null,
  p_busca text default '',
  p_limite integer default 24,
  p_offset integer default 0,
  p_degrau integer default 3
)
returns jsonb
language sql
stable
security definer
set search_path to ''
as $function$
  select clube_novo.site_novo_boxes_resposta_publica_v1(
    clube_novo.site_novo_boxes_em_andamento_calculo_v1(
      p_box,p_busca,p_limite,p_offset,p_degrau
    )
  );
$function$;

create or replace function public.site_novo_boxes_v1(
  p_box text default null,
  p_busca text default '',
  p_limite integer default 24,
  p_offset integer default 0,
  p_ordem text default 'recentes',
  p_degrau integer default 3
)
returns jsonb
language sql
stable
security definer
set search_path to ''
as $function$
  select clube_novo.site_novo_boxes_resposta_publica_v1(
    clube_novo.site_novo_boxes_calculo_v1(
      p_box,p_busca,p_limite,p_offset,p_ordem,p_degrau
    )
  );
$function$;

comment on function public.site_novo_boxes_em_andamento_v1(text,text,integer,integer,integer)
is 'Boxes em andamento com etiqueta publica e calculo percentual interno.';
comment on function public.site_novo_boxes_v1(text,text,integer,integer,text,integer)
is 'Boxes cadastradas com etiqueta publica e calculo percentual interno.';

revoke all on function public.site_novo_boxes_em_andamento_v1(text,text,integer,integer,integer) from public;
revoke all on function public.site_novo_boxes_v1(text,text,integer,integer,text,integer) from public;
grant execute on function public.site_novo_boxes_em_andamento_v1(text,text,integer,integer,integer) to anon,authenticated,service_role;
grant execute on function public.site_novo_boxes_v1(text,text,integer,integer,text,integer) to anon,authenticated,service_role;
