begin;
insert into clube_novo.contrato_leitura_catalogo_fisico
 (contrato_id,catalogo_schema,catalogo_tabela,modo_validacao,artefato_fisico,coluna_chave_fisica,colunas_chave_canonica,papel_fonte,familia_dependencia,check_dependencia,proveniencia)
values ('clubef-dt870-2026-r1','clube_novo','estilo_ia','dependencia_normalizada',null,'bit',array['bit'],'dt870_updated','relacoes','relacoes_normalizadas','sete bits comprovados Player.bin; conjunto derivado por bit e fingerprint da relação')
on conflict do nothing;
commit;
