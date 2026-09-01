begin;

-- Cada superficie publica consulta somente o seu contrato. As views abaixo
-- expoem o cadastro atual de clube_novo; resultado de Build permanece fora da
-- V1 ate existir uma publicacao que grave a pontuacao final (b1 e bonus nao sao
-- combinados aqui).

create or replace function clube_novo.frontend_normalizar_texto_v1(p_texto text)
returns text
language sql
immutable
strict
parallel safe
set search_path = pg_catalog
as $function$
  select translate(
    lower(p_texto),
    'áàâãäåéèêëíìîïóòôõöúùûüçñýÿÁÀÂÃÄÅÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑÝ',
    'aaaaaaeeeeiiiiooooouuuucnyyAAAAAAEEEEIIIIOOOOOUUUUCNY'
  );
$function$;

revoke all on function clube_novo.frontend_normalizar_texto_v1(text)
  from public;
grant execute on function clube_novo.frontend_normalizar_texto_v1(text)
  to anon, authenticated;

-- As views precisam atravessar o schema privado sem conceder acesso direto a
-- anon/authenticated. Um owner sem login e sem BYPASSRLS limita esse privilegio
-- ao conjunto exato de tabelas abaixo; ele nao pode criar objetos nem escrever.
do $role$
begin
  if not exists (
    select 1 from pg_roles where rolname = 'clube_frontend_view_owner'
  ) then
    create role clube_frontend_view_owner
      nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
  end if;
end
$role$;

grant clube_frontend_view_owner to postgres;
grant usage on schema clube_novo to clube_frontend_view_owner;
grant select on
  clube_novo.carta_jogo,
  clube_novo.carta_atributo_jogo,
  clube_novo.atributo_jogo,
  clube_novo.atributo_ordem_otimizador,
  clube_novo.carta_corpo_jogo,
  clube_novo.corpo_ordem,
  clube_novo.carta_habilidade_jogo,
  clube_novo.habilidade_jogo,
  clube_novo.carta_estilo_ia_jogo,
  clube_novo.estilo_ia,
  clube_novo.carta_posicao_jogo,
  clube_novo.carta_posicao_principal_jogo,
  clube_novo.posicao_jogo,
  clube_novo.carta_impeto_jogo,
  clube_novo.impeto_jogo,
  clube_novo.impeto_atributo_jogo,
  clube_novo.carta_pe_jogo,
  clube_novo.pe,
  clube_novo.carta_playstyle_jogo,
  clube_novo.playstyle,
  clube_novo.nacionalidade_jogo,
  clube_novo.clube_jogo,
  clube_novo.liga_jogo,
  clube_novo.tipo_carta_jogo
to clube_frontend_view_owner;

grant execute on function clube_novo.frontend_normalizar_texto_v1(text)
  to clube_frontend_view_owner;

drop policy if exists frontend_view_owner_select_v1
  on clube_novo.atributo_ordem_otimizador;
create policy frontend_view_owner_select_v1
  on clube_novo.atributo_ordem_otimizador
  for select to clube_frontend_view_owner using (true);

drop policy if exists frontend_view_owner_select_v1
  on clube_novo.carta_posicao_principal_jogo;
create policy frontend_view_owner_select_v1
  on clube_novo.carta_posicao_principal_jogo
  for select to clube_frontend_view_owner using (true);

drop policy if exists frontend_view_owner_select_v1
  on clube_novo.carta_pe_jogo;
create policy frontend_view_owner_select_v1
  on clube_novo.carta_pe_jogo
  for select to clube_frontend_view_owner using (true);

drop policy if exists frontend_view_owner_select_v1
  on clube_novo.carta_playstyle_jogo;
create policy frontend_view_owner_select_v1
  on clube_novo.carta_playstyle_jogo
  for select to clube_frontend_view_owner using (true);

create index if not exists carta_jogo_frontend_box_v1_idx
  on clube_novo.carta_jogo (box, overall desc, nome, card_id)
  where box is not null
    and btrim(box) <> ''
    and lower(btrim(box)) not in ('0', 'dummy', '[[not use]]');

create index if not exists carta_jogo_frontend_busca_v1_fts_idx
  on clube_novo.carta_jogo using gin (
    to_tsvector(
      'simple'::regconfig,
      clube_novo.frontend_normalizar_texto_v1(
        coalesce(card_id, '') || ' ' ||
        coalesce(nome, '') || ' ' ||
        coalesce(box, '') || ' ' ||
        coalesce(posicao, '') || ' ' ||
        coalesce(estilo_of_pos, '') || ' ' ||
        coalesce(nacionalidade, '')
      )
    )
  );

