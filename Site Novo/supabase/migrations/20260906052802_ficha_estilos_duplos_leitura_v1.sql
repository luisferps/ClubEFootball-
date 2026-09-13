-- Ficha: os dois estilos fisicos e composicao unica dos metadados de consulta.
SET lock_timeout='3s';
CREATE OR REPLACE FUNCTION public.site_novo_ficha_v2(p_card_id text DEFAULT NULL::text, p_linha_id bigint DEFAULT NULL::bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path TO ''
AS $function$
declare
  ficha jsonb;
  impetos jsonb;
  sugestoes jsonb;
  estilos jsonb;
  build jsonb;
  tecnico jsonb;
begin
  ficha := public.site_novo_ficha_v1(p_card_id,p_linha_id)
    || jsonb_build_object('contrato','site-novo-ficha-v2','versao',2);
  if jsonb_typeof(ficha #> '{dados,card}') = 'object' then
    select coalesce(jsonb_agg(jsonb_build_object(
      'id',p.id_jogo,'slot',cp.slot_fisico,
      'tipo',case cp.slot_fisico when 1 then 'ofensivo' when 2 then 'defensivo' end,
      'nome',coalesce(p.nome_tela,p.nome_pt,p.nome_en)
    ) order by cp.slot_fisico,p.id_jogo),'[]'::jsonb)
    into estilos
    from clube_novo.carta_playstyle_jogo cp
    join clube_novo.playstyle p on p.id_jogo=cp.playstyle_id
    where cp.card_id=ficha #>> '{dados,card,card_id}';
    ficha := jsonb_set(ficha,'{dados,card,estilos_jogo}',estilos);
  end if;
  build := ficha #> '{dados,build}';
  if jsonb_typeof(build) <> 'object' or build is null then
    return ficha;
  end if;
  if jsonb_typeof(build->'impetos') = 'array' then
    select coalesce(jsonb_agg(elemento.item || jsonb_build_object(
      'cor_visual',cor.cor_visual,
      'cor_visual_estado',coalesce(cor.estado_validacao,'aguardando_mapeamento')
    ) order by elemento.ordem),'[]'::jsonb)
    into impetos
    from jsonb_array_elements(build->'impetos') with ordinality elemento(item,ordem)
    left join clube_novo.impeto_jogo ij on ij.codigo_jogo=case
      when coalesce(elemento.item->>'codigo','') ~ '^[0-9]+$'
      then (elemento.item->>'codigo')::integer else null end
    left join clube_novo.tipo_impeto_cor_visual_jogo cor
      on cor.tipo_raw=ij.tipo_condicao_raw and cor.estado_validacao='confirmada';
    build := jsonb_set(build,'{impetos}',impetos);
  end if;
  sugestoes := clube_novo.site_novo_ficha_sugestoes_v1(
    ficha #>> '{dados,card,card_id}',(build->>'linha_id')::bigint);
  build := build || jsonb_build_object(
    'habilidades_sugeridas',sugestoes->'habilidades',
    'habilidades_sugeridas_estado',sugestoes->>'estado');
  tecnico := build->'tecnico';
  if jsonb_typeof(tecnico)='object' then
    build := jsonb_set(build,'{tecnico}',tecnico || jsonb_build_object(
      'sugeridos',sugestoes->'tecnicos','sugeridos_estado',sugestoes->>'estado'));
  end if;
  return jsonb_set(ficha,'{dados,build}',build);
end;
$function$;
REVOKE ALL ON FUNCTION public.site_novo_ficha_v2(text,bigint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.site_novo_ficha_v2(text,bigint) TO anon,authenticated,service_role;
NOTIFY pgrst,'reload schema';
