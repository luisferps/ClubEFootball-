-- Restaurar somente a porta da Ficha; nenhum resultado sera removido.
CREATE OR REPLACE FUNCTION public.site_novo_ficha_v2(p_card_id text DEFAULT NULL::text, p_linha_id bigint DEFAULT NULL::bigint)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
with original as (
  select public.site_novo_ficha_v1(p_card_id, p_linha_id) as payload
), enriquecida as (
  select
    o.payload,
    case
      when jsonb_typeof(o.payload #> '{dados,build,impetos}') = 'array' then (
        select coalesce(
          jsonb_agg(
            elemento.item || jsonb_build_object(
              'cor_visual', cor.cor_visual,
              'cor_visual_estado', coalesce(cor.estado_validacao, 'aguardando_mapeamento')
            )
            order by elemento.ordem
          ),
          '[]'::jsonb
        )
        from jsonb_array_elements(o.payload #> '{dados,build,impetos}')
          with ordinality as elemento(item, ordem)
        left join clube_novo.impeto_jogo ij
          on ij.codigo_jogo = case
            when coalesce(elemento.item ->> 'codigo', '') ~ '^[0-9]+$'
              then (elemento.item ->> 'codigo')::integer
            else null
          end
        left join clube_novo.tipo_impeto_cor_visual_jogo cor
          on cor.tipo_raw = ij.tipo_condicao_raw
          and cor.estado_validacao = 'confirmada'
      )
      else null
    end as impetos
  from original o
)
select
  case
    when impetos is not null then jsonb_set(
      payload || jsonb_build_object(
        'contrato', 'site-novo-ficha-v2',
        'versao', 2
      ),
      '{dados,build,impetos}',
      impetos,
      true
    )
    else payload || jsonb_build_object(
      'contrato', 'site-novo-ficha-v2',
      'versao', 2
    )
  end
from enriquecida;
$function$

REVOKE ALL ON FUNCTION public.site_novo_ficha_v2(text,bigint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.site_novo_ficha_v2(text,bigint) TO anon,authenticated,service_role;
NOTIFY pgrst, 'reload schema';
