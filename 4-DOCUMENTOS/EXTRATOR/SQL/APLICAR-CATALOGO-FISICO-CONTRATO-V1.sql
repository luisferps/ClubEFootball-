-- Cobertura de catálogos e projeção canônica de Cartas, parte do pedido de clube_novo.
-- Metadados do contrato somente: não escreve dados extraídos nem habilita carga.
begin;

create table if not exists clube_novo.contrato_leitura_catalogo_fisico (
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  catalogo_schema text not null default 'clube_novo', catalogo_tabela text not null,
  modo_validacao text not null check (modo_validacao in ('fisico_direto','dependencia_normalizada')),
  artefato_fisico text, coluna_chave_fisica text, colunas_chave_canonica text[] not null,
  papel_fonte text, familia_dependencia text, check_dependencia text, proveniencia text not null,
  primary key (contrato_id, catalogo_schema, catalogo_tabela), check (catalogo_schema = 'clube_novo'),
  check (array_length(colunas_chave_canonica, 1) > 0),
  check ((modo_validacao = 'fisico_direto' and artefato_fisico is not null and coluna_chave_fisica is not null and papel_fonte is not null)
      or (modo_validacao = 'dependencia_normalizada' and familia_dependencia is not null and check_dependencia is not null))
);
create table if not exists clube_novo.contrato_leitura_projecao_cartas (
  contrato_id text not null references clube_novo.contrato_leitura_jogo(contrato_id) on delete restrict,
  chave_campo text not null, artefato_fisico text not null check (artefato_fisico in ('cartas_fisicas','dimensoes_fisicas')),
  coluna_fisica text not null, destino_schema text not null default 'clube_novo', destino_tabela text not null default 'carta_jogo',
  destino_coluna text not null, tipo_valor text not null, proveniencia text not null,
  primary key (contrato_id, chave_campo), check (destino_schema = 'clube_novo'), check (destino_tabela = 'carta_jogo')
);

-- Cada catálogo solicitado é coberto por fotografia física direta ou pelo validador normalizado pedido pelo banco.
insert into clube_novo.contrato_leitura_catalogo_fisico
 (contrato_id,catalogo_schema,catalogo_tabela,modo_validacao,artefato_fisico,coluna_chave_fisica,colunas_chave_canonica,papel_fonte,familia_dependencia,check_dependencia,proveniencia)