create or replace view public.frontend_boxes_v1
with (security_barrier = true)
as
select
  'clube-frontend-boxes-v1'::text as schema_versao,
  c.card_id,
  btrim(c.box) as box_nome,
  c.nome,
  case
    when c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      then c.foto_url_cloudinary
    else null
  end as foto_url_cloudinary,
  c.overall,
  c.tipo_carta_id,
  tc.nome_exibicao as tipo_carta_nome,
  cpp.posicao_id as posicao_principal_id,
  pp.codigo_pt as posicao_principal_codigo,
  pp.nome_pt as posicao_principal_nome,
  count(*) over (partition by btrim(c.box))::bigint as box_total_cards,
  row_number() over (
    partition by btrim(c.box)
    order by c.overall desc nulls last, c.nome nulls last, c.card_id
  )::bigint as rank_box_overall,
  (
    nullif(btrim(c.nome), '') is not null
    and cpp.posicao_id is not null
    and tc.tipo_carta_id is not null
    and (
      c.foto_url_cloudinary is null
      or c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
    )
  ) as integridade_cadastro,
  array_remove(array[
    case when nullif(btrim(c.nome), '') is null then 'NOME_AUSENTE' end,
    case when cpp.posicao_id is null then 'POSICAO_PRINCIPAL_AUSENTE' end,
    case when tc.tipo_carta_id is null then 'TIPO_CARTA_NAO_RESOLVIDO' end,
    case
      when c.foto_url_cloudinary is not null
       and c.foto_url_cloudinary !~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      then 'FOTO_URL_NAO_CANONICA'
    end
  ]::text[], null) as pendencias,
  c.visto_em as catalogo_atualizado_em
from clube_novo.carta_jogo c
left join clube_novo.carta_posicao_principal_jogo cpp
  on cpp.card_id = c.card_id
left join clube_novo.posicao_jogo pp
  on pp.id = cpp.posicao_id
left join clube_novo.tipo_carta_jogo tc
  on tc.tipo_carta_id = c.tipo_carta_id
where c.box is not null
  and btrim(c.box) <> ''
  and lower(btrim(c.box)) not in ('0', 'dummy', '[[not use]]');

comment on view public.frontend_boxes_v1 is
  'Contrato SELECT-only da tela Boxes. Uma linha por card com box valida; nao le nem calcula Builds.';

create or replace view public.frontend_home_v1
with (security_barrier = true)
as
with box_destaque as (
  select
    btrim(c.box) as box_nome,
    count(*)::bigint as box_total_cards
  from clube_novo.carta_jogo c
  where c.box is not null
    and btrim(c.box) <> ''
    and lower(btrim(c.box)) not in ('0', 'dummy', '[[not use]]')
  group by btrim(c.box)
  order by count(*) desc, btrim(c.box)
  limit 1
), cards_destaque as (
  select
    c.*,
    d.box_nome,
    d.box_total_cards,
    row_number() over (
      order by c.overall desc nulls last, c.nome nulls last, c.card_id
    )::bigint as rank_box_overall
  from clube_novo.carta_jogo c
  cross join box_destaque d
  where btrim(c.box) = d.box_nome
)
select
  'clube-frontend-home-v1'::text as schema_versao,
  'box_destaque'::text as secao,
  c.card_id,
  c.box_nome,
  c.nome,
  case
    when c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      then c.foto_url_cloudinary
    else null
  end as foto_url_cloudinary,
  c.overall,
  c.tipo_carta_id,
  tc.nome_exibicao as tipo_carta_nome,
  cpp.posicao_id as posicao_principal_id,
  pp.codigo_pt as posicao_principal_codigo,
  pp.nome_pt as posicao_principal_nome,
  c.box_total_cards,
  c.rank_box_overall,
  (
    nullif(btrim(c.nome), '') is not null
    and cpp.posicao_id is not null
    and tc.tipo_carta_id is not null
    and (
      c.foto_url_cloudinary is null
      or c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
    )
  ) as integridade_cadastro,
  array_remove(array[
    case when nullif(btrim(c.nome), '') is null then 'NOME_AUSENTE' end,
    case when cpp.posicao_id is null then 'POSICAO_PRINCIPAL_AUSENTE' end,
    case when tc.tipo_carta_id is null then 'TIPO_CARTA_NAO_RESOLVIDO' end,
    case
      when c.foto_url_cloudinary is not null
       and c.foto_url_cloudinary !~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      then 'FOTO_URL_NAO_CANONICA'
    end
  ]::text[], null) as pendencias,
  c.visto_em as catalogo_atualizado_em
