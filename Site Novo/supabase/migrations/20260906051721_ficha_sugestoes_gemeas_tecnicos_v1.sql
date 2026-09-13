-- Leitura de sugestoes para a Ficha. Preserva os resultados dos motores e a publicacao.
SET lock_timeout = '3s';
CREATE OR REPLACE FUNCTION clube_novo.site_novo_ficha_sugestoes_v1(p_card_id text, p_linha_id bigint)
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path TO ''
AS $function$
with contexto as materialized (
  select a.linha_id, a.card_id, a.funcao_id, b.tecnico_id,
         b.habilidades_adicionais, b.arows_snapshot, l.regua_snapshot as regua
  from clube_novo.build_publicacao_linha_ativa_v1 a
  join clube_novo.build_otimizador b on b.id = a.build_otimizador_id
  join clube_novo.otimizador_lote_producao_linha_v3 pl
    on pl.linha_id = a.linha_id and pl.resultado_fingerprint = b.resultado_fingerprint
  join clube_novo.otimizador_lote_producao_v3 l on l.id = pl.lote_id
  where a.card_id = p_card_id and a.linha_id = p_linha_id
), habilidades as materialized (
  select (h.item->>'skill_id')::integer as id, h.item,
    (select jsonb_agg(e.item order by e.item->>'codigo_atributo')
     from jsonb_array_elements(h.item->'efeitos') e(item)) as efeitos
  from contexto c cross join lateral jsonb_array_elements(c.regua->'habilidades') h(item)
), bloqueios as materialized (
  select (b.item->>'skill_id')::integer as id
  from contexto c cross join lateral jsonb_array_elements(c.regua->'bloqueios') b(item)
  where (b.item->>'funcao_id')::bigint = c.funcao_id
), incidencias as materialized (
  select (i.item->>'skill_id')::integer as id, (i.item->>'incidencia_pct')::numeric as pct
  from contexto c cross join lateral jsonb_array_elements(c.regua->'incidencias') i(item)
  where (i.item->>'funcao_id')::bigint = c.funcao_id
), pares as (
  select distinta.id, hg.nome_pt as nome, hg.ordem,
         coalesce(i.pct, 0) as incidencia,
         escolhida.skill_id as substitui_id, origem.nome_pt as substitui_nome,
         escolhida.ordem as ordem_escolhida
  from contexto c
  cross join lateral unnest(c.habilidades_adicionais) with ordinality escolhida(skill_id, ordem)
  join clube_novo.habilidade_jogo origem on origem.skill_id = escolhida.skill_id
  join habilidades atual on atual.id = escolhida.skill_id
  join habilidades distinta on distinta.id = any(origem.gemeas)
    and distinta.efeitos = atual.efeitos
    and distinta.item->>'tipo' = atual.item->>'tipo'
  join clube_novo.habilidade_jogo hg on hg.skill_id = distinta.id
  left join incidencias i on i.id = distinta.id
  where atual.item->>'fabricavel' = 'true'
    and distinta.item->>'fabricavel' = 'true'
    and distinta.item->>'pode_rodar' = 'true'
    and distinta.item->>'vetada' = 'false'
    and not (distinta.id = any(c.habilidades_adicionais))
    and not exists (select 1 from clube_novo.carta_habilidade_jogo n where n.card_id=c.card_id and n.skill_id=distinta.id)
    and not exists (select 1 from bloqueios v where v.id=distinta.id)
), gemeas as (
  select id,nome,ordem,incidencia,
    jsonb_agg(jsonb_build_object('id',substitui_id,'nome',substitui_nome) order by ordem_escolhida) as substitui
  from pares group by id,nome,ordem,incidencia
), pesos as materialized (
  select (p.item->>0)::integer as indice
  from contexto c cross join lateral jsonb_array_elements(c.arows_snapshot) p(item)
  where jsonb_array_length(c.arows_snapshot)=26 and (p.item->>1)::numeric <> 0
), tecnicos as materialized (
  select (t.item->>'tecnico_id')::bigint as id, t.item,
         c.regua->'multiplicadores'->(t.item->>'proficiencia_maxima') as multiplicador,
         (select coalesce(jsonb_agg(jsonb_build_object('indice', (b.item->>'indice_otimizador')::integer,
                    'delta', (b.item->>'delta')::numeric) order by (b.item->>'indice_otimizador')::integer), '[]'::jsonb)
          from jsonb_array_elements(t.item->'boosts') b(item)
          join pesos p on p.indice=(b.item->>'indice_otimizador')::integer) as efeitos
  from contexto c cross join lateral jsonb_array_elements(c.regua->'tecnicos') t(item)
  where exists (select 1 from pesos)
), equivalentes as (
  select t.id,j.nome_en as nome,
    (select jsonb_agg(jsonb_build_object('codigo',e.item->>'codigo_estilo','nome',ej.nome_pt,
                          'proficiencia',(e.item->>'valor')::integer) order by ej.ordem)
     from jsonb_array_elements(t.item->'estilos_principais') e(item)
     join clube_novo.estilo_jogo_tecnico ej on ej.codigo=e.item->>'codigo_estilo') as estilos
  from contexto c join tecnicos escolhido on escolhido.id=c.tecnico_id
  join tecnicos t on t.id <> escolhido.id and t.multiplicador=escolhido.multiplicador and t.efeitos=escolhido.efeitos
  join clube_novo.tecnico_jogo j on j.id=t.id
  where jsonb_typeof(t.multiplicador)='number'
)
select jsonb_build_object(
  'estado', case when exists (select 1 from contexto) then 'pronto' else 'nao_publicado' end,
  'habilidades', coalesce((select jsonb_agg(jsonb_build_object('id',id,'nome',nome,'substitui',substitui)
                         order by incidencia desc,ordem,id) from gemeas), '[]'::jsonb),
  'tecnicos', coalesce((select jsonb_agg(jsonb_build_object('id',id,'nome',nome,'estilos',estilos) order by nome,id)
                      from equivalentes), '[]'::jsonb)
);
$function$;
REVOKE ALL ON FUNCTION clube_novo.site_novo_ficha_sugestoes_v1(text,bigint) FROM PUBLIC,anon,authenticated,service_role;
COMMENT ON FUNCTION clube_novo.site_novo_ficha_sugestoes_v1(text,bigint) IS 'Sugestoes de leitura da linha publicada: gemeas fabricaveis com efeito identico no snapshot e lista explicita de substituicoes; tecnicos com mesmo multiplicador e deltas nos atributos pontuados. Nenhuma alteracao ou recalculo de build.';

