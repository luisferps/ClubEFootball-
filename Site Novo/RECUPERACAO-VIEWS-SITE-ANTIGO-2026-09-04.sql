-- RECUPERACAO DAS VIEWS REMOVIDAS NA APOSENTADORIA DO SITE ANTIGO
-- Capturado do catálogo vivo do projeto trqqpsnafpbudtvvicch em 2026-09-04 antes da remoção.
-- Este arquivo NÃO foi executado. Use somente numa restauração deliberada e revisada.
-- Escopo: exatamente as três views que puderam ser removidas sem CASCADE.

begin;
set local lock_timeout = '5s';
set local statement_timeout = '60s';

create view public.frontend_boxes_v1 with (security_barrier=true) as
SELECT 'clube-frontend-boxes-v1'::text AS schema_versao,
    c.card_id,
    btrim(c.box) AS box_nome,
    c.nome,
        CASE
            WHEN c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text THEN c.foto_url_cloudinary
            ELSE NULL::text
        END AS foto_url_cloudinary,
    c.overall,
    c.tipo_carta_id,
    tc.nome_exibicao AS tipo_carta_nome,
    cpp.posicao_id AS posicao_principal_id,
    pp.codigo_pt AS posicao_principal_codigo,
    pp.nome_pt AS posicao_principal_nome,
    count(*) OVER (PARTITION BY (btrim(c.box))) AS box_total_cards,
    row_number() OVER (PARTITION BY (btrim(c.box)) ORDER BY c.overall DESC NULLS LAST, c.nome, c.card_id) AS rank_box_overall,
    NULLIF(btrim(c.nome), ''::text) IS NOT NULL AND cpp.posicao_id IS NOT NULL AND tc.tipo_carta_id IS NOT NULL AND (c.foto_url_cloudinary IS NULL OR c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text) AS integridade_cadastro,
    array_remove(ARRAY[
        CASE
            WHEN NULLIF(btrim(c.nome), ''::text) IS NULL THEN 'NOME_AUSENTE'::text
            ELSE NULL::text
        END,
        CASE
            WHEN cpp.posicao_id IS NULL THEN 'POSICAO_PRINCIPAL_AUSENTE'::text
            ELSE NULL::text
        END,
        CASE
            WHEN tc.tipo_carta_id IS NULL THEN 'TIPO_CARTA_NAO_RESOLVIDO'::text
            ELSE NULL::text
        END,
        CASE
            WHEN c.foto_url_cloudinary IS NOT NULL AND c.foto_url_cloudinary !~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text THEN 'FOTO_URL_NAO_CANONICA'::text
            ELSE NULL::text
        END], NULL::text) AS pendencias,
    c.visto_em AS catalogo_atualizado_em
   FROM clube_novo.carta_jogo c
     LEFT JOIN clube_novo.carta_posicao_principal_jogo cpp ON cpp.card_id = c.card_id
     LEFT JOIN clube_novo.posicao_jogo pp ON pp.id = cpp.posicao_id
     LEFT JOIN clube_novo.tipo_carta_jogo tc ON tc.tipo_carta_id = c.tipo_carta_id
  WHERE c.box IS NOT NULL AND btrim(c.box) <> ''::text AND (lower(btrim(c.box)) <> ALL (ARRAY['0'::text, 'dummy'::text, '[[not use]]'::text]));

comment on view public.frontend_boxes_v1 is 'Contrato SELECT-only da tela Boxes. Uma linha por card com box valida; nao le nem calcula Builds.';
alter view public.frontend_boxes_v1 owner to clube_frontend_view_owner;
revoke all privileges on public.frontend_boxes_v1 from public, anon, authenticated, service_role;
grant select on public.frontend_boxes_v1 to anon, authenticated;
grant all privileges on public.frontend_boxes_v1 to service_role;