from cards_destaque c
left join clube_novo.carta_posicao_principal_jogo cpp
  on cpp.card_id = c.card_id
left join clube_novo.posicao_jogo pp
  on pp.id = cpp.posicao_id
left join clube_novo.tipo_carta_jogo tc
  on tc.tipo_carta_id = c.tipo_carta_id
where c.rank_box_overall <= 3;

comment on view public.frontend_home_v1 is
  'Contrato SELECT-only da Home V1. Entrega somente a amostra cadastral deterministica da Box destaque; o topo de Builds fica fail-closed.';

create or replace view public.frontend_busca_v1
/* Esta view nao esconde linhas: ela e o catalogo pesquisavel inteiro. Sem a
   barreira, o operador FTS pode descer ate o indice GIN antes do LATERAL que
   monta os playstyles. O owner continua sem login, escrita ou acesso amplo. */
with (security_barrier = false)
as
select
  'clube-frontend-busca-v1'::text as schema_versao,
  c.card_id,
  c.nome,
  case
    when c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      then c.foto_url_cloudinary
    else null
  end as foto_url_cloudinary,
  case
    when c.box is not null
     and btrim(c.box) <> ''
     and lower(btrim(c.box)) not in ('0', 'dummy', '[[not use]]')
      then btrim(c.box)
    else null
  end as box_nome,
  c.overall,
  c.tipo_carta_id,
  tc.nome_exibicao as tipo_carta_nome,
  cpp.posicao_id as posicao_principal_id,
  pp.codigo_pt as posicao_principal_codigo,
  pp.nome_pt as posicao_principal_nome,
  coalesce(ps.playstyles, '[]'::jsonb) as playstyles,
  clube_novo.frontend_normalizar_texto_v1(
    coalesce(c.card_id, '') || ' ' ||
    coalesce(c.nome, '') || ' ' ||
    coalesce(c.box, '') || ' ' ||
    coalesce(c.posicao, '') || ' ' ||
    coalesce(c.estilo_of_pos, '') || ' ' ||
    coalesce(c.nacionalidade, '')
  ) as busca_texto,
  (
    nullif(btrim(c.nome), '') is not null
    and cpp.posicao_id is not null
    and tc.tipo_carta_id is not null
    and (
      c.foto_url_cloudinary is null
      or c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
    )
  ) as integridade_cadastro,
  array_remove(array[
    case when nullif(btrim(c.nome), '') is null then 'NOME_AUSENTE' end,
    case when cpp.posicao_id is null then 'POSICAO_PRINCIPAL_AUSENTE' end,
    case when tc.tipo_carta_id is null then 'TIPO_CARTA_NAO_RESOLVIDO' end,
    case
      when c.foto_url_cloudinary is not null
       and c.foto_url_cloudinary !~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      then 'FOTO_URL_NAO_CANONICA'
    end
  ]::text[], null) as pendencias,
  c.visto_em as catalogo_atualizado_em,
  to_tsvector(
    'simple'::regconfig,
    clube_novo.frontend_normalizar_texto_v1(
      coalesce(c.card_id, '') || ' ' ||
      coalesce(c.nome, '') || ' ' ||
      coalesce(c.box, '') || ' ' ||
      coalesce(c.posicao, '') || ' ' ||
      coalesce(c.estilo_of_pos, '') || ' ' ||
      coalesce(c.nacionalidade, '')
    )
  ) as busca_documento
from clube_novo.carta_jogo c
left join clube_novo.carta_posicao_principal_jogo cpp
  on cpp.card_id = c.card_id
left join clube_novo.posicao_jogo pp
  on pp.id = cpp.posicao_id
left join clube_novo.tipo_carta_jogo tc
  on tc.tipo_carta_id = c.tipo_carta_id
