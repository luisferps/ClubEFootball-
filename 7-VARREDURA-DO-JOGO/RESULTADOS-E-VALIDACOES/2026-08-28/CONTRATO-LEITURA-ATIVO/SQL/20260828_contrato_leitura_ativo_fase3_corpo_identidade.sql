-- Chave de junção da família física PlayerAppearance.bin.
insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,byte_offset,largura_bytes,endianness,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1',a.arquivo_id,'carta.corpo.card_id','carta_jogo.card_id','byte_le',0,8,'little',
       '{"identidade":"u64","junção":"card_id"}'::jsonb,'clube_novo','carta_jogo','card_id','{"unico":true}',
       'corpo (12 medidas)','PlayerAppearance.bin offset0 u64; chave física de junção do corpo','comprovado'
from clube_novo.contrato_leitura_arquivo a
where a.contrato_id='clubef-dt870-2026-r1' and a.papel_fonte='dt870_updated' and a.arquivo='PlayerAppearance.bin'
on conflict (contrato_id,chave_campo) do nothing;