create view public.frontend_home_v1 with (security_barrier=true) as
WITH box_destaque AS (
         SELECT btrim(c_1.box) AS box_nome,
            count(*) AS box_total_cards
           FROM clube_novo.carta_jogo c_1
          WHERE c_1.box IS NOT NULL AND btrim(c_1.box) <> ''::text AND (lower(btrim(c_1.box)) <> ALL (ARRAY['0'::text, 'dummy'::text, '[[not use]]'::text]))
          GROUP BY (btrim(c_1.box))
          ORDER BY (count(*)) DESC, (btrim(c_1.box))
         LIMIT 1
        ), cards_destaque AS (
         SELECT c_1.card_id,
            c_1.nome,
            c_1.posicao,
            c_1.slot_ofensivo,
            c_1.slot_ofensivo_id,
            c_1.estilo_of_novo,
            c_1.slot_defensivo,
            c_1.slot_defensivo_id,
            c_1.estilo_def_novo,
            c_1.pe,
            c_1.altura,
            c_1.peso,
            c_1.idade,
            c_1.nacionalidade,
            c_1.impeto_s1,
            c_1.impeto_s2_cond,
            c_1.vaga_s1,
            c_1.vaga_s2,
            c_1.atributos,
            c_1.habilidades,
            c_1.aptidoes,
            c_1.estilos_ia,
            c_1.extraido_em,
            c_1.tipo,
            c_1.overall,
            c_1.roda_motor,
            c_1.estilo_of_pos,
            c_1.box,
            c_1.slot_defensivo_confirmado,
            c_1.visto_em,
            c_1.extracao_id,
            c_1.lancamento,
            c_1.pe_ruim_uso,
            c_1.pe_ruim_precisao,
            c_1.resistencia_lesao,
            c_1.forma,
            c_1.slot_ofensivo_confirmado,
            c_1.corpo,
            c_1.grupo_id,
            c_1.level_cap,
            c_1.orcamento,
            c_1.cap_estimado,
            c_1.codigo_nacionalidade,
            c_1.codigo_clube,
            c_1.codigo_liga,
            c_1.chave_tipo_carta,
            c_1.registro_vinculos_jogo,
            c_1.codigo_nacionalidade_player_raw,
            c_1.codigo_tipo_carta_fisico,
            c_1.marcador_subtipo_tipo_carta,
            c_1.jogador_indisponivel,
            c_1.fonte_vinculos_jogo,
            c_1.cpk_vinculos_jogo,
            c_1.arquivo_vinculos_jogo,
            c_1.hash_player_bin_vinculos,
            c_1.contrato_vinculos_jogo,
            c_1.pode_rodar_vinculos,
            c_1.falta_o_que_vinculos,
            c_1.carregado_vinculos_em,
            c_1.tipo_carta_id,
            c_1.foto_url_cloudinary,
            d.box_nome,
            d.box_total_cards,
            row_number() OVER (ORDER BY c_1.overall DESC NULLS LAST, c_1.nome, c_1.card_id) AS rank_box_overall
           FROM clube_novo.carta_jogo c_1
             CROSS JOIN box_destaque d
          WHERE btrim(c_1.box) = d.box_nome
        )
 SELECT 'clube-frontend-home-v1'::text AS schema_versao,
    'box_destaque'::text AS secao,
    c.card_id,
    c.box_nome,
    c.nome,
        CASE
            WHEN c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text THEN c.foto_url_cloudinary
            ELSE NULL::text
        END AS foto_url_cloudinary,
    c.overall,
    c.tipo_carta_id,
    tc.nome_exibicao AS tipo_carta_nome,
    cpp.posicao_id AS posicao_principal_id,
    pp.codigo_pt AS posicao_principal_codigo,
    pp.nome_pt AS posicao_principal_nome,
    c.box_total_cards,
    c.rank_box_overall,
    NULLIF(btrim(c.nome), ''::text) IS NOT NULL AND cpp.posicao_id IS NOT NULL AND tc.tipo_carta_id IS NOT NULL AND (c.foto_url_cloudinary IS NULL OR c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text) AS integridade_cadastro,
    array_remove(ARRAY[
        CASE
            WHEN NULLIF(btrim(c.nome), ''::text) IS NULL THEN 'NOME_AUSENTE'::text
            ELSE NULL::text
        END,
        CASE
            WHEN cpp.posicao_id IS NULL THEN 'POSICAO_PRINCIPAL_AUSENTE'::text
            ELSE NULL::text
        END,
        CASE
            WHEN tc.tipo_carta_id IS NULL THEN 'TIPO_CARTA_NAO_RESOLVIDO'::text
            ELSE NULL::text
        END,
        CASE
            WHEN c.foto_url_cloudinary IS NOT NULL AND c.foto_url_cloudinary !~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text THEN 'FOTO_URL_NAO_CANONICA'::text
            ELSE NULL::text
        END], NULL::text) AS pendencias,
    c.visto_em AS catalogo_atualizado_em
   FROM cards_destaque c
     LEFT JOIN clube_novo.carta_posicao_principal_jogo cpp ON cpp.card_id = c.card_id
     LEFT JOIN clube_novo.posicao_jogo pp ON pp.id = cpp.posicao_id
     LEFT JOIN clube_novo.tipo_carta_jogo tc ON tc.tipo_carta_id = c.tipo_carta_id
  WHERE c.rank_box_overall <= 3;

comment on view public.frontend_home_v1 is 'Contrato SELECT-only da Home V1. Entrega somente a amostra cadastral deterministica da Box destaque; o topo de Builds fica fail-closed.';
alter view public.frontend_home_v1 owner to clube_frontend_view_owner;
revoke all privileges on public.frontend_home_v1 from public, anon, authenticated, service_role;
grant select on public.frontend_home_v1 to anon, authenticated;
grant all privileges on public.frontend_home_v1 to service_role;