left join lateral (
  select jsonb_agg(
    jsonb_build_object(
      'slot', cp.slot_fisico,
      'id', cp.playstyle_id,
      'codigo', p.codigo_jogo,
      'nome', coalesce(p.nome_tela, p.nome_pt, p.nome_en, p.codigo_jogo),
      'valor_raw', cp.valor_raw
    )
    order by cp.slot_fisico, cp.playstyle_id
  ) as playstyles
  from clube_novo.carta_playstyle_jogo cp
  join clube_novo.playstyle p on p.id_jogo = cp.playstyle_id
  where cp.card_id = c.card_id
) ps on true;

comment on view public.frontend_busca_v1 is
  'Contrato SELECT-only da Busca. Uma linha cadastral por card, documento FTS indexado e playstyles montados somente para o resultado; nao junta Builds no navegador.';

create or replace view public.frontend_ficha_v1
with (security_barrier = true)
as
select
  'clube-frontend-ficha-v1'::text as schema_versao,
  c.card_id,
  c.nome,
  case
    when c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      then c.foto_url_cloudinary
    else null
  end as foto_url_cloudinary,
  case
    when c.box is not null
     and btrim(c.box) <> ''
     and lower(btrim(c.box)) not in ('0', 'dummy', '[[not use]]')
      then btrim(c.box)
    else null
  end as box_nome,
  c.overall,
  c.tipo_carta_id,
  tc.nome_exibicao as tipo_carta_nome,
  c.posicao as posicao_origem,
  cpp.posicao_id as posicao_principal_id,
  pp.codigo_pt as posicao_principal_codigo,
  pp.nome_pt as posicao_principal_nome,
  c.slot_ofensivo,
  c.slot_ofensivo_id,
  c.slot_defensivo,
  c.slot_defensivo_id,
  c.estilo_of_pos,
  c.pe as pe_dominante,
  c.altura,
  c.peso,
  c.idade,
  c.codigo_nacionalidade,
  coalesce(nj.nome_pt_br, c.nacionalidade) as nacionalidade_nome,
  c.codigo_clube,
  cj.nome_pt_br as clube_nome,
  c.codigo_liga,
  lj.nome_pt_br as liga_nome,
  c.pe_ruim_uso,
  c.pe_ruim_precisao,
  c.resistencia_lesao,
  c.forma,
  c.level_cap,
  c.orcamento,
  c.cap_estimado,
  c.roda_motor,
  coalesce(at.itens, '[]'::jsonb) as atributos,
  coalesce(co.itens, '[]'::jsonb) as corpo,
  coalesce(po.itens, '[]'::jsonb) as posicoes,
  coalesce(ha.itens, '[]'::jsonb) as habilidades,
  coalesce(ei.itens, '[]'::jsonb) as estilos_ia,
  coalesce(pej.itens, '[]'::jsonb) as pes,
  coalesce(pl.itens, '[]'::jsonb) as playstyles,
  coalesce(im.itens, '[]'::jsonb) as impetos,
  coalesce(at.quantidade, 0) as atributos_quantidade,
  coalesce(co.quantidade, 0) as corpo_quantidade,
  coalesce(po.quantidade, 0) as posicoes_quantidade,
  coalesce(ha.quantidade, 0) as habilidades_quantidade,
  coalesce(ei.quantidade, 0) as estilos_ia_quantidade,
  coalesce(pej.quantidade, 0) as pes_quantidade,
  coalesce(pl.quantidade, 0) as playstyles_quantidade,
  coalesce(im.quantidade, 0) as impetos_quantidade,
  (
    nullif(btrim(c.nome), '') is not null
    and cpp.posicao_id is not null
    and tc.tipo_carta_id is not null
    and coalesce(at.quantidade, 0) = 26
    and coalesce(co.quantidade, 0) = 12
    and coalesce(po.quantidade, 0) > 0
    and coalesce(pej.quantidade, 0) = 3
    and coalesce(pl.quantidade, 0) = 2
    and (
      c.foto_url_cloudinary is null
      or c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
    )
  ) as integridade_ficha,
  array_remove(array[
    case when nullif(btrim(c.nome), '') is null then 'NOME_AUSENTE' end,
    case when cpp.posicao_id is null then 'POSICAO_PRINCIPAL_AUSENTE' end,
    case when tc.tipo_carta_id is null then 'TIPO_CARTA_NAO_RESOLVIDO' end,
    case when coalesce(at.quantidade, 0) <> 26 then 'ATRIBUTOS_INCOMPLETOS' end,
    case when coalesce(co.quantidade, 0) <> 12 then 'CORPO_INCOMPLETO' end,
    case when coalesce(po.quantidade, 0) = 0 then 'POSICOES_AUSENTES' end,
    case when coalesce(pej.quantidade, 0) <> 3 then 'PE_INCOMPLETO' end,
    case when coalesce(pl.quantidade, 0) <> 2 then 'PLAYSTYLES_INCOMPLETOS' end,
    case
      when c.foto_url_cloudinary is not null
       and c.foto_url_cloudinary !~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'
      then 'FOTO_URL_NAO_CANONICA'
    end
  ]::text[], null) as pendencias,
  false as build_publicada,
  'CONTRATO_PONTUACAO_FINAL_AUSENTE'::text as build_indisponivel_codigo,
  c.visto_em as catalogo_atualizado_em
