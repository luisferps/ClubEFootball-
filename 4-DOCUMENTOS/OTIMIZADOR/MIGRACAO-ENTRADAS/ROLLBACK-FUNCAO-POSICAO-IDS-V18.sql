-- Rollback de V18. Repõe apenas a antiga referência textual nas fábricas e
-- remove a relação auxiliar; não toca nos 19 moldes, linhas, builds ou fórmula.
begin;

do $rollback_v18$
declare
  r record;
  definicao text;
  antigo constant text := 'exists(select 1 from clube_novo.otimizador_funcao_posicao fp where fp.funcao_id=fs.id and fp.posicao_id=p.id)';
  novo constant text := 'p.codigo_pt=any(fs.posicoes)';
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
    if position(antigo in definicao)=0 then
      raise exception 'rollback V18 recusado: fábrica % não contém a referência por ID esperada',r.oid::regprocedure;
    end if;
    execute replace(definicao,antigo,novo);
  end loop;
end
$rollback_v18$;

drop table if exists clube_novo.otimizador_funcao_posicao;

commit;
