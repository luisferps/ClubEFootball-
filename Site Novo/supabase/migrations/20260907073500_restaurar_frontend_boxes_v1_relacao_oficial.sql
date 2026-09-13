-- Restaura o contrato SELECT-only consumido pela página Boxes cadastradas.
-- A origem é a relação oficial de boxes comerciais. O campo carta_jogo.box
-- permanece vazio e nunca volta a receber rótulos físicos de variação.

-- O dono dedicado perdeu CREATE no endurecimento do schema público. A
-- permissão é concedida somente dentro desta transação para aceitar a troca de
-- proprietário e é retirada antes do commit.
grant create on schema public to clube_frontend_view_owner;

create or replace view public.frontend_boxes_v1
with (security_barrier=true)
as
with vinculos as (
  select distinct on (btrim(x.box_nome),x.card_id)
    x.card_id,
    btrim(x.box_nome) as box_nome
  from clube_novo.carta_box_oferta_v1 x
  where x.estado_box in ('finalizada','cadastrada')
    and nullif(btrim(x.box_nome),'') is not null
    and not exists (
      select 1
      from clube_novo.carta_box_oferta_v1 atual
      where atual.estado_box='em_andamento'
        and btrim(atual.box_nome)=btrim(x.box_nome)
    )
  order by btrim(x.box_nome),x.card_id,x.box_id desc
),
base as (
  select
    'clube-frontend-boxes-v1'::text as schema_versao,
    c.card_id,
    v.box_nome,
    c.nome,
    case
      when c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
        then c.foto_url_cloudinary
      else null::text
    end as foto_url_cloudinary,
    c.overall,
    c.tipo_carta_id,
    tc.nome_exibicao as tipo_carta_nome,
    principal.posicao_id as posicao_principal_id,
    principal.codigo_pt as posicao_principal_codigo,
    principal.nome_pt as posicao_principal_nome,
    nullif(btrim(c.nome),'') is not null
      and principal.posicao_id is not null
      and tc.tipo_carta_id is not null
      and (
        c.foto_url_cloudinary is null
        or c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      ) as integridade_cadastro,
    array_remove(array[
      case when nullif(btrim(c.nome),'') is null then 'NOME_AUSENTE'::text end,
      case when principal.posicao_id is null then 'POSICAO_PRINCIPAL_AUSENTE'::text end,
      case when tc.tipo_carta_id is null then 'TIPO_CARTA_NAO_RESOLVIDO'::text end,
      case when c.foto_url_cloudinary is not null
             and c.foto_url_cloudinary !~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
           then 'FOTO_URL_NAO_CANONICA'::text end
    ],null::text) as pendencias,
    c.visto_em as catalogo_atualizado_em
  from vinculos v
  join clube_novo.carta_jogo c on c.card_id=v.card_id
  left join clube_novo.tipo_carta_jogo tc on tc.tipo_carta_id=c.tipo_carta_id
  left join lateral (
    select cp.posicao_id,p.codigo_pt,p.nome_pt
    from clube_novo.carta_posicao_principal_jogo cp
    join clube_novo.posicao_jogo p on p.id=cp.posicao_id
    where cp.card_id=c.card_id
    order by cp.posicao_id
    limit 1
  ) principal on true
)
select
  base.*,
  count(*) over(partition by box_nome) as box_total_cards,
  row_number() over(
    partition by box_nome
    order by overall desc nulls last,nome,card_id
  ) as rank_box_overall
from base;

comment on view public.frontend_boxes_v1 is
  'Contrato SELECT-only da tela Boxes cadastradas. Usa somente a relação oficial de boxes comerciais; carta_jogo.box e rótulos físicos de variação não participam.';

alter view public.frontend_boxes_v1 owner to clube_frontend_view_owner;
revoke all privileges on public.frontend_boxes_v1 from public,anon,authenticated,service_role;
grant select on public.frontend_boxes_v1 to anon,authenticated;
grant all privileges on public.frontend_boxes_v1 to service_role;

revoke create on schema public from clube_frontend_view_owner;
