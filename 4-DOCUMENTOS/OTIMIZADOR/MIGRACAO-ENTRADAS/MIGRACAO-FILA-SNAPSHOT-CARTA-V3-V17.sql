-- V17 — A criação de novas filas sela a carta pelo contrato V3.
--
-- A alteração é cirúrgica: somente troca a chamada de leitura
-- public.otimizador_carta_v2(card_id) por public.otimizador_carta_v3(card_id)
-- nas três fábricas de lote. Fórmula, pesos, seleção, ordem e escrita da fila
-- permanecem byte a byte como estavam. Lotes já selados não são alterados.

begin;

do $v17$
declare
  r record;
  definicao text;
begin
  for r in
    select v.oid
    from (values
      ('public.otimizador_criar_amostra_teste_v3(uuid,text,text,text,text)'::regprocedure),
      ('public.otimizador_criar_amostra_controlada_50_v2(uuid,text,text,text,text,jsonb)'::regprocedure),
      ('public.otimizador_criar_fila_comparacao_legado_50_v1(uuid,text,text,text,text)'::regprocedure)
    ) as v(oid)
  loop
    select pg_get_functiondef(r.oid) into definicao;
    if position('public.otimizador_carta_v2(' in definicao)=0 then
      raise exception 'V17 recusada: fábrica % não contém a leitura V2 esperada', r.oid::regprocedure;
    end if;
    execute replace(definicao,'public.otimizador_carta_v2(','public.otimizador_carta_v3(');
  end loop;
end
$v17$;

revoke all on function public.otimizador_criar_amostra_teste_v3(uuid,text,text,text,text)
  from public, anon, authenticated;
revoke all on function public.otimizador_criar_amostra_controlada_50_v2(uuid,text,text,text,text,jsonb)
  from public, anon, authenticated;
revoke all on function public.otimizador_criar_fila_comparacao_legado_50_v1(uuid,text,text,text,text)
  from public, anon, authenticated;
grant execute on function public.otimizador_criar_amostra_teste_v3(uuid,text,text,text,text) to service_role;
grant execute on function public.otimizador_criar_amostra_controlada_50_v2(uuid,text,text,text,text,jsonb) to service_role;
grant execute on function public.otimizador_criar_fila_comparacao_legado_50_v1(uuid,text,text,text,text) to service_role;

commit;
