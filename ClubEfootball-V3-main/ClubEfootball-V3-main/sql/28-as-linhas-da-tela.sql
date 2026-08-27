-- ============================================================================
--  28 · AS LINHAS DA TELA VÃO PARA O BANCO — 17/08/2026
-- ============================================================================
--  Ordem do Luis, 17/08:
--    "A única diferença é essa. Esse jogar os dados e levar eles junto com o
--     arquivo do encaixe — a gente vai pegar esses mesmos dados do banco de
--     dados, online. Só isso. O restante dele não toca, é pra ficar do jeito
--     que está: o design, os trem tudo."
--
--  O QUE SÃO "AS LINHAS DA TELA"
--    É a lista pronta que o encaixe mostra: uma linha para cada carta em cada
--    função, com os 53 campos que aparecem na tela — nome, ovr, tier, a nota,
--    o técnico, o ímpeto, as habilidades, as barrinhas, os atributos finais.
--    São 12.370 linhas. Hoje elas são coladas dentro do arquivo, e são elas
--    que fazem o encaixe ter 39,1 MB.
--
--  POR QUE A LINHA INTEIRA VAI COMO UM BLOCO, E NÃO EM 53 COLUNAS
--    Porque quem monta essas linhas é o gera_encaixe.py, e ele muda. Se cada
--    campo virasse coluna, no dia em que ele acrescentasse um campo o banco
--    recusaria a linha inteira — ou pior, aceitaria e perderia o campo novo
--    em silêncio. Como bloco, o banco acompanha sozinho.
--
--    O card_id e a funcao ficam DE FORA do bloco também, como colunas, porque
--    são a chave: é por elas que se atualiza sem duplicar.
--
--  ⛔ SÓ ACRESCENTA. Nenhuma tabela existente é tocada.
--  ⛔ Rode este arquivo UMA vez no SQL Editor. Pode rodar de novo sem estragar.
-- ============================================================================

create table if not exists tela_encaixe (
  card_id    text        not null,
  funcao     text        not null,
  linha      jsonb       not null,
  gerado_em  timestamptz not null default now(),
  primary key (card_id, funcao)
);

comment on table tela_encaixe is
  'As linhas prontas do encaixe: uma por carta x funcao, com os 53 campos que a tela mostra. Quem escreve e o gera_encaixe.py; quem le e o proprio encaixe, pelo navegador.';

-- O índice é para a tela poder pedir só uma função sem varrer as 12.370.
create index if not exists tela_encaixe_funcao on tela_encaixe (funcao);

-- ------------------------------------------- A LEITURA PÚBLICA
--  Mesma regra das outras 14: a chave do navegador LÊ, e não escreve.
alter table tela_encaixe enable row level security;

do $$
begin
  if not exists (select 1 from pg_policies
                 where schemaname = 'public' and tablename = 'tela_encaixe'
                   and policyname = 'tela_encaixe_leitura_publica') then
    create policy tela_encaixe_leitura_publica on public.tela_encaixe
      for select to anon, authenticated using (true);
    raise notice 'criei a politica de leitura em tela_encaixe';
  else
    raise notice 'a politica ja existia';
  end if;
end $$;

-- ⛔ Cinto e suspensório: sem o GRANT, a chave pública não escreve nem que
--    alguém crie uma política larga por engano depois.
revoke insert, update, delete on public.tela_encaixe from anon;

-- ============================================================================
--  CONFERÊNCIA — rode depois
-- ============================================================================
select 'tela_encaixe' as tabela, count(*) as linhas from tela_encaixe;

select tablename, policyname, cmd, roles
from pg_policies where tablename = 'tela_encaixe';