create view public.frontend_busca_v1 with (security_barrier=false) as
SELECT 'clube-frontend-busca-v1'::text AS schema_versao,
    c.card_id,
    c.nome,
        CASE
            WHEN c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text THEN c.foto_url_cloudinary
            ELSE NULL::text
        END AS foto_url_cloudinary,
        CASE
            WHEN c.box IS NOT NULL AND btrim(c.box) <> ''::text AND (lower(btrim(c.box)) <> ALL (ARRAY['0'::text, 'dummy'::text, '[[not use]]'::text])) THEN btrim(c.box)
            ELSE NULL::text
        END AS box_nome,
    c.overall,
    c.tipo_carta_id,
    tc.nome_exibicao AS tipo_carta_nome,
    cpp.posicao_id AS posicao_principal_id,
    pp.codigo_pt AS posicao_principal_codigo,
    pp.nome_pt AS posicao_principal_nome,
    COALESCE(ps.playstyles, '[]'::jsonb) AS playstyles,
    clube_novo.frontend_normalizar_texto_v1((((((((((COALESCE(c.card_id, ''::text) || ' '::text) || COALESCE(c.nome, ''::text)) || ' '::text) || COALESCE(c.box, ''::text)) || ' '::text) || COALESCE(c.posicao, ''::text)) || ' '::text) || COALESCE(c.estilo_of_pos, ''::text)) || ' '::text) || COALESCE(c.nacionalidade, ''::text)) AS busca_texto,
    NULLIF(btrim(c.nome), ''::text) IS NOT NULL AND cpp.posicao_id IS NOT NULL AND tc.tipo_carta_id IS NOT NULL AND (c.foto_url_cloudinary IS NULL OR c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text) AS integridade_cadastro,
    array_remove(ARRAY[
        CASE
            WHEN NULLIF(btrim(c.nome), ''::text) IS NULL THEN 'NOME_AUSENTE'::text
            ELSE NULL::text
        END,
        CASE
            WHEN cpp.posicao_id IS NULL THEN 'POSICAO_PRINCIPAL_AUSENTE'::text
            ELSE NULL::text
        END,
        CASE
            WHEN tc.tipo_carta_id IS NULL THEN 'TIPO_CARTA_NAO_RESOLVIDO'::text
            ELSE NULL::text
        END,
        CASE
            WHEN c.foto_url_cloudinary IS NOT NULL AND c.foto_url_cloudinary !~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text THEN 'FOTO_URL_NAO_CANONICA'::text
            ELSE NULL::text
        END], NULL::text) AS pendencias,
    c.visto_em AS catalogo_atualizado_em,
    to_tsvector('simple'::regconfig, clube_novo.frontend_normalizar_texto_v1((((((((((COALESCE(c.card_id, ''::text) || ' '::text) || COALESCE(c.nome, ''::text)) || ' '::text) || COALESCE(c.box, ''::text)) || ' '::text) || COALESCE(c.posicao, ''::text)) || ' '::text) || COALESCE(c.estilo_of_pos, ''::text)) || ' '::text) || COALESCE(c.nacionalidade, ''::text))) AS busca_documento
   FROM clube_novo.carta_jogo c
     LEFT JOIN clube_novo.carta_posicao_principal_jogo cpp ON cpp.card_id = c.card_id
     LEFT JOIN clube_novo.posicao_jogo pp ON pp.id = cpp.posicao_id
     LEFT JOIN clube_novo.tipo_carta_jogo tc ON tc.tipo_carta_id = c.tipo_carta_id
     LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('slot', cp.slot_fisico, 'id', cp.playstyle_id, 'codigo', p.codigo_jogo, 'nome', COALESCE(p.nome_tela, p.nome_pt, p.nome_en, p.codigo_jogo), 'valor_raw', cp.valor_raw) ORDER BY cp.slot_fisico, cp.playstyle_id) AS playstyles
           FROM clube_novo.carta_playstyle_jogo cp
             JOIN clube_novo.playstyle p ON p.id_jogo = cp.playstyle_id
          WHERE cp.card_id = c.card_id) ps ON true;

comment on view public.frontend_busca_v1 is 'Contrato SELECT-only da Busca. Uma linha cadastral por card, documento FTS indexado e playstyles montados somente para o resultado; nao junta Builds no navegador.';
alter view public.frontend_busca_v1 owner to clube_frontend_view_owner;
revoke all privileges on public.frontend_busca_v1 from public, anon, authenticated, service_role;
grant select on public.frontend_busca_v1 to anon, authenticated;
grant all privileges on public.frontend_busca_v1 to service_role;

commit;

-- A recuperação das três views encadeadas da Ficha está no arquivo separado
-- RECUPERACAO-VIEWS-FICHA-SITE-ANTIGO-2026-09-04.sql.