from clube_novo.carta_jogo c
left join clube_novo.carta_posicao_principal_jogo cpp
  on cpp.card_id = c.card_id
left join clube_novo.posicao_jogo pp
  on pp.id = cpp.posicao_id
left join clube_novo.tipo_carta_jogo tc
  on tc.tipo_carta_id = c.tipo_carta_id
left join clube_novo.nacionalidade_jogo nj
  on nj.codigo_jogo = c.codigo_nacionalidade
left join clube_novo.clube_jogo cj
  on cj.codigo_jogo = c.codigo_clube
left join clube_novo.liga_jogo lj
  on lj.codigo_jogo = c.codigo_liga
left join lateral (
  select
    jsonb_agg(
      jsonb_build_object(
        'codigo', ca.codigo_atributo,
        'indice_otimizador', ao.indice_otimizador,
        'bit', a.bit,
        'nome', coalesce(a.nome_pt, a.nome_en, a.codigo),
        'grupo', a.grupo,
        'valor', ca.valor,
        'pode_rodar', a.pode_rodar
      )
      order by ao.indice_otimizador nulls last, a.idx_casa, ca.codigo_atributo
    ) as itens,
    count(*)::integer as quantidade
  from clube_novo.carta_atributo_jogo ca
  join clube_novo.atributo_jogo a on a.codigo = ca.codigo_atributo
  left join clube_novo.atributo_ordem_otimizador ao
    on ao.codigo_atributo = ca.codigo_atributo
  where ca.card_id = c.card_id
) at on true
left join lateral (
  select
    jsonb_agg(
      jsonb_build_object(
        'codigo', cc.codigo_corpo,
        'ordem', coo.pos,
        'nome', coalesce(coo.nome_pt, coo.nosso, coo.nome_en, cc.codigo_corpo),
        'valor', cc.valor,
        'usado_pelo_motor', coo.usado_pelo_motor,
        'pode_rodar', coo.pode_rodar
      )
      order by coo.pos nulls last, cc.codigo_corpo
    ) as itens,
    count(*)::integer as quantidade
  from clube_novo.carta_corpo_jogo cc
  join clube_novo.corpo_ordem coo on coo.codigo = cc.codigo_corpo
  where cc.card_id = c.card_id
) co on true
left join lateral (
  select
    jsonb_agg(
      jsonb_build_object(
        'id', cp.posicao_id,
        'codigo', p.codigo_pt,
        'nome', p.nome_pt,
        'nivel_aptidao', cp.nivel_aptidao,
        'nativa', cp.posicao_id = cpp.posicao_id
      )
      order by (cp.posicao_id = cpp.posicao_id) desc, cp.nivel_aptidao desc, p.id
    ) as itens,
    count(*)::integer as quantidade
  from clube_novo.carta_posicao_jogo cp
  join clube_novo.posicao_jogo p on p.id = cp.posicao_id
  where cp.card_id = c.card_id
) po on true
left join lateral (
  select
    jsonb_agg(
      jsonb_build_object(
        'skill_id', ch.skill_id,
        'ordem', ch.ordem,
        'nome', coalesce(h.nome_pt, h.nome_en, h.nome_no_motor, h.skill_id::text),
        'tipo', h.tipo,
        'fabricavel', h.fabricavel,
        'so_goleiro', h.so_goleiro,
        'vetada', h.vetada,
        'novo_2027', h.novo_2027
      )
      order by ch.ordem nulls last, h.ordem, ch.skill_id
    ) as itens,
    count(*)::integer as quantidade
  from clube_novo.carta_habilidade_jogo ch
  join clube_novo.habilidade_jogo h on h.skill_id = ch.skill_id
  where ch.card_id = c.card_id
) ha on true
left join lateral (
  select
    jsonb_agg(
      jsonb_build_object(
        'bit', ce.bit_estilo_ia,
        'codigo', e.codigo,
        'nome', coalesce(e.nome_tela, e.nome_pt, e.nome_en, e.codigo),
        'descricao', e.descricao_pt,
        'pode_rodar', e.pode_rodar
      )
      order by ce.bit_estilo_ia
    ) as itens,
    count(*)::integer as quantidade
  from clube_novo.carta_estilo_ia_jogo ce
  join clube_novo.estilo_ia e on e.bit = ce.bit_estilo_ia
  where ce.card_id = c.card_id
) ei on true
left join lateral (
  select
    jsonb_agg(
      jsonb_build_object(
        'campo', cp.campo,
        'valor', cp.valor,
        'codigo', p.codigo,
        'nome', coalesce(p.nome_pt, p.nome_en, p.codigo),
        'valor_bonus', p.valor_bonus,
        'pode_rodar', p.pode_rodar
      )
      order by cp.campo
    ) as itens,
    count(*)::integer as quantidade
  from clube_novo.carta_pe_jogo cp
  join clube_novo.pe p on p.campo = cp.campo and p.valor = cp.valor
  where cp.card_id = c.card_id
) pej on true
left join lateral (
  select
    jsonb_agg(
      jsonb_build_object(
        'slot', cp.slot_fisico,
        'id', cp.playstyle_id,
        'codigo', p.codigo_jogo,
        'nome', coalesce(p.nome_tela, p.nome_pt, p.nome_en, p.codigo_jogo),
        'valor_raw', cp.valor_raw,
        'ativo_catalogo', p.ativo,
        'pode_rodar', p.pode_rodar
      )
      order by cp.slot_fisico, cp.playstyle_id
    ) as itens,
    count(*)::integer as quantidade
  from clube_novo.carta_playstyle_jogo cp
  join clube_novo.playstyle p on p.id_jogo = cp.playstyle_id
  where cp.card_id = c.card_id
) pl on true
left join lateral (
  select
    jsonb_agg(
      jsonb_build_object(
        'slot', ci.slot,
        'codigo', ci.codigo_impeto,
        'nome', coalesce(ij.nome_pt, ij.nome_en, ci.codigo_impeto::text),
        'vaga', ci.vaga,
        'ordem', ci.ordem,
        'condicional', ci.condicional,
        'condicao_estado', ij.condicao_estado,
        'pode_rodar', ij.pode_rodar,
        'efeitos', coalesce(ef.itens, '[]'::jsonb)
      )
      order by ci.ordem, ci.slot
    ) as itens,
    count(*)::integer as quantidade
  from clube_novo.carta_impeto_jogo ci
  left join clube_novo.impeto_jogo ij on ij.codigo_jogo = ci.codigo_impeto
  left join lateral (
    select jsonb_agg(
      jsonb_build_object(
        'codigo_atributo', ia.codigo_atributo,
        'delta', ia.delta,
        'status_validacao', ia.status_validacao
      ) order by ia.ordem, ia.codigo_atributo
    ) as itens
    from clube_novo.impeto_atributo_jogo ia
    where ia.codigo_impeto = ci.codigo_impeto
  ) ef on true
  where ci.card_id = c.card_id
) im on true;

comment on view public.frontend_ficha_v1 is
  'Contrato SELECT-only da parte cadastral da Ficha. Relacoes normalizadas ja chegam agregadas; Build/score permanecem bloqueados ate contrato de publicacao explicito.';

revoke all on public.frontend_boxes_v1,
              public.frontend_home_v1,
              public.frontend_busca_v1,
              public.frontend_ficha_v1
  from public, anon, authenticated;

grant select on public.frontend_boxes_v1,
                public.frontend_home_v1,
                public.frontend_busca_v1,
                public.frontend_ficha_v1
  to anon, authenticated;

grant usage, create on schema public to clube_frontend_view_owner;
alter view public.frontend_boxes_v1 owner to clube_frontend_view_owner;
alter view public.frontend_home_v1 owner to clube_frontend_view_owner;
alter view public.frontend_busca_v1 owner to clube_frontend_view_owner;
alter view public.frontend_ficha_v1 owner to clube_frontend_view_owner;
revoke create on schema public from clube_frontend_view_owner;
revoke clube_frontend_view_owner from postgres;

notify pgrst, 'reload schema';

commit;
