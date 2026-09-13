-- Decisao Luis, 08/09/2026. Aplicado ao clube_novo em 08/09/2026 17:47 BRT.
-- Apenas elegibilidade adicional. Nao refila, nao despublica, nao altera snapshots.
begin;
insert into clube_novo.habilidade_funcao_bloqueio_otimizador(skill_id,funcao_id,origem)
select 56,f,'Decisao Luis 2026-09-08: proibir Volta para marcar adicional; sem refila ou despublicacao nesta etapa'
from unnest(array[1,2,6,7,10,11,16,17,18,19]::bigint[]) f
on conflict (skill_id,funcao_id) do nothing;
commit;

