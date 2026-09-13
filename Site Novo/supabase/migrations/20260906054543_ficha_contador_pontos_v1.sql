SET lock_timeout='3s';
-- Contador de leitura, sem alterar barras, motores ou resultados.
-- Regra conferida em 2-MOTORES/OTIMIZADOR/equacao.py:98-101 e motor.py:gasto.
CREATE OR REPLACE FUNCTION clube_novo.site_novo_contador_pontos_v1(p_barras jsonb,p_total integer)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path TO ''
AS $function$
declare
  item jsonb;
  chave text;
  valor integer;
  nivel integer;
  gasto integer := 0;
  vistas text[] := ARRAY[]::text[];
  esperadas constant text[] := ARRAY['shooting','passing','dribbling','dexterity',
    'lowerBodyStrength','aerialStrength','defending','gk1','gk2','gk3'];
  vazio jsonb := jsonb_build_object('estado','incompleto','total',p_total,'gastos',null,'restantes',null);
begin
  if p_total is null or p_total<0 or jsonb_typeof(p_barras) is distinct from 'array' then
    return vazio;
  end if;
  if jsonb_array_length(p_barras)<>10 then return vazio; end if;
  for item in select value from jsonb_array_elements(p_barras) loop
    chave := item->>'chave';
    if chave is null or not (chave=any(esperadas)) or chave=any(vistas)
      or jsonb_typeof(item->'valor') is distinct from 'number'
      or (item->>'valor') !~ '^(0|[1-9][0-9]?)$' then return vazio; end if;
    valor := (item->>'valor')::integer;
    if valor>25 then return vazio; end if;
    vistas := array_append(vistas,chave);
    for nivel in 1..valor loop gasto := gasto+(nivel+3)/4; end loop;
  end loop;
  if gasto>p_total then
    return jsonb_build_object('estado','invalido','total',p_total,'gastos',gasto,'restantes',null);
  end if;
  return jsonb_build_object('estado','valido','total',p_total,'gastos',gasto,'restantes',p_total-gasto);
end;
$function$;
REVOKE ALL ON FUNCTION clube_novo.site_novo_contador_pontos_v1(jsonb,integer) FROM PUBLIC,anon,authenticated,service_role;

CREATE OR REPLACE FUNCTION public.site_novo_ficha_v2(p_card_id text DEFAULT NULL::text, p_linha_id bigint DEFAULT NULL::bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET jit TO 'off'
AS $function$
declare
  ficha jsonb;
  impetos jsonb;
  sugestoes jsonb;
  estilos jsonb;
  pe_rotulado jsonb;
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
    if jsonb_typeof(ficha #> '{dados,card,pe}')='array' then
      select coalesce(jsonb_agg(e.item || jsonb_build_object(
        'rotulo_valor',case when p.campo='pe_dominante' then p.nome_pt else nullif(p.nome_antigo,'') end
      ) order by e.ordem),'[]'::jsonb)
      into pe_rotulado
      from jsonb_array_elements(ficha #> '{dados,card,pe}') with ordinality e(item,ordem)
      left join clube_novo.pe p on p.campo=e.item->>'campo'
        and p.valor=(e.item->>'valor')::integer;
      ficha := jsonb_set(ficha,'{dados,card,pe}',pe_rotulado);
    end if;
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
  build := build || jsonb_build_object('pontos_distribuicao',
    clube_novo.site_novo_contador_pontos_v1(build->'barras',(build->>'orcamento_total')::integer));
  return jsonb_set(ficha,'{dados,build}',build);
end;
$function$
;
NOTIFY pgrst,'reload schema';
