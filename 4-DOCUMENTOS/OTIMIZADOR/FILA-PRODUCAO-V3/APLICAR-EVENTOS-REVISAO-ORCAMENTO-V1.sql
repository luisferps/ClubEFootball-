-- Amplia apenas os eventos aceitos, preservando a expressão vigente.
begin;
do $$
declare v_expr text;
begin
 select pg_get_expr(conbin,conrelid) into v_expr
 from pg_constraint where conrelid='clube_novo.otimizador_evento_producao_v3'::regclass
   and conname='otimizador_evento_producao_v3_evento_check';
 if v_expr is null then raise exception 'Constraint de eventos não encontrada'; end if;
 if position('prioridade_orcamento_reordenada' in v_expr)=0
    or position('revisao_orcamento_preparada' in v_expr)=0 then
   alter table clube_novo.otimizador_evento_producao_v3 drop constraint otimizador_evento_producao_v3_evento_check;
   execute format('alter table clube_novo.otimizador_evento_producao_v3 add constraint otimizador_evento_producao_v3_evento_check check ((%s) or evento in (%L,%L))',
     v_expr,'prioridade_orcamento_reordenada','revisao_orcamento_preparada');
 end if;
end $$;
commit;

