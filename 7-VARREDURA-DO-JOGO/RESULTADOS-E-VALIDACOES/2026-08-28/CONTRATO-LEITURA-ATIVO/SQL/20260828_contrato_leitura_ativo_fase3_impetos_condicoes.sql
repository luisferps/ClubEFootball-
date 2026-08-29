-- Fase 3: campos físicos que descrevem alvo, classe, faixas e expansão de liga.
-- O contrato descreve a extração; não habilita fórmula, consumidor nem qualquer escrita de domínio.

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,byte_offset,bit_inicio,largura_bits,largura_bytes,endianness,codificacao,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', a.arquivo_id, v.chave_campo, v.entidade_destino, v.tipo_leitura,
       v.byte_offset::integer, v.bit_inicio::integer, v.largura_bits::smallint, v.largura_bytes::integer, v.endianness, v.codificacao,
       v.transformacao::jsonb, v.catalogo_schema, v.catalogo_tabela, v.catalogo_chave, v.requisito::jsonb,
       v.assunto, v.prova, 'comprovado'
from (values
 ('impeto.condicao.nacionalidade','impeto_condicao_nacionalidade_jogo.codigo_nacionalidade','bitfield_le',null,128,9,null,'little',null,'{"modo":"alvo"}','clube_novo','nacionalidade_jogo','codigo_jogo','{"fk":"codigo_nacionalidade"}','impeto - catalogo','PlayerBooster.bin bit128/w9'),
 ('impeto.condicao.liga','impeto_condicao_liga_jogo.codigo_liga_categoria','bitfield_le',null,96,16,null,'little',null,'{"modo":"alvo"}','clube_novo','liga_jogo','codigo_jogo','{"fk":"codigo_liga_categoria"}','impeto - catalogo','PlayerBooster.bin bit96/w16'),
 ('impeto.condicao.clube','impeto_condicao_clube_jogo.codigo_clube','bitfield_le',null,32,18,null,'little',null,'{"modo":"alvo"}','clube_novo','clube_jogo','codigo_jogo','{"fk":"codigo_clube"}','impeto - catalogo','PlayerBooster.bin bit32/w18'),
 ('impeto.condicao.classe_dono','impeto_condicao_classe_jogo.classe_dono','bitfield_le',null,302,3,null,'little',null,'{}','clube_novo','impeto_condicao_classe_jogo','classe_dono','{}','impeto - catalogo','PlayerBooster.bin bit302/w3'),
 ('impeto.condicao.classe_candidato','impeto_classe_candidato_jogo.classe_candidato','bitfield_le',null,299,3,null,'little',null,'{}','clube_novo','impeto_classe_candidato_jogo','classe_candidato','{}','impeto - catalogo','PlayerBooster.bin bit299/w3'),
 ('impeto.condicao.faixa.corte','impeto_condicao_parametro_faixa_jogo.corte_raw','bitfield_le',null,207,5,null,'little',null,'{}','clube_novo','impeto_condicao_parametro_faixa_jogo','corte_raw','{}','impeto - catalogo','PlayerBooster.bin bit207/w5'),
 ('impeto.condicao.faixa.efeito_maximo','impeto_condicao_parametro_faixa_jogo.efeito_maximo','bitfield_le',null,212,5,null,'little',null,'{}','clube_novo','impeto_condicao_parametro_faixa_jogo','efeito_maximo','{}','impeto - catalogo','PlayerBooster.bin bit212/w5')
) as v(chave_campo,entidade_destino,tipo_leitura,byte_offset,bit_inicio,largura_bits,largura_bytes,endianness,codificacao,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,assunto,prova)
join clube_novo.contrato_leitura_arquivo a
  on a.contrato_id='clubef-dt870-2026-r1' and a.papel_fonte='dt870_updated' and a.arquivo='PlayerBooster.bin'
on conflict (contrato_id,chave_campo) do nothing;

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,byte_offset,largura_bytes,endianness,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', a.arquivo_id, v.chave_campo, v.entidade_destino, 'byte_le',
       v.byte_offset::integer, 2, 'little', v.transformacao::jsonb,
       'clube_novo','impeto_condicao_liga_membro_jogo','codigo_liga_membro','{}'::jsonb,
       'liga.catalogo',v.prova,'comprovado'
from (values
 ('impeto.liga_membro.anterior','impeto_condicao_liga_membro_jogo.codigo_liga_membro',4,'{"papel":"vinculo_anterior","sentinela":65535}','CompetitionUnit.bin offset4 u16; membro anterior'),
 ('impeto.liga_membro.base','impeto_condicao_liga_membro_jogo.codigo_liga_membro',10,'{"papel":"alvo_base"}','CompetitionUnit.bin offset10 u16; liga alvo base'),
 ('impeto.liga_membro.posterior','impeto_condicao_liga_membro_jogo.codigo_liga_membro',6,'{"papel":"vinculo_posterior","sentinela":65535}','CompetitionUnit.bin offset6 u16; membro posterior')
) as v(chave_campo,entidade_destino,byte_offset,transformacao,prova)
join clube_novo.contrato_leitura_arquivo a
  on a.contrato_id='clubef-dt870-2026-r1' and a.papel_fonte='dt870_updated' and a.arquivo='CompetitionUnit.bin'
on conflict (contrato_id,chave_campo) do nothing;
