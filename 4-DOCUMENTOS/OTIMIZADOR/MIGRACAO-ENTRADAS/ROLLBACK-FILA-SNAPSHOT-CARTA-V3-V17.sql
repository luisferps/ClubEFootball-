-- Rollback de V17. Reverte somente o endereço de leitura das fábricas novas.
-- Não toca em lotes, linhas, resultados, fórmula, pesos ou publicação.
begin;

do $rollback_v17$
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
    if position('public.otimizador_carta_v3(' in definicao)=0 then
      raise exception 'rollback V17 recusado: fábrica % não contém a leitura V3 esperada', r.oid::regprocedure;
    end if;
    execute replace(definicao,'public.otimizador_carta_v3(','public.otimizador_carta_v2(');
  end loop;
end
$rollback_v17$;

commit;
