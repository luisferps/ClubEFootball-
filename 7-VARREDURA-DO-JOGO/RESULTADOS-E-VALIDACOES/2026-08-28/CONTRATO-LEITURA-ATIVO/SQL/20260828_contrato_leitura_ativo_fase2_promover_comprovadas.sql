-- Fase 2: referências físicas comprovadas, promovidas como rascunho não executável.
-- Os fingerprints 00..00 são sentinelas de rascunho: o CHECK impede ativação antes do cálculo integral.

insert into clube_novo.contrato_leitura_jogo
  (contrato_id, versao_jogo, versao_contrato, fingerprint_contrato_sha256, fingerprint_fontes_sha256, estado, politica_fonte, cobertura_total, observacao)
values
  ('clubef-dt870-2026-r1', 'dt870-2026-atualizacao', 'r1', repeat('0', 64), repeat('0', 64), 'rascunho',
   '{"fonte_ativa":"dt870_updated","texto_pt_br":"dt261_bra","modo":"somente_leitura","fallback_numerico":"proibido"}'::jsonb,
   false, 'Fase 2: somente campos com prova física e hash de arquivo; ainda não é contrato executável.')
on conflict (contrato_id) do nothing;

insert into clube_novo.contrato_leitura_arquivo
  (contrato_id,papel_fonte,arquivo,cpk,versao_arquivo,sha256_arquivo,tamanho_registro,prefixo_bytes,decodificador,obrigatorio,proveniencia)
values
  ('clubef-dt870-2026-r1','dt870_updated','Player.bin','dt870_console_win.cpk','dt870-2026-atualizacao','2afe17a686bef320dce3c4096355ba99b56bfb8a42b08018f0ae2fe444b05853',400,0,'wesys_raw',true,'clube_novo.mapa_do_jogo + validação física de cartas'),
  ('clubef-dt870-2026-r1','dt870_updated','Coach.bin','dt870_console_win.cpk','dt870-2026-atualizacao','092a07c62d1df0f19da6ad0e4e1252de07e5e1df8e9090760734829044c0d42a',176,0,'wesys_raw',true,'clube_novo.mapa_do_jogo + validação física de técnicos'),
  ('clubef-dt870-2026-r1','dt870_updated','Country.bin','dt870_console_win.cpk','dt870-2026-atualizacao','6dcb876a1922281cc5bf513f8ee117846fbeed42e48936f40af2007232c1b0a7',1488,0,'wesys_raw',true,'clube_novo.mapa_do_jogo + validação física de nacionalidades'),
  ('clubef-dt870-2026-r1','dt261_bra','all.str','dt261_bra_console_win.cpk','dt261-bra-ptbr','306741adab8376ed64620b618ae9721d316ae548b126419730b9bd5ff5f525a9',null,0,'all_str_v1',true,'clube_novo.mapa_do_jogo + leitor canônico de textos')
on conflict (contrato_id,papel_fonte,arquivo) do nothing;

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,byte_offset,bit_inicio,largura_bits,largura_bytes,endianness,codificacao,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', a.arquivo_id, v.chave_campo, v.entidade_destino, v.tipo_leitura,
       v.byte_offset, v.bit_inicio, v.largura_bits, v.largura_bytes, v.endianness, v.codificacao,
       v.transformacao::jsonb, v.catalogo_schema, v.catalogo_tabela, v.catalogo_chave, v.requisito::jsonb,
       v.assunto, v.prova, 'comprovado'
