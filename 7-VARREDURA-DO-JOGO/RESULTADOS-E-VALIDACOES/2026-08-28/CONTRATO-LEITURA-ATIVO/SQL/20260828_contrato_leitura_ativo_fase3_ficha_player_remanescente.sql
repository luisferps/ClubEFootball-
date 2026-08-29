-- Fase 3: todos os campos escalares de Player.bin que a ficha publicada lê.
-- Valores promovidos do mapa físico comprovado; ainda não há leitor runtime no contrato.

update clube_novo.contrato_leitura_campo
set catalogo_chave='bit',
    requisito='{"fk":"valor físico Player.bin -> playstyle.bit"}'::jsonb,
    prova='Player.bin bit 372/w8 e bit440/w6; valor físico resolve por clube_novo.playstyle.bit'
where contrato_id='clubef-dt870-2026-r1'
  and chave_campo in ('carta.playstyle.primario','carta.playstyle.secundario');

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,byte_offset,bit_inicio,largura_bits,largura_bytes,endianness,codificacao,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', a.arquivo_id, v.chave_campo, v.entidade_destino, v.tipo_leitura,
       v.byte_offset, v.bit_inicio, v.largura_bits, v.largura_bytes, v.endianness, v.codificacao,
       v.transformacao::jsonb, v.catalogo_schema, v.catalogo_tabela, v.catalogo_chave, v.requisito::jsonb,
       v.assunto, v.prova, 'comprovado'
from (values
 ('carta.altura','carta_jogo.altura','bitfield_le',null,248,8,null,'little',null,'{"operacao":"raw+100"}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin bit248/w8; altura=raw+100'),
 ('carta.peso','carta_jogo.peso','bitfield_le',null,280,7,null,'little',null,'{"operacao":"raw+30"}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin bit280/w7; peso=raw+30'),
 ('carta.idade','carta_jogo.idade','bitfield_le',null,536,6,null,'little',null,'{"operacao":"raw+10"}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin bit536/w6; idade=raw+10'),
 ('carta.pe.ruim_uso','carta_jogo.pe_ruim_uso','bitfield_le',null,478,2,null,'little',null,'{"enum":"0..3"}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin bit478/w2'),
 ('carta.pe.ruim_precisao','carta_jogo.pe_ruim_precisao','bitfield_le',null,578,2,null,'little',null,'{"enum":"0..3"}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin bit578/w2'),
 ('carta.pe','carta_jogo.pe','bitfield_le',null,654,1,null,'little',null,'{"enum":{"0":"Direito","1":"Esquerdo"}}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin bit654/w1'),
 ('carta.forma','carta_jogo.forma','bitfield_le',null,582,2,null,'little',null,'{"enum":{"0":"Inconsistent","1":"Standard","2":"Unwavering"}}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin bit582/w2'),
 ('carta.resistencia_lesao.media','carta_jogo.resistencia_lesao','bitfield_le',null,542,1,null,'little',null,'{"precedencia":"alta sobre media; 0=baixa"}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin bit542/w1; compõe resistência a lesão'),
 ('carta.resistencia_lesao.alta','carta_jogo.resistencia_lesao','bitfield_le',null,543,1,null,'little',null,'{"precedencia":"alta sobre media; 0=baixa"}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin bit543/w1; compõe resistência a lesão'),
 ('carta.nome.roman','carta_jogo.nome','fixed_utf8_nul',271,null,null,61,'not_applicable','utf-8','{"campo_nome":3,"inicio_regiao":88,"stride":61}','clube_novo','carta_jogo','card_id','{}','carta - ficha','Player.bin: região de nomes byte88; campo roman índice 3, offset271, 61 bytes UTF-8 NUL')
) as v(chave_campo,entidade_destino,tipo_leitura,byte_offset,bit_inicio,largura_bits,largura_bytes,endianness,codificacao,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,assunto,prova)
join clube_novo.contrato_leitura_arquivo a
  on a.contrato_id='clubef-dt870-2026-r1' and a.papel_fonte='dt870_updated' and a.arquivo='Player.bin'
on conflict (contrato_id,chave_campo) do nothing;
