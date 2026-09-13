-- Box comercial tem origem na sincronizacao da oferta. O texto fisico de
-- PlayerVariationDetail.bin identifica a variacao e nao pode formar uma Box.

alter table clube_novo.carta_jogo
  drop constraint if exists carta_jogo_box_sem_origem_comercial_ck;

alter table clube_novo.carta_jogo
  add constraint carta_jogo_box_sem_origem_comercial_ck
  check (box is null) not valid;

update clube_novo.carta_jogo
set box = null
where box is not null;

comment on column clube_novo.carta_jogo.box is
  'Campo retirado do contrato do Extrator. Deve permanecer NULL; Box comercial pertence aos vinculos normalizados de oferta.';

create or replace view clube_novo.carta_box_oferta_v1
with (security_invoker=true) as
select
  m.card_id,
  x.box_id,
  x.box_nome,
  x.estado_box,
  x.data_oferta,
  x.origem_fingerprint
from clube_novo.box_card_em_andamento_v1 m
join clube_novo.box_contexto_contratacao_v1 x
  on x.box_id = m.box_id
where x.oferta_fonte is not null
  and nullif(btrim(x.box_nome), '') is not null;

revoke all on clube_novo.carta_box_oferta_v1 from public, anon, authenticated;

comment on view clube_novo.carta_box_oferta_v1 is
  'Leitura central das boxes comerciais comprovadas pela sincronizacao da oferta. Rotulos fisicos de variacao da carta nunca entram como box.';
