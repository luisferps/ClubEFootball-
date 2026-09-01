-- Teste determinístico e somente leitura do contrato final V1.
-- Esperado no snapshot de 01/09/2026: 613, 613, 0, 0, 0, 0.
with resumo as (
  select
    count(*) as total_com_ambos,
    count(*) filter (where estado_final = 'bloqueada_lote_de_teste') as testes_bloqueados,
    count(*) filter (where elegivel_publicacao) as elegiveis,
    count(*) filter (where publicacao_liberada) as publicadas,
    count(*) filter (
      where pontuacao_final_candidata is distinct from
        round(pontuacao_otimizador + bonus_total_bonificador, 4)
    ) as divergencias_de_paridade
  from clube_novo.build_pontuacao_final_v1
  where build_otimizador_id is not null and build_bonificador_id is not null
), publico as (
  select count(*) as retorno_da_rpc
  from public.frontend_build_publicada_v1(null, null, 500, 0)
)
select jsonb_build_object(
  'total_com_ambos', resumo.total_com_ambos,
  'testes_bloqueados', resumo.testes_bloqueados,
  'elegiveis', resumo.elegiveis,
  'publicadas', resumo.publicadas,
  'divergencias_de_paridade', resumo.divergencias_de_paridade,
  'retorno_da_rpc', publico.retorno_da_rpc
) as resultado
from resumo cross join publico;

-- A segunda prova deve ser feita com o papel de front-end; não altera o banco.
begin;
set local role anon;
select count(*) as linhas_visiveis_ao_frontend
from public.frontend_build_publicada_v1(null, null, 500, 0);
commit;
