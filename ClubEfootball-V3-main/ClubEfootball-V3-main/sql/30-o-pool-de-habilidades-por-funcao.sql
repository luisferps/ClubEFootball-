-- ============================================================================
--  30 · O POOL DE HABILIDADES POR FUNÇÃO — 17/08/2026
-- ============================================================================
--  Ordem do Luis, 17/08:
--    "Seria muito mais fácil trabalhar com uma tabela de habilidades e outra
--     tabela do card. E aí depois também pode ter uma tabela de habilidades que
--     são possíveis, um pool — um pool geralzão, e um pool pra cada função."
--
--  E, antes, a distinção que faz esta tabela existir:
--    "Dentro do jogo pode-se colocar praticamente qualquer uma. Então são duas
--     coisas diferentes pro motor, porque tem habilidades que não mudam nada,
--     não ajudam em nada em determinadas funções."
--
--  ============================================================================
--  O QUE JÁ EXISTIA, E O QUE FALTAVA
--
--    insumo_habilidade ... as 65 do jogo (44 comuns + 21 especiais)      TINHA
--    cards_base .......... as que cada carta tem (nativas + especiais)   TINHA
--    insumo_bloqueio ..... quais NÃO entram em cada função (246 pares)   TINHA
--    o pool por função ... quais PODEM, e quais VALEM A PENA             FALTAVA
--
--  O bloqueio é o negativo. Esta view é o positivo — e ela responde as duas
--  perguntas que o Luis separou:
--
--    `permitida`  o JOGO deixa pôr essa habilidade nessa função?
--    `util`       ela MEXE em algum atributo que essa função pesa?
--
--  São coisas diferentes de propósito. O jogo deixa o zagueiro adicionar
--  "Chapéu"; o motor não perde tempo com ela, porque não mexe em nada que a
--  função de zagueiro pesa. É exatamente o que o motor.py já faz:
--
--      cand   = [h for h in falta if util(h)]        <- otimiza por PONTOS
--      outros = [h for h in falta if not util(h)]    <- preenche vaga que sobrou
--
--  ============================================================================
--  POR QUE VIEW, E NÃO TABELA
--
--    Porque ela é DERIVADA de três tabelas que mudam: as habilidades, os
--    bloqueios e o molde. Tabela materializada ficaria velha em silêncio no dia
--    em que o Luis mexesse num peso do molde — e ninguém veria.
--    View recalcula sozinha, sempre.
--
--  ⛔ SÓ ACRESCENTA. Nenhuma tabela é tocada. Rodar de novo só substitui a view.
-- ============================================================================

create or replace view pool_de_habilidades as
with
-- as 44 comuns: são as que o card pode ADICIONAR. As 21 especiais ficam de
-- fora porque não se adicionam — vêm de fábrica ou não vêm.
comuns as (
  select chave, nome_pt, efeito
  from insumo_habilidade
  where tipo = 'comum'
),
-- de cada habilidade, QUAIS atributos ela mexe.
-- o `efeito` é {"7": {"pct": 5}, "18": {"flat": 2}} — a chave é o atributo.
mexe_em as (
  select c.chave, c.nome_pt, (jsonb_each(c.efeito)).key::int as attr
  from comuns c
  where c.efeito is not null and c.efeito <> '{}'::jsonb
),
-- de cada função, quais atributos ela PESA (peso > 0)
pesa as (
  select funcao, attr
  from insumo_molde
  where coalesce(peso, 0) > 0
)
select
  f.nome                                   as funcao,
  c.chave                                  as habilidade_chave,
  c.nome_pt                                as habilidade,
  (b.habilidade is null)                   as permitida,
  exists (select 1 from mexe_em m
          join pesa p on p.funcao = f.nome and p.attr = m.attr
          where m.chave = c.chave)         as util,
  (select count(*) from mexe_em m where m.chave = c.chave) as atributos_que_mexe
from funcoes f
cross join comuns c
left join insumo_bloqueio b
       on b.funcao = f.nome and b.habilidade = c.nome_pt;

comment on view pool_de_habilidades is
  'Para cada funcao, quais habilidades comuns o JOGO permite (permitida) e quais MEXEM em atributo que a funcao pesa (util). Derivada de insumo_habilidade + insumo_bloqueio + insumo_molde — nunca fica velha.';

-- ============================================================================
--  CONFERÊNCIA
-- ============================================================================

-- 1) o tamanho do pool de cada função
select funcao,
       count(*)                                    as total_comuns,
       count(*) filter (where permitida)           as o_jogo_deixa,
       count(*) filter (where permitida and util)  as valem_a_pena,
       count(*) filter (where not permitida)       as bloqueadas
from pool_de_habilidades
group by funcao
order by valem_a_pena desc;

-- 2) as que o jogo deixa mas NAO servem — a diferença que o Luis descreveu
select funcao, habilidade
from pool_de_habilidades
where permitida and not util
order by funcao, habilidade
limit 40;
