-- ===========================================================================
--  32 — A ETIQUETA DO CARD (e o fim da box falsa)
--  Cole INTEIRO no SQL Editor do Supabase e clique RUN.
--  Roda quantas vezes quiser: e tudo "if not exists".
-- ===========================================================================
--
--  ORDEM DO LUIS, 18/08:
--    "Big Time e o TIPO da carta. E um card lancado especial pra comemorar uma
--     partida que o jogador jogou bem demais — por isso ela vem com a data da
--     partida. Box ou campanha e aonde voce roda as moedas pra obter as cartas."
--
--  O que estava errado: o campo `box` guardava a ETIQUETA DA CARTA. Provado em
--  18/08 com dois ids que o efHub publica DENTRO da box `Living Legends 2026`
--  (17 cartas):
--     89138556575063  Lionel Messi       estava em "Big Time Argentina 15 Jul '26"
--     89138556572074  Cristiano Ronaldo  estava em "Big Time Portugal 23 Jun '26"
--
--  A etiqueta e dado bom — so nao e box. Agora ela tem coluna propria.
-- ===========================================================================

alter table public.cards_base
  add column if not exists etiqueta_do_card text;

comment on column public.cards_base.etiqueta_do_card is
  'O TIPO do card e, quando existe, a partida que ele comemora — ex.: "Big Time Portugal 23 Jun ''26", "Uruguay 2010". Vem do variation_details.name do efootballdb. NAO e box: box e onde se roda a moeda, e quem lista box e o efHub.';

comment on column public.cards_base.box is
  'Nome da BOX/campanha de onde o card saiu — onde se roda a moeda. Fonte unica: a lista de box do efHub (/api/public/packs), lida pelo vigia. NUNCA gravar aqui o variation_details.name do efootballdb: aquilo e etiqueta de carta e vai para etiqueta_do_card.';

create index if not exists cards_base_etiqueta_idx
  on public.cards_base (etiqueta_do_card);

-- ---------------------------------------------------------------------------
--  CONFERENCIA — o que voce deve ver depois de rodar
-- ---------------------------------------------------------------------------
select
  count(*)                                                as cards,
  count(box)                                              as com_box,
  count(etiqueta_do_card)                                 as com_etiqueta,
  count(*) filter (where box ilike 'Big Time%')           as box_ainda_com_etiqueta
from public.cards_base;

-- as prateleiras de um card so (era 598 em 18/08 — tem que cair)
select box, count(*) as cartas
from public.cards_base
where box is not null
group by box
having count(*) = 1
order by box;
