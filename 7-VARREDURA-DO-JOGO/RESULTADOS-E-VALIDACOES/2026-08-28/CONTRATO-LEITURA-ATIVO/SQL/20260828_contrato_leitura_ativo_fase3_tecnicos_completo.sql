-- Fase 3: identificador, nomes, cinco proficiências e boosts de Coach.bin.
-- Mantém Técnico no rascunho de leitura; nenhuma carga em tecnico_jogo é executada aqui.

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,byte_offset,bit_inicio,largura_bits,largura_bytes,endianness,codificacao,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', a.arquivo_id, v.chave_campo, v.entidade_destino, v.tipo_leitura,
       v.byte_offset, v.bit_inicio, v.largura_bits, v.largura_bytes, v.endianness, v.codificacao,
       v.transformacao::jsonb, v.catalogo_schema, v.catalogo_tabela, v.catalogo_chave, v.requisito::jsonb,
       v.assunto, v.prova, 'comprovado'
from (values
 ('tecnico.id','tecnico_jogo.id','byte_le',0,null,null,8,'little',null,'{"identidade":"u64"}','clube_novo','tecnico_jogo','id','{"unico":true}','tecnico','Coach.bin offset0 u64 little-endian'),
 ('tecnico.nome.jp','tecnico_jogo.nome_jp','fixed_utf8_nul',32,null,null,46,'not_applicable','utf-8','{}','clube_novo','tecnico_jogo','id','{}','tecnico','Coach.bin byte32/46 UTF-8 NUL'),
 ('tecnico.nome.en','tecnico_jogo.nome_en','fixed_utf8_nul',78,null,null,46,'not_applicable','utf-8','{}','clube_novo','tecnico_jogo','id','{}','tecnico','Coach.bin byte78/46 UTF-8 NUL'),
 ('tecnico.nome.cn','tecnico_jogo.nome_cn','fixed_utf8_nul',124,null,null,52,'not_applicable','utf-8','{}','clube_novo','tecnico_jogo','id','{}','tecnico','Coach.bin byte124/52 UTF-8 NUL'),
 ('tecnico.proficiencia.possession_game','tecnico_estilo_jogo.proficiencia','bitfield_le',null,206,7,null,'little',null,'{"codigo_estilo":"possessionGame"}','clube_novo','estilo_jogo_tecnico','codigo','{"fk":"tecnico_estilo_jogo.codigo_estilo"}','tecnico','Coach.bin bit206/w7'),
 ('tecnico.proficiencia.long_ball_counter','tecnico_estilo_jogo.proficiencia','bitfield_le',null,238,7,null,'little',null,'{"codigo_estilo":"longBallCounter"}','clube_novo','estilo_jogo_tecnico','codigo','{"fk":"tecnico_estilo_jogo.codigo_estilo"}','tecnico','Coach.bin bit238/w7'),
 ('tecnico.proficiencia.quick_counter','tecnico_estilo_jogo.proficiencia','bitfield_le',null,224,7,null,'little',null,'{"codigo_estilo":"quickCounter"}','clube_novo','estilo_jogo_tecnico','codigo','{"fk":"tecnico_estilo_jogo.codigo_estilo"}','tecnico','Coach.bin bit224/w7'),
 ('tecnico.proficiencia.long_ball','tecnico_estilo_jogo.proficiencia','bitfield_le',null,199,7,null,'little',null,'{"codigo_estilo":"longBall"}','clube_novo','estilo_jogo_tecnico','codigo','{"fk":"tecnico_estilo_jogo.codigo_estilo"}','tecnico','Coach.bin bit199/w7'),
 ('tecnico.proficiencia.out_wide','tecnico_estilo_jogo.proficiencia','bitfield_le',null,213,7,null,'little',null,'{"codigo_estilo":"outWide"}','clube_novo','estilo_jogo_tecnico','codigo','{"fk":"tecnico_estilo_jogo.codigo_estilo"}','tecnico','Coach.bin bit213/w7'),
 ('tecnico.boost.1','tecnico_atributo_jogo.codigo_atributo','bitfield_le',null,160,5,null,'little',null,'{"zero":"ausencia_legitima","indice_atributo":"raw-1","delta":1,"ordem":1}','clube_novo','atributo_ordem_otimizador','indice_otimizador','{"fk":"indice 0..25 -> atributo_ordem_otimizador"}','tecnico','Coach.bin bit160/w5'),
 ('tecnico.boost.2','tecnico_atributo_jogo.codigo_atributo','bitfield_le',null,148,5,null,'little',null,'{"zero":"ausencia_legitima","indice_atributo":"raw-1","delta":1,"ordem":2}','clube_novo','atributo_ordem_otimizador','indice_otimizador','{"fk":"indice 0..25 -> atributo_ordem_otimizador"}','tecnico','Coach.bin bit148/w5')
) as v(chave_campo,entidade_destino,tipo_leitura,byte_offset,bit_inicio,largura_bits,largura_bytes,endianness,codificacao,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,assunto,prova)
join clube_novo.contrato_leitura_arquivo a
  on a.contrato_id='clubef-dt870-2026-r1' and a.papel_fonte='dt870_updated' and a.arquivo='Coach.bin'
on conflict (contrato_id,chave_campo) do nothing;
