update clube_novo.funcao_sistema set rotulo=initcap(rotulo) where rotulo is distinct from initcap(rotulo);
CREATE OR REPLACE FUNCTION clube_novo.site_novo_box_card_analise_snapshot_v1(p_box_id bigint,p_card_id text,p_degrau smallint)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO ''
AS $function$
with original as (
 select coalesce(
 (select r.analises from clube_novo.box_avaliacao_revisao_0909 r where r.box_id=p_box_id and r.card_id=p_card_id and r.degrau=p_degrau),
 clube_novo.site_novo_box_card_analise_snapshot_original_0909(p_box_id,p_card_id,p_degrau)) analises
)
select case when o.analises is null then null else coalesce((
 select jsonb_agg(case when f.id is not null then jsonb_set(j.item,'{funcao}',to_jsonb(f.rotulo)) else j.item end order by j.ordem)
 from jsonb_array_elements(o.analises) with ordinality j(item,ordem)
 left join clube_novo.build_linha_card l on l.id=(j.item->>'linha_id')::bigint
 left join clube_novo.funcao_sistema f on f.id=l.funcao_id
),'[]'::jsonb) end from original o;
$function$;

-- Renomeacao aprovada posteriormente pelo usuario.
update clube_novo.funcao_sistema f set rotulo=v.novo from (values (4,'Goleiro Recuado'),(5,'Goleiro Avançado'),(6,'Lateral Recuado'),(7,'Lateral Avançado')) v(id,novo) where f.id=v.id;
