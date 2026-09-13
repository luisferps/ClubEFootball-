begin; set local statement_timeout='30s';
do $test$
declare first_id bigint; r jsonb; bid bigint; protegido boolean:=false;
begin
 select build_linha_card_id into first_id from public.bonificador_contexto_fila_v7(1,0);
 if first_id<>3117450 then raise exception 'prioridade mudou; conferir teste'; end if;
 r:=clube_novo.reaproveitar_bonificador_conforme_v1(3117450,3267,442812,'teste_fila_rollback');bid:=(r->>'build_bonificador_id')::bigint;
 select build_linha_card_id into first_id from public.bonificador_contexto_fila_v7(1,0);
 if first_id=3117450 then raise exception 'fila repetiu bonus conforme'; end if;
 delete from clube_novo.bonificador_conferencia_vigente_v1 where linha_id=3117450;
 select build_linha_card_id into first_id from public.bonificador_contexto_fila_v7(1,0);
 if first_id=3117450 then raise exception 'conferencia sem cache repetiu bonus conforme'; end if;
 begin update clube_novo.build_bonificador set bonus_ia=bonus_ia+0.1 where id=bid;
 exception when others then if sqlerrm like '%imutavel%' then protegido:=true; else raise; end if; end;
 if not protegido then raise exception 'resultado perdeu imutabilidade'; end if;
 select build_linha_card_id into first_id from public.bonificador_contexto_fila_v7(1,0);
 if first_id=3117450 then raise exception 'resultado conforme reapareceu'; end if;
end $test$;rollback;
