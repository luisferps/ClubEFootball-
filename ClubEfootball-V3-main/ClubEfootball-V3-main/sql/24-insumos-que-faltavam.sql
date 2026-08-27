-- ============================================================================
--  24 · OS QUATRO INSUMOS QUE NAO TINHAM TABELA — 17/08/2026
-- ============================================================================
--  Ordem do Luis, 17/08: "junta isso e sobe pro Supabase."
--
--  Levantados por engenharia reversa de UMA carta (Morgan Rogers 86, Meia
--  ofensivo armador), anotando cada tipo de dado no ponto em que ele foi
--  preciso. Estes quatro eram os unicos sem tabela nenhuma no banco.
--
--  ⛔ SO ACRESCENTA. Nenhuma tabela existente e tocada.
--  ⛔ Rode este arquivo UMA vez no SQL Editor do Supabase. Pode rodar de novo
--     sem estragar nada (tudo e IF NOT EXISTS).
-- ============================================================================

-- ---------------------------------------------------------------- 1. A REGUA
--  A LEI DO VALOR: quanto vale estar acima do alvo, quanto custa estar abaixo.
--  Nao e regra do jogo — e valoracao declarada do Luis.
--  Fonte: regua.py  (DEG, TETO_PUN, VMAX)
create table if not exists insumo_regua (
  chave        text primary key,
  valor        jsonb       not null,
  o_que_e      text,
  vem_de       text,
  atualizado_em timestamptz default now()
);
comment on table insumo_regua is
  'A regua da nota: os nove degraus acima do alvo, o teto da punicao e a formula da punicao. Valoracao do Luis, nao regra do jogo.';

-- ------------------------------------------- 2. O CATALOGO DE IMPETOS
--  Quais impetos existem para fabricar, e o que cada um soma em cada atributo.
--  Fonte: CAT_dom.json  (58 impetos)
create table if not exists insumo_impeto_catalogo (
  nome         text primary key,
  condicional  boolean     not null default false,
  efeito       jsonb       not null,
  o_que_e      text,
  atualizado_em timestamptz default now()
);
comment on table insumo_impeto_catalogo is
  'O catalogo de impetos fabricaveis. efeito = lista de [indice do atributo, quanto sobe]. O motor escolhe daqui.';

-- ------------------------------------- 3. A TABELA DO MULTIPLICADOR TATICO
--  O multiplicador que o tecnico aplica, medido no videogame ponto por ponto.
--  Fonte: tabm_medido.json  (100 pontos)
create table if not exists insumo_multiplicador (
  ponto        integer primary key,
  multiplicador numeric(10,6) not null,
  o_que_e      text,
  atualizado_em timestamptz default now()
);
comment on table insumo_multiplicador is
  'A tabela do multiplicador tatico, medida no videogame. ponto -> multiplicador.';

-- ------------------------------------------------ 4. AS BARRAS DE PROGRESSAO
--  Cada nivel gasto numa barra soma +1 em TODOS os atributos dela.
--  ⚠️ Salto (13) mora em DUAS barras. Isso nao e erro.
--  Fonte: equacao.py  (MB e ACCU)
create table if not exists insumo_barra (
  barra        text        not null,
  attr         integer     not null,
  ordem        integer,
  o_que_e      text,
  atualizado_em timestamptz default now(),
  primary key (barra, attr)
);
comment on table insumo_barra is
  'As 10 barras de progressao: quais atributos cada barra sobe. Salto mora em duas de proposito.';

create table if not exists insumo_custo_nivel (
  nivel        integer primary key,
  custo        integer     not null,
  acumulado    integer     not null,
  o_que_e      text,
  atualizado_em timestamptz default now()
);
comment on table insumo_custo_nivel is
  'O custo de cada nivel e o acumulado. custo do nivel n = ceil(n/4), teto 25. O orcamento e 2 x (nivel maximo - 1).';

-- ============================================================================
--  CONFERENCIA — rode depois e veja se as cinco nasceram
-- ============================================================================
select 'insumo_regua'            as tabela, count(*) from insumo_regua
union all select 'insumo_impeto_catalogo', count(*) from insumo_impeto_catalogo
union all select 'insumo_multiplicador',   count(*) from insumo_multiplicador
union all select 'insumo_barra',           count(*) from insumo_barra
union all select 'insumo_custo_nivel',     count(*) from insumo_custo_nivel;