from (values
  ('dt870_updated','Player.bin','carta.id','carta_jogo.card_id','byte_le',8,null,null,8,'little',null,'{}','clube_novo','carta_jogo','card_id','{"identidade":"u64"}','carta - ficha','card_id u64 no offset 8; registro Player.bin 400 bytes'),
  ('dt870_updated','Player.bin','carta.clube.codigo','carta_jogo.codigo_clube','byte_le',16,null,null,4,'little',null,'{}','clube_novo','clube_jogo','codigo_jogo','{"fk":"carta_jogo.codigo_clube -> clube_jogo.codigo_jogo"}','carta.clube','Player.bin offset 16 u32 little-endian'),
  ('dt870_updated','Player.bin','carta.nacionalidade.raw','carta_jogo.codigo_nacionalidade_player_raw','bitfield_le',null,328,10,null,'little',null,'{"operacao":"floor(raw/2)","destino":"codigo_nacionalidade"}','clube_novo','nacionalidade_jogo','codigo_jogo','{"fk":"carta_jogo.codigo_nacionalidade -> nacionalidade_jogo.codigo_jogo"}','carta.nacionalidade','Player.bin bit 328/w10; 43.072/43.072 resolvidas'),
  ('dt870_updated','Player.bin','carta.tipo.codigo','carta_jogo.codigo_tipo_carta_fisico','id_mask',null,null,null,null,'little',null,'{"origem":"card_id","bit_inicio":44,"largura_bits":4}','clube_novo','tipo_carta_jogo','codigo_tipo_fisico','{"provisorio":"preservar quando sem ponte nominal"}','carta.tipo.codigo','card_id bits 44-47; estado físico provado'),
  ('dt870_updated','Player.bin','carta.tipo.subtipo','carta_jogo.marcador_subtipo_tipo_carta','bitfield_le',null,104,1,null,'little',null,'{}','clube_novo','tipo_carta_jogo','marcador_subtipo','{"provisorio":"preservar quando sem ponte nominal"}','carta.tipo.codigo','Player.bin registro bit 104 define subtipo 0/1'),
  ('dt870_updated','Player.bin','carta.impeto.slot1','carta_impeto_jogo.codigo_impeto','bitfield_le',null,308,10,null,'little',null,'{"slot":1,"zero":"sem","136":"vaga"}','clube_novo','impeto_jogo','codigo_jogo','{"estado":"0=sem;136=vaga;demais=impeto"}','impeto - na carta','Player.bin slot 1 bit308/w10, correspondência direta no catálogo'),
  ('dt870_updated','Player.bin','carta.impeto.slot2','carta_impeto_jogo.codigo_impeto','bitfield_le',null,288,10,null,'little',null,'{"slot":2,"zero":"sem","136":"vaga"}','clube_novo','impeto_jogo','codigo_jogo','{"estado":"0=sem;136=vaga;demais=impeto"}','impeto - na carta','Player.bin slot 2 bit288/w10, correspondência direta no catálogo'),
  ('dt870_updated','Player.bin','carta.playstyle.primario','carta_playstyle_jogo.codigo_jogo','bitfield_le',null,372,8,null,'little',null,'{}','clube_novo','playstyle','codigo_jogo','{}','estilo de jogo - na carta','Player.bin bit372/w8'),
  ('dt870_updated','Player.bin','carta.playstyle.secundario','carta_playstyle_jogo.codigo_jogo','bitfield_le',null,440,6,null,'little',null,'{"slot":2}','clube_novo','playstyle','codigo_jogo','{}','estilo de jogo - na carta','Player.bin bit440/w6'),
  ('dt870_updated','Coach.bin','tecnico.idade.raw','tecnico_jogo.idade','bitfield_le',null,231,7,null,'little',null,'{"operacao":"raw+14"}','clube_novo','tecnico_jogo','id','{}','tecnico.idade','Coach.bin bit231/w7; idade=raw+14'),
  ('dt870_updated','Coach.bin','tecnico.nacionalidade.codigo','tecnico_jogo.codigo_nacionalidade','bitfield_le',null,170,8,null,'little',null,'{}','clube_novo','nacionalidade_jogo','codigo_jogo','{"fk":"tecnico_jogo.codigo_nacionalidade -> nacionalidade_jogo.codigo_jogo"}','tecnico.nacionalidade','Coach.bin bit170/w8'),
  ('dt870_updated','Coach.bin','tecnico.afinidade.codigo','tecnico_jogo.codigo_afinidade','bitfield_le',null,187,3,null,'little',null,'{}','clube_novo','afinidade_tecnico_jogo','codigo_jogo','{}','tecnico.afinidade','Coach.bin bit187/w3'),
  ('dt870_updated','Coach.bin','tecnico.estilo.sobreposicao','tecnico_estilo_jogo.valor','bitfield_le',null,135,7,null,'little',null,'{}','clube_novo','estilo_jogo_tecnico','codigo','{"zero":"ausencia_legitima"}','tecnico.estilo.sobreposicao','Coach.bin bit135/w7 unsigned little-endian'),
  ('dt870_updated','Country.bin','nacionalidade.codigo','nacionalidade_jogo.codigo_jogo','bitfield_le',null,10,9,null,'little',null,'{}','clube_novo','nacionalidade_jogo','codigo_jogo','{}','nacionalidade.codigo','Country.bin bit10/w9; 214 códigos únicos'),
  ('dt870_updated','Country.bin','nacionalidade.nome_pt_br','nacionalidade_jogo.nome_pt_br','fixed_utf8_nul',788,null,null,70,'not_applicable','utf-8','{}','clube_novo','nacionalidade_jogo','codigo_jogo','{}','nacionalidade.nome_pt_br','Country.bin offset788/70 UTF-8 NUL'),
  ('dt870_updated','Country.bin','nacionalidade.sigla','nacionalidade_jogo.sigla','fixed_utf8_nul',708,null,null,10,'not_applicable','utf-8','{}','clube_novo','nacionalidade_jogo','codigo_jogo','{}','nacionalidade.sigla','Country.bin offset708/10 UTF-8 NUL'),
  ('dt261_bra','all.str','texto.all_str.catalogo','texto_do_jogo','all_str_parser',null,null,null,null,'not_applicable','utf-8','{"idioma":"pt-BR"}','clube_novo','texto_do_jogo','secao,id_texto','{"chaves":"unicas"}','tipo_carta.rotulo','Leitor canônico all.str com 11.679 chaves e hash físico comprovado'),
  ('dt261_bra','all.str','tecnico.afinidade.rotulo.codigo_5','afinidade_tecnico_jogo','all_str_parser',null,null,null,null,'not_applicable','utf-8','{"secao":"Any1W","id_texto":495}','clube_novo','texto_do_jogo','secao,id_texto','{"codigo":5}','afinidade_tecnico.rotulo.codigo_5','all.str Any1W:495, texto oficial comprovado')
) as v(papel_fonte,arquivo,chave_campo,entidade_destino,tipo_leitura,byte_offset,bit_inicio,largura_bits,largura_bytes,endianness,codificacao,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,assunto,prova)
join clube_novo.contrato_leitura_arquivo a
  on a.contrato_id = 'clubef-dt870-2026-r1' and a.papel_fonte = v.papel_fonte and a.arquivo = v.arquivo
on conflict (contrato_id,chave_campo) do nothing;

insert into clube_novo.contrato_leitura_requisito (contrato_id,chave_requisito,expressao,obrigatorio,proveniencia)
values
  ('clubef-dt870-2026-r1','contrato.fallback_numerico.proibido','{"regra":"nenhum leitor pode usar constante estrutural fora dos campos ativos do contrato"}',true,'diretriz de arquitetura 28/08/2026'),
  ('clubef-dt870-2026-r1','carga.fingerprint.exato','{"regra":"versao_jogo,fingerprint_contrato_sha256,fingerprint_fontes_sha256 devem coincidir antes da carga"}',true,'diretriz de arquitetura 28/08/2026'),
  ('clubef-dt870-2026-r1','consumidor.desligado','{"regra":"pode_rodar=0 durante a migração do contrato"}',true,'contrato final do Extrator')
on conflict (contrato_id,chave_requisito) do nothing;
