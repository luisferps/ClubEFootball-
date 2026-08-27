-- ===========================================================================
--  23 — A COLUNA `faltou` DA TABELA bonus
--  Cole INTEIRO no SQL Editor do Supabase e clique RUN.
--  Roda quantas vezes quiser: e tudo "if not exists".
-- ===========================================================================
--
--  ORDEM DO LUIS, 15/08:
--    "quando nao souber o numero, tem que avisar que nao foi possivel puxar,
--     senao a gente nao vai saber nunca, vai ficar la eternamente desse jeito.
--     Nao tem que inventar numero velho, tem que falar nao sei, coloca la
--     nao sei."
--
--  O motor_bonus obedece essa ordem: quando um insumo nao existe, ele NAO
--  poe zero — poe NAO SEI, e escreve o nome do que faltou numa lista.
--  Zero e um numero inventado, e numero inventado some. "Nao sei" cobra.
--
--  O problema ate 19/08: a tabela `bonus` nao tinha onde guardar essa lista.
--  O motor mandava as 17.463 linhas, o banco recusava por causa da coluna
--  que nao existia, e o motor reenviava SEM ela. As linhas subiam, mas a
--  informacao de o que faltou ficava so no arquivo NAO-SEI.txt da maquina.
--  Quem olhasse o banco via bonus com nota e nao tinha como saber que parte
--  daquela nota estava faltando insumo.
--
--  Depois de rodar isto, o `faltou` sobe junto e o banco passa a contar a
--  mesma historia que a maquina.
-- ===========================================================================

alter table public.bonus
  add column if not exists faltou text[];

comment on column public.bonus.faltou is
  'Os insumos que NAO existiam na hora de calcular este bonus — ex.: {"corpo","estilo da IA"}. Lista vazia = calculei com tudo. NAO confundir com bonus zero: zero e uma medida ("conferi e nao ganha nada"), faltou e a ausencia da medida ("nunca perguntei"). Ordem do Luis, 15/08: nao inventar zero no lugar de nao sei.';

create index if not exists bonus_faltou_idx
  on public.bonus using gin (faltou);

-- ---------------------------------------------------------------------------
--  CONFERENCIA — o que voce deve ver depois de rodar
-- ---------------------------------------------------------------------------
--  Antes de rodar o motor de bonus de novo, `com_faltou` vem 0: a coluna
--  acabou de nascer e esta vazia. Rode o ATUALIZAR-O-ENCAIXE-AGORA.bat e
--  volte aqui — ai os numeros batem com o NAO-SEI.txt da maquina.

select
  count(*)                                              as linhas,
  count(faltou)                                         as com_coluna_preenchida,
  count(*) filter (where faltou is not null
                     and cardinality(faltou) > 0)       as pares_com_algum_nao_sei,
  count(*) filter (where faltou is not null
                     and cardinality(faltou) = 0)       as pares_completos
from public.bonus;

-- quantos pares faltou CADA insumo (tem que bater com o resumo do motor)
select insumo, count(*) as pares
from public.bonus, unnest(faltou) as insumo
group by insumo
order by pares desc;
