-- ============================================================
-- REGRA DOS DOIS ESTILOS - 26/08/2026
-- migracao: regra_dois_estilos_casa_e_secundario
-- JA APLICADA no Supabase trqqpsnafpbudtvvicch (schema clube)
-- Guardado aqui como registro do que foi executado.
-- ============================================================

-- 1. parametro do estilo secundario
delete from clube.bonus_parametro where chave='estilo_ativo_secundario';
insert into clube.bonus_parametro (chave, valor, descricao, atualizado_em)
values ('estilo_ativo_secundario','0.5','quanto ganha o estilo do segundo slot quando ativa na posicao', now());

-- 2. conserto de etiqueta dos laterais (destrava 4.997 cartas)
update clube.bonus_posicao_regra set nome='Lateral defensivo', atualizado_em=now()
 where tipo='estilo' and nome='Zagueiro defensivo';
update clube.bonus_posicao_regra set nome='Lateral ofensivo', atualizado_em=now()
 where tipo='estilo' and nome='Zagueiro ofensivo';

-- 3. cadastro dos 8 estilos novos de 2027
delete from clube.bonus_posicao_regra where tipo='estilo' and nome in
 ('Interceptador de passe','Defensor participativo','Cobertura','Mestre da linha alta',
  'Pressão no ataque','Ladrão no ataque','Saída ofensiva','Goleiro-líbero');
insert into clube.bonus_posicao_regra (tipo,nome,posicoes,atualizado_em) values
 ('estilo','Interceptador de passe', '["MO","MLD","MLE","MC","VOL"]'::jsonb, now()),
 ('estilo','Defensor participativo', '["MO","MLD","MLE","MC","VOL"]'::jsonb, now()),
 ('estilo','Cobertura',              '["MC","VOL","LD","LE","ZC"]'::jsonb,   now()),
 ('estilo','Mestre da linha alta',   '["LD","LE","ZC"]'::jsonb,              now()),
 ('estilo','Pressão no ataque',      '["CA","SA","PD","PE"]'::jsonb,         now()),
 ('estilo','Ladrão no ataque',       '["CA","SA","PD","PE"]'::jsonb,         now()),
 ('estilo','Saída ofensiva',         '["CA","SA","PD","PE","MO"]'::jsonb,    now()),
 ('estilo','Goleiro-líbero',         '["GK"]'::jsonb,                        now());

-- 4. A CASA: estilo -> ficha (funcao), por posicao
--    Estilo SEM linha aqui NAO roteia - so paga o bonus secundario.
create table if not exists clube.estilo_funcao (
  estilo   text not null,
  posicao  text not null,
  funcao_codigo text not null references clube.funcao(codigo),
  primary key (estilo, posicao, funcao_codigo)
);
comment on table clube.estilo_funcao is
 'A casa de cada estilo: em que ficha ele e o dono. Estilo sem linha aqui NAO roteia - so paga o bonus secundario. Regra de 26/08.';