CREATE OR REPLACE FUNCTION public.site_novo_ficha_v2(p_card_id text DEFAULT NULL::text, p_linha_id bigint DEFAULT NULL::bigint)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO ''
AS $function$
with original as materialized (
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
), com_cores as materialized (

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
  end as payload
from enriquecida
)
select case when jsonb_typeof(c.payload #> '{dados,build}') = 'object' then
 jsonb_set(c.payload, '{dados,build}',
  (c.payload #> '{dados,build}') || jsonb_build_object(
   'habilidades_sugeridas', s.sugestoes->'habilidades',
   'habilidades_sugeridas_estado', s.sugestoes->>'estado',
   'tecnico', case when jsonb_typeof(c.payload #> '{dados,build,tecnico}') = 'object'
      then (c.payload #> '{dados,build,tecnico}') || jsonb_build_object(
         'sugeridos',s.sugestoes->'tecnicos','sugeridos_estado',s.sugestoes->>'estado')
      else c.payload #> '{dados,build,tecnico}' end
  ))
 else c.payload end
from com_cores c
cross join lateral (
 select clube_novo.site_novo_ficha_sugestoes_v1(
  c.payload #>> '{dados,card,card_id}',
  (c.payload #>> '{dados,build,linha_id}')::bigint
 ) as sugestoes
 offset 0
) s;
$function$;
REVOKE ALL ON FUNCTION public.site_novo_ficha_v2(text,bigint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.site_novo_ficha_v2(text,bigint) TO anon,authenticated,service_role;
NOTIFY pgrst, 'reload schema';
