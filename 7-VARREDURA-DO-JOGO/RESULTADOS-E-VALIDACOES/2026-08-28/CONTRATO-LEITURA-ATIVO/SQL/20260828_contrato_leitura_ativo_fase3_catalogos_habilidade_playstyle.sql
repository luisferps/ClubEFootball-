-- Fase 3: dois catálogos físicos usados pelo núcleo e pelas relações.
-- Fonte comprovada no dt870 atualizado; promoção para rascunho, sem carga.

insert into clube_novo.contrato_leitura_arquivo
  (contrato_id,papel_fonte,arquivo,cpk,versao_arquivo,sha256_arquivo,tamanho_registro,prefixo_bytes,decodificador,obrigatorio,proveniencia)
values
  ('clubef-dt870-2026-r1','dt870_updated','PlayerSkill.bin','dt870_console_win.cpk','dt870-2026-atualizacao','0028916b9904fcc03b9862b3cc6bf084048e5d6c54dea7dcefe4e64d35b07795',104,0,'wesys_raw',true,'releitura física do catálogo ativo; extractMetadataFromCpk'),
  ('clubef-dt870-2026-r1','dt870_updated','Playstyle.bin','dt870_console_win.cpk','dt870-2026-atualizacao','67a3f34ba9c63e5b84396e2891e3b0ac10a315125f4a6ae0eebeb032a06d0d38',168,0,'wesys_raw',true,'releitura física do catálogo ativo; extractMetadataFromCpk')
on conflict (contrato_id,papel_fonte,arquivo) do nothing;

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,byte_offset,largura_bytes,endianness,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', a.arquivo_id,
       'catalogo.habilidade.id','habilidade_jogo.skill_id','byte_le',0,4,'little',
       '{"identidade":"u32"}'::jsonb,'clube_novo','habilidade_jogo','skill_id',
       '{"unico":true,"registros_fisicos":72}'::jsonb,'habilidade_jogo.endereco',
       'PlayerSkill.bin: 72 registros de 104 bytes; skill_id u32 little-endian no offset 0','comprovado'
from clube_novo.contrato_leitura_arquivo a
where a.contrato_id='clubef-dt870-2026-r1' and a.papel_fonte='dt870_updated' and a.arquivo='PlayerSkill.bin'
on conflict (contrato_id,chave_campo) do nothing;

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,byte_offset,largura_bytes,endianness,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', a.arquivo_id,
       'catalogo.playstyle.id','playstyle.id_jogo','byte_le',0,4,'little',
       '{"identidade":"u32"}'::jsonb,'clube_novo','playstyle','id_jogo',
       '{"unico":true,"registros_fisicos":36}'::jsonb,'playstyle.endereco',
       'Playstyle.bin: 36 registros de 168 bytes; id_jogo u32 little-endian no offset 0','comprovado'
from clube_novo.contrato_leitura_arquivo a
where a.contrato_id='clubef-dt870-2026-r1' and a.papel_fonte='dt870_updated' and a.arquivo='Playstyle.bin'
on conflict (contrato_id,chave_campo) do nothing;
