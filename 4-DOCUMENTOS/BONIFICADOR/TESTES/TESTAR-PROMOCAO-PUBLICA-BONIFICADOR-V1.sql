-- Readback somente leitura da promoção V1.
select jsonb_build_object(
  'promovidas', count(*),
  'publicadas', count(*) filter (where f.publicacao_liberada),
  'estado_publicada', count(*) filter (where f.estado_final = 'publicada'),
  'paridade_integra', count(*) filter (
    where f.pontuacao_final_candidata = round(f.pontuacao_otimizador + f.bonus_total_bonificador, 4)
  ),
  'com_selo_final', count(*) filter (where f.selo_final_fingerprint is not null)
) as readback
from clube_novo.build_pontuacao_final_v1 f
join clube_novo.bonificador_promocao_publicacao_snapshot_v1 s on s.linha_id = f.linha_id;

begin;
set local role anon;
select count(*) as linhas_visiveis_ao_frontend
from public.frontend_build_publicada_v1(null, null, 500, 0);
select count(*) as linhas_visiveis_na_segunda_pagina
from public.frontend_build_publicada_v1(null, null, 500, 500);
commit;
