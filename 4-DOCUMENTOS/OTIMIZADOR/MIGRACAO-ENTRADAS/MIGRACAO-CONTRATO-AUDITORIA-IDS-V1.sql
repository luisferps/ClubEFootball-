begin;

create or replace function public.otimizador_ids_cartas_auditoria_v1()
returns jsonb
language sql stable security definer
set search_path=''
as $$
select coalesce(jsonb_agg(c.card_id order by c.card_id), '[]'::jsonb)
from clube_novo.carta_jogo c;
$$;

revoke all on function public.otimizador_ids_cartas_auditoria_v1()
from public, anon, authenticated;
grant execute on function public.otimizador_ids_cartas_auditoria_v1()
to service_role;

commit;
