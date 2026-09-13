begin; set local statement_timeout='20s';
do $test$
declare cid text:='299067699633495'; capdata timestamptz; r jsonb; corpo text; valor_antigo integer; recusou boolean:=false;
begin
 select extraido_em into capdata from clube_novo.carta_jogo where card_id=cid;
 insert into clube_novo.valor_do_dono(destino_schema,destino_tabela,chave,coluna,valor,porque)
 values('clube_novo','carta_jogo',jsonb_build_object('card_id',cid),'extraido_em',to_jsonb(capdata+interval '1 minute'),'teste revalidacao rollback');
 update clube_novo.build_linha_card set carta_versao=(select extraido_em::text from clube_novo.carta_jogo where card_id=cid),carta_fingerprint=clube_novo.bonificador_carta_fingerprint_v1(cid) where id=508099;
 r:=clube_novo.reaproveitar_bonificador_conforme_v1(508099,9126,445754,'teste_metadata_rollback');
 if coalesce((r->>'sem_recalculo')::boolean,false)=false then raise exception 'metadata exigiu recalculo'; end if;
 select codigo_corpo,valor into corpo,valor_antigo from clube_novo.carta_corpo_jogo where card_id=cid and valor between 0 and 14 limit 1;
 if corpo is null then raise exception 'sem medida para teste'; end if;
 update clube_novo.carta_corpo_jogo set valor=valor_antigo+1 where card_id=cid and codigo_corpo=corpo;
 update clube_novo.build_linha_card set carta_fingerprint=clube_novo.bonificador_carta_fingerprint_v1(cid) where id=508100;
 update clube_novo.build_linha_card set carta_versao=(select extraido_em::text from clube_novo.carta_jogo where card_id=cid) where id=508100;
 begin perform clube_novo.reaproveitar_bonificador_conforme_v1(508100,9128,445755,'teste_corpo_rollback');
 exception when others then if sqlerrm like '%igualdade das entradas%' then recusou:=true; else raise; end if; end;
 if not recusou then raise exception 'corpo alterado foi aceito'; end if;
end $test$; rollback;
