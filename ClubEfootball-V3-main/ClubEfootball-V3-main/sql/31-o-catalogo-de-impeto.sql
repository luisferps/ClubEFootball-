-- ============================================================================
--  31 · O CATÁLOGO DE ÍMPETO — 18/08/2026
-- ============================================================================
--  Ordem do Luis, 18/08:
--    "O nome do ímpeto não é 'Chute +1'. O nome do ímpeto é CHUTE. O mais um
--     significa que ele aumenta mais um ponto em alguns atributos, que dá pra
--     saber previamente."
--
--    "É só você colocar o nome de um dos idiomas, pode ser o inglês, como chave
--     única, e colocar uma coluna para os outros nomes."
--
--    "Vai ter mais um, vai ter mais dois, daqui a pouco vai ter mais dez nomes
--     pra uma coisa só."
--
--  ============================================================================
--  O QUE ESTAVA ERRADO
--
--    O nível estava COLADO no nome. "Chute +1" e "Chute +3" eram dois ímpetos
--    diferentes no sistema. São o mesmo. Resultado medido em 18/08:
--
--      110 nomes guardados   ->   38 ímpetos de verdade
--      27 deles tinham nome em portugues E em ingles
--
--    E a prova de que é o mesmo ímpeto não é tradução: é MEDIDA. Conferi 39
--    ímpetos em níveis diferentes — NENHUM muda de atributo. "Chute" pega
--    Finalização, Força do chute, Curva e Passe alto em +1 e em +5. O número
--    só diz quanto ele soma EM CADA UM (Chute +3 = 12 pontos, não 3 repartidos).
--
--  ============================================================================
--  ⛔ A REGRA QUE MANDA NO CAMPO `adicionavel` — Luis, 18/08
--
--    "O nível +1 é para ímpetos ADICIONADOS. Você não consegue adicionar um
--     ímpeto com nível maior do que um. Os outros níveis — +2, +3, +4, +5 —
--     são para ímpetos que já vêm DE FÁBRICA."
--
--    Medido nas 12.368 linhas: em 1.124 a carta tem vaga livre e o motor
--    escolheu o ímpeto. Em 100% delas escolheu +1. O motor está CERTO.
--
--    ⛔ NÃO "consertar" isso. Vaga vazia só recebe +1. Ponto.
--
--  ============================================================================
--  ⚠️ O QUE AINDA FALTA — os degraus do condicional
--
--    Luis: "Se for condicional ele vai mostrar mais um."
--    Medido: 116 dos 119 condicionais aparecem como +1.
--    Luis: "Geralmente o condicional é mais três."
--
--    As colunas `condicional` e `degraus` existem para isso. `degraus` nasce
--    vazio e é preenchido carta a carta — é conferência de olho no jogo.
--
--  ⛔ SÓ ACRESCENTA. Nenhuma tabela existente é tocada.
-- ============================================================================

create table if not exists insumo_impeto (
  chave         text        primary key,   -- o ingles, sem espaco: 'shooting'
  nome_en       text,
  nome_pt       text,
  outros_nomes  jsonb       not null default '[]'::jsonb,
  atributos     jsonb       not null,      -- [1,6,12,14] — FIXOS, nao mudam com o nivel
  niveis_vistos jsonb       not null default '[]'::jsonb,
  adicionavel   boolean     not null default false,  -- entra em vaga vazia (sempre nivel 1)
  condicional   boolean     not null default false,
  degraus       jsonb,                     -- [1,2,3] quando condicional. NULL = ninguem conferiu
  condicao      text,                      -- o que faz subir o degrau
  cartas        integer     not null default 0,
  atualizado_em timestamptz not null default now()
);

comment on table insumo_impeto is
  'Um impeto por linha. A chave e o nome em ingles; os outros idiomas ficam em nome_pt e outros_nomes. Os atributos sao FIXOS e nao mudam com o nivel — o nivel so diz quanto soma em cada um. adicionavel=true significa que ele entra numa vaga vazia, e nesse caso SEMPRE no nivel 1 (ordem do Luis, 18/08). degraus NULL quer dizer que ninguem conferiu ainda.';

comment on column insumo_impeto.atributos is
  'Os numeros dos atributos que este impeto mexe. Medido, nao traduzido: dois nomes que mexem nos mesmos atributos SAO o mesmo impeto.';

comment on column insumo_impeto.adicionavel is
  'true = pode ser posto numa vaga vazia, e so no nivel 1. Os niveis 2 a 5 so vem de fabrica.';

comment on column insumo_impeto.degraus is
  'Para os condicionais: quais niveis ele percorre, ex [1,2,3]. NULL = nao conferido.';

create index if not exists insumo_impeto_condicional on insumo_impeto (condicional);

-- ------------------------------------------- A LEITURA PÚBLICA
--  Mesma regra das outras: a chave do navegador LÊ, e não escreve.
alter table insumo_impeto enable row level security;

do $$
begin
  if not exists (select 1 from pg_policies
                 where schemaname = 'public' and tablename = 'insumo_impeto'
                   and policyname = 'insumo_impeto_leitura_publica') then
    create policy insumo_impeto_leitura_publica on public.insumo_impeto
      for select to anon, authenticated using (true);
    raise notice 'criei a politica de leitura em insumo_impeto';
  else
    raise notice 'a politica ja existia';
  end if;
end $$;

revoke insert, update, delete on public.insumo_impeto from anon;

-- ============================================================================
--  CONFERÊNCIA — rode depois do MONTAR-O-CATALOGO-DE-IMPETO.bat
-- ============================================================================

-- 1) o catalogo inteiro, do mais usado para o menos
select chave, nome_pt, atributos, niveis_vistos, adicionavel, condicional, cartas
from insumo_impeto
order by cartas desc;

-- 2) quantos sao adicionaveis (entram em vaga vazia) e quantos so vem de fabrica
select adicionavel, count(*) as impetos, sum(cartas) as cartas
from insumo_impeto
group by adicionavel;

-- 3) OS QUE FALTAM CONFERIR — os condicionais sem degrau
select chave, nome_pt, atributos, cartas
from insumo_impeto
where condicional and degraus is null
order by cartas desc;

-- 4) o mesmo impeto com mais de um nome — a duplicacao que isto resolve
select chave, nome_en, nome_pt, outros_nomes
from insumo_impeto
where nome_pt is not null and nome_en is not null and nome_pt <> nome_en
order by cartas desc;
