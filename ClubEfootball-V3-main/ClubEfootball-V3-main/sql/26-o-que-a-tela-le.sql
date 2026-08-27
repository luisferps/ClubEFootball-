-- ============================================================================
--  26 · O QUE A TELA LE E O BANCO NAO TINHA — 17/08/2026
-- ============================================================================
--  Ordem do Luis, 17/08:
--    "O encaixe e so uma interface. Ele e o que vai fazer as consultas do banco
--     e colocar na tela. Ele nao tem que ficar carregando um outro banco de
--     dados duplicado dentro dele."
--
--  Medido: o gera_encaixe.py le 16 arquivos que nao vem do banco. Destes,
--  QUATRO nao existem em tabela nenhuma. Sao estes. Os outros doze ja tem o
--  dado dentro da cards_base — o problema la e so ninguem ter ligado.
--
--  ⛔ SO ACRESCENTA. Nenhuma tabela existente e tocada.
--  ⛔ Pode rodar de novo sem estragar nada (tudo e IF NOT EXISTS).
-- ============================================================================

-- ------------------------------------------- 1. A REGRA DA POSICAO x FUNCAO
--  De `regra.json`. Duas coisas dentro:
--    REGRA       posicao -> quais funcoes ela pode ocupar  (12 posicoes)
--    SA_FAMILIA  estilo de jogo -> para que familia o segundo atacante vai (22)
--  Guardado como jsonb inteiro, igual ao insumo_regua: sao duas tabelas de
--  decisao pequenas, e quebrar em linha nao ajuda ninguem a ler.
create table if not exists insumo_regra_funcao (
  chave         text primary key,
  valor         jsonb       not null,
  o_que_e       text,
  vem_de        text,
  atualizado_em timestamptz default now()
);
comment on table insumo_regra_funcao is
  'A regra de posicao x funcao e a familia do segundo atacante. Fonte: regra.json.';

-- ------------------------------------------------------------- 2. O MEU TIME
--  De `meu_time.json`. As cartas que o Luis tem. A tela marca elas.
--  ⚠️ O arquivo tem 114 ids e 99 nomes: ha id sem nome. O id manda; o nome e
--     rotulo, e pode ficar nulo.
create table if not exists meu_time (
  card_id       text primary key,
  nome          text,
  fonte         text,
  atualizado_em timestamptz default now()
);
comment on table meu_time is
  'As cartas que o Luis tem. O id manda; o nome e rotulo e pode ser nulo.';

-- -------------------------------------------------------------- 3. AS CAMPANHAS
--  De `campanhas_efhub.json` e `efscout_campanhas.json`: que cartas cada box
--  trouxe. A `fonte` fica na chave porque as duas listam a MESMA box com
--  conteudo que pode divergir — e divergencia se mede, nao se apaga.
create table if not exists campanha (
  fonte         text        not null,
  nome          text        not null,
  ids           jsonb       not null,
  ordem         integer,
  quando        date,
  atualizado_em timestamptz default now(),
  primary key (fonte, nome)
);
comment on table campanha is
  'As box e as cartas de cada uma. Chave = fonte + nome: o efHub e o efscout podem discordar, e os dois ficam.';

-- --------------------------------------------------------- 4. O TIPO DA CARTA
--  De `efscout_campanhas.json`, no `player_type`. Diz que tipo de carta e
--  (Standard, POTW, Epic...). A tela usa para a etiqueta.
create table if not exists insumo_player_type (
  card_id       text primary key,
  tipo          integer,
  atualizado_em timestamptz default now()
);
comment on table insumo_player_type is
  'O tipo da carta pelo efscout. A tela usa na etiqueta.';

-- ============================================================================
--  CONFERENCIA — rode depois e veja se as quatro nasceram
-- ============================================================================
select 'insumo_regra_funcao'  as tabela, count(*) from insumo_regra_funcao
union all select 'meu_time',             count(*) from meu_time
union all select 'campanha',             count(*) from campanha
union all select 'insumo_player_type',   count(*) from insumo_player_type;