insert into clube.estilo_funcao (estilo,posicao,funcao_codigo) values
 ('O destruidor','ZC','zagueiro_de_combate'),
 ('Defensor criativo','ZC','zagueiro_de_saida'),
 ('Atacante surpresa','ZC','zagueiro_de_saida'),
 ('Lateral defensivo','LD','lateral_defensivo'),
 ('Lateral defensivo','LE','lateral_defensivo'),
 ('Lateral ofensivo','LD','lateral_ofensivo'),
 ('Lateral ofensivo','LE','lateral_ofensivo'),
 ('Lateral atacante','LD','lateral_ofensivo'),
 ('Lateral atacante','LE','lateral_ofensivo'),
 ('O destruidor','LD','lateral_defensivo'),   -- casa nova, aprovada 26/08
 ('O destruidor','LE','lateral_defensivo'),   -- casa nova, aprovada 26/08
 ('Goleiro defensivo','GO','goleiro_defensivo'),
 ('Goleiro ofensivo','GO','goleiro_ofensivo'),
 ('Primeiro volante','VOL','volante_de_contencao'),
 ('O destruidor','VOL','volante_de_contencao'),
 ('Orquestrador','VOL','volante_de_construcao'),
 ('Meia versátil','VOL','volante_de_construcao'),
 ('Orquestrador','MLG','meia_central_armador'),
 ('Armador criativo','MLG','meia_central_armador'),
 ('O destruidor','MLG','meia_central_armador'),
 ('Clássico nº 10','MLG','meia_central_armador'),
 ('Meia versátil','MLG','meia_central_de_chegada'),
 ('Jogador de infiltração','MLG','meia_central_de_chegada'),
 ('Perito em cruzamento','MLD','meia_de_lado_por_fora'),
 ('Perito em cruzamento','MLE','meia_de_lado_por_fora'),
 ('Meia versátil','MLD','meia_de_lado_por_fora'),
 ('Meia versátil','MLE','meia_de_lado_por_fora'),
 ('Lateral móvel','MLD','meia_de_lado_por_fora'),
 ('Lateral móvel','MLE','meia_de_lado_por_fora'),
 ('Jogador de infiltração','MLD','meia_de_lado_por_dentro'),
 ('Jogador de infiltração','MLE','meia_de_lado_por_dentro'),
 ('Armador criativo','MLD','meia_de_lado_por_dentro'),
 ('Armador criativo','MLE','meia_de_lado_por_dentro'),
 ('Armador criativo','MAT','meia_ofensivo_armador'),
 ('Clássico nº 10','MAT','meia_ofensivo_armador'),
 ('Jogador de infiltração','MAT','segundo_atacante'),
 ('Puxa marcação','MAT','segundo_atacante'),
 ('Armador criativo','PTD','ponta_criadora'),
 ('Armador criativo','PTE','ponta_criadora'),
 ('Lateral móvel','PTD','ponta_criadora'),
 ('Lateral móvel','PTE','ponta_criadora'),
 ('Perito em cruzamento','PTD','ponta_criadora'),
 ('Perito em cruzamento','PTE','ponta_criadora'),
 ('Ala produtivo','PTD','ponta_finalizadora'),
 ('Ala produtivo','PTE','ponta_finalizadora'),
 ('Artilheiro','PTD','ponta_finalizadora'),
 ('Artilheiro','PTE','ponta_finalizadora'),
 ('Homem de área','CA','centroavante_fixo'),
 ('Pivô','CA','centroavante_fixo'),
 ('Artilheiro','CA','centroavante_movel'),
 ('Puxa marcação','CA','centroavante_movel'),
 ('Atacante pivô','CA','falso_nove'),
 ('Atacante pivô','SA','falso_nove'),
 ('Jogador de infiltração','SA','segundo_atacante'),
 ('Puxa marcação','SA','segundo_atacante'),
 ('Armador criativo','SA','meia_ofensivo_armador'),
 ('Clássico nº 10','SA','meia_ofensivo_armador')
on conflict do nothing;

-- 5. o slot que manda em cada posicao (ficha recomendada + molde)
create table if not exists clube.posicao_slot (
  posicao text primary key,
  slot    text not null check (slot in ('ofensivo','defensivo'))
);
comment on table clube.posicao_slot is
 'Qual slot manda em cada posicao: define a ficha recomendada e o molde. Regra de 26/08.';
insert into clube.posicao_slot (posicao,slot) values
 ('ZC','defensivo'),('LD','defensivo'),('LE','defensivo'),('GO','defensivo'),('VOL','defensivo'),
 ('MLG','ofensivo'),('MLD','ofensivo'),('MLE','ofensivo'),('MAT','ofensivo'),
 ('CA','ofensivo'),('SA','ofensivo'),('PTD','ofensivo'),('PTE','ofensivo')
on conflict (posicao) do update set slot=excluded.slot;


-- ============================================================
-- CONFERENCIA (rodar depois)
-- ============================================================
-- select
--  (select count(*) from clube.estilo_funcao) casas,               -- esperado 57
--  (select count(*) from clube.posicao_slot) posicoes,             -- esperado 13
--  (select valor from clube.bonus_parametro
--     where chave='estilo_ativo_secundario') secundario,           -- esperado 0.5
--  (select count(*) from clube.bonus_posicao_regra
--     where tipo='estilo' and nome in
--       ('Zagueiro defensivo','Zagueiro ofensivo')) sobrou_velho;  -- esperado 0

-- select * from clube.auditoria_completa();