select c.contrato_id,'clube_novo',v.tabela,v.modo,v.artefato,v.coluna,v.chaves,v.papel,v.familia,v.check_nome,v.proveniencia
from clube_novo.contrato_leitura_jogo c cross join (values
 ('afinidade_tecnico_jogo','fisico_direto','afinidades_tecnico','codigo_jogo',array['codigo_jogo']::text[],'dt870_updated',null,null,'Coach.bin: código físico'),
 ('habilidade_jogo','fisico_direto','habilidades','id',array['skill_id']::text[],'dt870_updated',null,null,'PlayerSkill.bin: id físico'),
 ('nacionalidade_jogo','fisico_direto','nacionalidades','codigo_jogo',array['codigo_jogo']::text[],'dt870_updated',null,null,'Country.bin: código físico'),
 ('playstyle','fisico_direto','playstyles','id',array['id_jogo']::text[],'dt870_updated',null,null,'Playstyle.bin: id físico'),
 ('posicao_jogo','fisico_direto','posicoes','id',array['id']::text[],'dt870_updated',null,null,'catálogo físico de posições'),
 ('atributo_jogo','dependencia_normalizada',null,null,array['codigo']::text[],null,'relacoes','relacoes_normalizadas','relações normalizadas por código'),
 ('corpo_ordem','dependencia_normalizada',null,null,array['codigo']::text[],null,'relacoes','relacoes_normalizadas','relações normalizadas por código'),
 ('estilo_ia','dependencia_normalizada',null,null,array['bit']::text[],null,'relacoes','relacoes_normalizadas','relações normalizadas por bit'),
 ('clube_jogo','dependencia_normalizada',null,null,array['codigo_jogo']::text[],null,'dimensoes','dimensoes_normalizadas','vínculos de dimensões por FK'),
 ('liga_jogo','dependencia_normalizada',null,null,array['codigo_jogo']::text[],null,'dimensoes','dimensoes_normalizadas','vínculos de dimensões por FK'),
 ('tipo_carta_jogo','dependencia_normalizada',null,null,array['codigo_tipo_fisico','marcador_subtipo','tipo_carta_id']::text[],null,'dimensoes','dimensoes_normalizadas','tipo de carta por chave física'),
 ('atributo_ordem_otimizador','dependencia_normalizada',null,null,array['indice_otimizador']::text[],null,'tecnicos','tecnicos_normalizados','catálogo usado por técnicos'),
 ('estilo_jogo_tecnico','dependencia_normalizada',null,null,array['codigo']::text[],null,'tecnicos','tecnicos_normalizados','estilo normalizado de técnico'),
 ('tecnico_jogo','dependencia_normalizada',null,null,array['id']::text[],null,'tecnicos','tecnicos_normalizados','técnicos por identidade estável'),
 ('texto_do_jogo','dependencia_normalizada',null,null,array['id_texto','secao']::text[],null,'textos','textos_normalizados','texto por seção e id'),
 ('impeto_atributo_jogo','dependencia_normalizada',null,null,array['codigo_atributo','codigo_impeto']::text[],null,'impetos','catalogo_normalizado','catálogo de ímpetos normalizado'),
 ('impeto_classe_candidato_jogo','dependencia_normalizada',null,null,array['classe_candidato']::text[],null,'impetos','catalogo_normalizado','catálogo de ímpetos normalizado'),
 ('impeto_condicao_classe_jogo','dependencia_normalizada',null,null,array['classe_dono']::text[],null,'impetos','catalogo_normalizado','catálogo de ímpetos normalizado'),
 ('impeto_condicao_jogo','dependencia_normalizada',null,null,array['codigo_impeto']::text[],null,'impetos','catalogo_normalizado','catálogo de ímpetos normalizado'),
 ('impeto_condicao_liga_membro_jogo','dependencia_normalizada',null,null,array['codigo_liga_alvo_base','codigo_liga_membro']::text[],null,'impetos','catalogo_normalizado','catálogo de ímpetos normalizado'),
 ('impeto_condicao_parametro_faixa_jogo','dependencia_normalizada',null,null,array['corte_raw','efeito_maximo']::text[],null,'impetos','catalogo_normalizado','catálogo de ímpetos normalizado'),
 ('impeto_jogo','dependencia_normalizada',null,null,array['codigo_jogo']::text[],null,'impetos','catalogo_normalizado','catálogo de ímpetos normalizado'),
 ('tipo_impeto_jogo','dependencia_normalizada',null,null,array['codigo_raw']::text[],null,'impetos','catalogo_normalizado','catálogo de ímpetos normalizado')
) v(tabela,modo,artefato,coluna,chaves,papel,familia,check_nome,proveniencia)
where c.estado='ativo'
on conflict (contrato_id,catalogo_schema,catalogo_tabela) do update set modo_validacao=excluded.modo_validacao,artefato_fisico=excluded.artefato_fisico,coluna_chave_fisica=excluded.coluna_chave_fisica,colunas_chave_canonica=excluded.colunas_chave_canonica,papel_fonte=excluded.papel_fonte,familia_dependencia=excluded.familia_dependencia,check_dependencia=excluded.check_dependencia,proveniencia=excluded.proveniencia;

-- O comparador recebe esta projeção do banco; títulos/box e demais rótulos não participam da identidade.
insert into clube_novo.contrato_leitura_projecao_cartas
 (contrato_id,chave_campo,artefato_fisico,coluna_fisica,destino_schema,destino_tabela,destino_coluna,tipo_valor,proveniencia)
