begin;
do $test$
declare l clube_novo.build_linha_card%rowtype; q clube_novo.otimizador_lote_producao_linha_v3%rowtype; lote clube_novo.otimizador_lote_producao_v3%rowtype; msg text; entrada jsonb;
begin
 select * into l from clube_novo.build_linha_card
 where funcao_id=1 and estado_otimizador='pendente' and lote_producao_id='ddbcbc86-1ae7-4b95-b9f0-22601f41b61d' limit 1;
 if l.id is null then raise exception 'Sem controle pendente'; end if;
 select * into q from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=l.lote_producao_id and linha_id=l.id;
 select * into lote from clube_novo.otimizador_lote_producao_v3 where id=l.lote_producao_id;
 entrada:=jsonb_build_object('card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
 'formula_fingerprint',l.otimizador_formula_fingerprint_esperado,'contrato_fingerprint',l.otimizador_contrato_fingerprint_esperado,
 'motor_versao',l.otimizador_motor_versao_esperada,'carta_entrada_fingerprint',q.entrada_fingerprint,
 'lote_fingerprint',lote.fingerprint,'impeto_condicional_codigo',l.impeto_condicional_codigo,'impeto_condicional_nivel',l.impeto_condicional_nivel,
 'b1',0,'barras','{}'::jsonb,'tecnico_id',null,'habilidades','[56]'::jsonb,'builds_comparadas',0,'builds_possiveis',0);
 begin
  perform public.otimizador_producao_importar_json_local_v1(lote.id,l.id,entrada,now());
  raise exception 'FALHOU: resultado proibido foi aceito';
 exception when others then msg:=sqlerrm;
 end;
 if msg not like '%habilidade adicional proibida nesta especialidade%' then raise exception 'Teste falhou: %',msg; end if;
end $test$;
rollback;
