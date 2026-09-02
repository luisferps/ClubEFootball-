-- Provas determinísticas e somente leitura do contrato V2.
with privado as (
  select
    count(*) as linhas,
    count(distinct linha_id) as linhas_distintas,
    count(distinct build_otimizador_id) as resultados_distintos,
    count(*) filter (
      where pontuacao_otimizador_bruta_selada
        <> pontuacao_otimizador_bruta_recalculada
    ) as divergencias_brutas,
    count(*) filter (
      where abs(pontuacao_normalizada_recomputada_evidencia
        - pontuacao_otimizador_normalizada)
        > 0.000000000001
    ) as divergencias_normalizacao,
    count(*) filter (
      where abs(overall_final_recomputado_evidencia - overall_final)
        > 0.000000000001
    ) as divergencias_composicao
  from clube_novo.build_pontuacao_normalizada_v2
), publicado as (
  select
    count(*) as linhas,
    count(distinct card_id) as cards,
    count(distinct (card_id, funcao_id)) as card_funcao,
    count(distinct publicacao_v2_fingerprint) as geracoes,
    count(*) filter (
      where abs(overall_final
        - (pontuacao_otimizador_normalizada + bonus_total_bonificador))
          > 0.000000000001
         or abs(percentual_topo - 100 * overall_final / topo_funcao)
          > 0.000000000001
         or estado_final <> 'publicada'
         or motivo_final <> 'PUBLICADA_V2_NORMALIZADA'
    ) as divergencias_publicas
  from clube_novo.build_pontuacao_final_v2
), paginas as (
  select
    (select count(*) from public.frontend_build_publicada_v2(null, null, 500, 0)) as pagina_1,
    (select count(*) from public.frontend_build_publicada_v2(null, null, 500, 500)) as pagina_2,
    (select count(*) from public.frontend_build_publicada_v2(null, null, 500, 1000)) as pagina_3
)
select jsonb_build_object(
  'privado', to_jsonb(privado),
  'publicado', to_jsonb(publicado),
  'paginas', to_jsonb(paginas)
) as resultado
from privado cross join publicado cross join paginas;

-- Prova com o mesmo papel do navegador.
begin;
set local role anon;
select
  (select count(*) from public.frontend_build_publicada_v2(null, null, 500, 0)) as pagina_1,
  (select count(*) from public.frontend_build_publicada_v2(null, null, 500, 500)) as pagina_2,
  (select count(*) from public.frontend_build_publicada_v2(null, null, 500, 1000)) as pagina_3,
  (select count(*) from public.frontend_build_estado_v2('52894132973575')) as status_card;
commit;