select c.contrato_id,v.chave,v.artefato,v.coluna,'clube_novo','carta_jogo',v.destino,v.tipo,v.proveniencia
from clube_novo.contrato_leitura_jogo c cross join (values
 ('carta.id','cartas_fisicas','card_id','card_id','text','Player.bin: card_id físico'),
 ('carta.clube.codigo','dimensoes_fisicas','codigo_clube','codigo_clube','integer','Player.bin + catálogo de clube'),
 ('carta.nacionalidade.raw','dimensoes_fisicas','codigo_nacionalidade_player_raw','codigo_nacionalidade_player_raw','integer','Player.bin: código bruto'),
 ('carta.tipo.codigo','dimensoes_fisicas','codigo_tipo_carta_fisico','codigo_tipo_carta_fisico','integer','Player.bin: tipo físico'),
 ('carta.tipo.subtipo','dimensoes_fisicas','marcador_subtipo_tipo_carta','marcador_subtipo_tipo_carta','integer','Player.bin: subtipo físico'),
 ('carta.tipo.indisponivel.id','dimensoes_fisicas','jogador_indisponivel','jogador_indisponivel','boolean','Player.bin: lista de indisponíveis'),
 ('carta.liga.team_id','dimensoes_fisicas','codigo_clube','codigo_clube','integer','Player.bin: clube vinculado à liga'),
 ('carta.liga.codigo','dimensoes_fisicas','codigo_liga','codigo_liga','integer','Player.bin: liga física'),
 ('carta.altura','cartas_fisicas','altura','altura','integer','Player.bin: altura normalizada'),
 ('carta.peso','cartas_fisicas','peso','peso','integer','Player.bin: peso normalizado'),
 ('carta.idade','cartas_fisicas','idade','idade','integer','Player.bin: idade normalizada'),
 ('carta.pe.ruim_uso','cartas_fisicas','pe_ruim_uso','pe_ruim_uso','integer','Player.bin: uso do pé ruim'),
 ('carta.pe.ruim_precisao','cartas_fisicas','pe_ruim_precisao','pe_ruim_precisao','integer','Player.bin: precisão do pé ruim'),
 ('carta.pe','cartas_fisicas','pe','pe','text','Player.bin: pé normalizado pelo normalizador do contrato'),
 ('carta.forma','cartas_fisicas','forma','forma','integer','Player.bin: forma'),
 ('carta.resistencia_lesao.media','cartas_fisicas','resistencia_lesao','resistencia_lesao','text','Player.bin: composição de resistência'),
 ('carta.resistencia_lesao.alta','cartas_fisicas','resistencia_lesao','resistencia_lesao','text','Player.bin: composição de resistência'),
 ('carta.nome.roman','cartas_fisicas','nome','nome','text','Player.bin: nome romanizado'),
 ('carta.corpo.card_id','cartas_fisicas','card_id','card_id','text','chave da relação de corpo')
) v(chave,artefato,coluna,destino,tipo,proveniencia)
where c.estado='ativo'
on conflict (contrato_id,chave_campo) do update set artefato_fisico=excluded.artefato_fisico,coluna_fisica=excluded.coluna_fisica,destino_coluna=excluded.destino_coluna,tipo_valor=excluded.tipo_valor,proveniencia=excluded.proveniencia;

update clube_novo.contrato_leitura_campo set entidade_destino='carta_jogo.jogador_indisponivel'
where chave_campo='carta.tipo.indisponivel.id' and entidade_destino='tipo_carta_jogo.tipo_carta_id';

create or replace function clube_novo.obter_pedido_leitura_tipado_ativo()
returns jsonb language plpgsql security invoker set search_path = clube_novo, pg_temp as $$
declare pedido jsonb; cid text;
begin
 pedido := clube_novo.obter_pedido_leitura_tipado_sem_revisao_v1(); cid := pedido->>'contrato_id';
 if cid is null or cid='' then raise exception 'pedido tipado sem contrato_id'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid) then raise exception 'pedido tipado sem cobertura de catálogo'; end if;
 if not exists(select 1 from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid) then raise exception 'pedido tipado sem projeção canônica de cartas'; end if;
 return pedido || jsonb_build_object(
  'catalogos_fisicos',(select coalesce(jsonb_agg(jsonb_build_object('schema',catalogo_schema,'table',catalogo_tabela,'modo_validacao',modo_validacao,'artefato_fisico',artefato_fisico,'coluna_chave_fisica',coluna_chave_fisica,'colunas_chave_canonica',colunas_chave_canonica,'papel_fonte',papel_fonte,'familia_dependencia',familia_dependencia,'check_dependencia',check_dependencia,'proveniencia',proveniencia) order by catalogo_tabela),'[]'::jsonb) from clube_novo.contrato_leitura_catalogo_fisico where contrato_id=cid),
  'projecoes_cartas',(select coalesce(jsonb_agg(jsonb_build_object('chave_campo',chave_campo,'artefato_fisico',artefato_fisico,'coluna_fisica',coluna_fisica,'destino_schema',destino_schema,'destino_tabela',destino_tabela,'destino_coluna',destino_coluna,'tipo_valor',tipo_valor,'proveniencia',proveniencia) order by chave_campo),'[]'::jsonb) from clube_novo.contrato_leitura_projecao_cartas where contrato_id=cid)
 );
end; $$;
commit;
