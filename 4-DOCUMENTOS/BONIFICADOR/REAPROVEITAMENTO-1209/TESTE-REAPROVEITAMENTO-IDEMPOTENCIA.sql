begin; set local statement_timeout='20s';
do $test$
declare a jsonb;b jsonb; original jsonb; clonado jsonb; evento integer; recusou boolean; rid bigint;
begin
 select to_jsonb(x) into original from clube_novo.build_bonificador x where id=445754;
 a:=clube_novo.reaproveitar_bonificador_conforme_v1(508099,9126,445754,'teste_rollback_1209');
 b:=clube_novo.reaproveitar_bonificador_conforme_v1(508099,9126,445754,'teste_rollback_1209');
 rid:=(a->>'build_bonificador_id')::bigint;
 if a->>'build_bonificador_id' is distinct from b->>'build_bonificador_id' or (b->>'clonado')::boolean or (b->>'vinculado')::boolean then raise exception 'idempotencia falhou'; end if;
 select to_jsonb(x) into clonado from clube_novo.build_bonificador x where id=rid;
 if not clube_novo.bonificador_resultado_conforme_componentes_v1(clonado,clube_novo.bonificador_componentes_vigentes_v1('299067699633495',1,12)) then raise exception 'clone divergiu'; end if;
 if (clonado - array['id','resultado_fingerprint','criado_em']) is distinct from (original - array['id','resultado_fingerprint','criado_em']) then raise exception 'parcelas ou selos alterados indevidamente'; end if;
 if original is distinct from (select to_jsonb(x) from clube_novo.build_bonificador x where id=445754) then raise exception 'origem alterada'; end if;
 select count(*) into evento from clube_novo.build_finalizacao_evento_v1 ev where ev.linha_id=508099 and ev.evento='bonificador_revalidado_sem_recalculo' and detalhe->>'origem'='teste_rollback_1209';
 if evento<>1 then raise exception 'auditoria nao idempotente'; end if;
 recusou:=false; begin perform clube_novo.reaproveitar_bonificador_conforme_v1(508100,9126,445754,'teste_identidade'); exception when others then if sqlerrm like '%identidade da linha%' then recusou:=true; else raise; end if; end;
 if not recusou then raise exception 'contexto divergente aceito'; end if;
 recusou:=false; begin perform clube_novo.reaproveitar_bonificador_conforme_v1(508100,9128,445754,'teste_posse'); exception when others then if sqlerrm like '%nao pertence%' then recusou:=true; else raise; end if; end;
 if not recusou then raise exception 'resultado alheio aceito'; end if;
end $test$;
rollback;
