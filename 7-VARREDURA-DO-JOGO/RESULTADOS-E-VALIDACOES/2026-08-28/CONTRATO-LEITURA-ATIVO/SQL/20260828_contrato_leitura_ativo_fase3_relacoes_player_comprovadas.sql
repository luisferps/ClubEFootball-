-- Fase 3A: famílias normalizadas cujo endereço já está tipado no modelo novo.
-- Lê somente o catálogo clube_novo e promove campos para o rascunho; não executa carga.

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,bit_inicio,largura_bits,endianness,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', f.arquivo_id,
       'carta.atributo.bit.' || a.bit,
       'carta_atributo_jogo.valor','bitfield_le',a.bit,a.largura,'little',
       jsonb_build_object('codigo_atributo',a.codigo,'base',40),
       'clube_novo','atributo_jogo','codigo',jsonb_build_object('fk','carta_atributo_jogo.codigo_atributo -> atributo_jogo.codigo'),
       'atributo_jogo.bit.' || a.bit,
       coalesce(a.endereco, 'Player.bin bit ' || a.bit || '/w' || a.largura),
       'comprovado'
from clube_novo.atributo_jogo a
join clube_novo.contrato_leitura_arquivo f on f.contrato_id='clubef-dt870-2026-r1' and f.papel_fonte='dt870_updated' and f.arquivo='Player.bin'
where a.bit is not null and a.largura is not null
on conflict (contrato_id,chave_campo) do nothing;

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,bit_inicio,largura_bits,endianness,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', f.arquivo_id,
       'carta.habilidade.' || h.skill_id,
       'carta_habilidade_jogo.skill_id','bitfield_le',h.bit_na_carta,1,'little',
       jsonb_build_object('skill_id',h.skill_id),
       'clube_novo','habilidade_jogo','skill_id',jsonb_build_object('presente_quando',true),
       'habilidade - na carta',
       'Player.bin bit ' || h.bit_na_carta || '; skill_id ' || h.skill_id || ' no catálogo normalizado',
       'comprovado'
from clube_novo.habilidade_jogo h
join clube_novo.contrato_leitura_arquivo f on f.contrato_id='clubef-dt870-2026-r1' and f.papel_fonte='dt870_updated' and f.arquivo='Player.bin'
where h.bit_na_carta is not null and h.pode_rodar is true
on conflict (contrato_id,chave_campo) do nothing;

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,bit_inicio,largura_bits,endianness,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', f.arquivo_id,
       'carta.estilo_ia.' || e.bit,
       'carta_estilo_ia_jogo.bit_estilo_ia','bitfield_le',e.bit,1,'little',
       jsonb_build_object('bit_estilo_ia',e.bit),
       'clube_novo','estilo_ia','bit',jsonb_build_object('presente_quando',true),
       'estilo de IA',
       coalesce(e.endereco, 'Player.bin bit ' || e.bit),
       'comprovado'
from clube_novo.estilo_ia e
join clube_novo.contrato_leitura_arquivo f on f.contrato_id='clubef-dt870-2026-r1' and f.papel_fonte='dt870_updated' and f.arquivo='Player.bin'
where e.bit is not null
on conflict (contrato_id,chave_campo) do nothing;

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,bit_inicio,largura_bits,endianness,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', f.arquivo_id,
       'carta.posicao.aptidao.' || lower(p.codigo_en),
       'carta_posicao_jogo.nivel_aptidao','bitfield_le',p.bit_aptidao,2,'little',
       jsonb_build_object('posicao_id',p.id,'codigo_en',p.codigo_en),
       'clube_novo','posicao_jogo','id',jsonb_build_object('fk','carta_posicao_jogo.posicao_id -> posicao_jogo.id'),
       'aptidao de posicao',
       'Player.bin bit ' || p.bit_aptidao || '/w2; posição ' || p.codigo_en,
       'comprovado'
from clube_novo.posicao_jogo p
join clube_novo.contrato_leitura_arquivo f on f.contrato_id='clubef-dt870-2026-r1' and f.papel_fonte='dt870_updated' and f.arquivo='Player.bin'
where p.bit_aptidao is not null
on conflict (contrato_id,chave_campo) do nothing;

insert into clube_novo.contrato_leitura_campo
  (contrato_id,arquivo_id,chave_campo,entidade_destino,tipo_leitura,bit_inicio,largura_bits,endianness,transformacao,catalogo_schema,catalogo_tabela,catalogo_chave,requisito,proveniencia_mapa_assunto,prova,status_prova)
select 'clubef-dt870-2026-r1', f.arquivo_id,
       'carta.posicao.principal','carta_posicao_principal_jogo.posicao_id','bitfield_le',556,4,'little',
       '{"campo":"posicao principal"}'::jsonb,
       'clube_novo','posicao_jogo','id','{"enum":"0..12"}'::jsonb,
       'posicao_jogo.endereco','Player.bin bit556/w4; enum 0..12 normalizado em posicao_jogo','comprovado'
from clube_novo.contrato_leitura_arquivo f
where f.contrato_id='clubef-dt870-2026-r1' and f.papel_fonte='dt870_updated' and f.arquivo='Player.bin'
on conflict (contrato_id,chave_campo) do nothing;
