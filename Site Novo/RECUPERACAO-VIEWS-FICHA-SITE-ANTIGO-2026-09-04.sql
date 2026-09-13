-- RECUPERACAO DAS VIEWS DA FICHA REMOVIDAS NA APOSENTADORIA DO SITE ANTIGO
-- Capturado do catálogo vivo do projeto trqqpsnafpbudtvvicch em 2026-09-04 antes da remoção.
-- Este arquivo NÃO foi executado. Use somente numa restauração deliberada e revisada.
-- Ordem de restauração: ficha cadastral, ficha-build e lista de builds da ficha.

begin;
set local lock_timeout = '5s';
set local statement_timeout = '60s';
set local search_path = public, pg_catalog;

create view public.frontend_ficha_v1 with (security_barrier=true) as
SELECT 'clube-frontend-ficha-v1'::text AS schema_versao,
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
    c.posicao AS posicao_origem,
    cpp.posicao_id AS posicao_principal_id,
    pp.codigo_pt AS posicao_principal_codigo,
    pp.nome_pt AS posicao_principal_nome,
    c.slot_ofensivo,
    c.slot_ofensivo_id,
    c.slot_defensivo,
    c.slot_defensivo_id,
    c.estilo_of_pos,
    c.pe AS pe_dominante,
    c.altura,
    c.peso,
    c.idade,
    c.codigo_nacionalidade,
    COALESCE(nj.nome_pt_br, c.nacionalidade) AS nacionalidade_nome,
    c.codigo_clube,
    cj.nome_pt_br AS clube_nome,
    c.codigo_liga,
    lj.nome_pt_br AS liga_nome,
    c.pe_ruim_uso,
    c.pe_ruim_precisao,
    c.resistencia_lesao,
    c.forma,
    c.level_cap,
    c.orcamento,
    c.cap_estimado,
    c.roda_motor,
    COALESCE(at.itens, '[]'::jsonb) AS atributos,
    COALESCE(co.itens, '[]'::jsonb) AS corpo,
    COALESCE(po.itens, '[]'::jsonb) AS posicoes,
    COALESCE(ha.itens, '[]'::jsonb) AS habilidades,
    COALESCE(ei.itens, '[]'::jsonb) AS estilos_ia,
    COALESCE(pej.itens, '[]'::jsonb) AS pes,
    COALESCE(pl.itens, '[]'::jsonb) AS playstyles,
    COALESCE(im.itens, '[]'::jsonb) AS impetos,
    COALESCE(at.quantidade, 0) AS atributos_quantidade,
    COALESCE(co.quantidade, 0) AS corpo_quantidade,
    COALESCE(po.quantidade, 0) AS posicoes_quantidade,
    COALESCE(ha.quantidade, 0) AS habilidades_quantidade,
    COALESCE(ei.quantidade, 0) AS estilos_ia_quantidade,
    COALESCE(pej.quantidade, 0) AS pes_quantidade,
    COALESCE(pl.quantidade, 0) AS playstyles_quantidade,
    COALESCE(im.quantidade, 0) AS impetos_quantidade,
    NULLIF(btrim(c.nome), ''::text) IS NOT NULL AND cpp.posicao_id IS NOT NULL AND tc.tipo_carta_id IS NOT NULL AND COALESCE(at.quantidade, 0) = 26 AND COALESCE(co.quantidade, 0) = 12 AND COALESCE(po.quantidade, 0) > 0 AND COALESCE(pej.quantidade, 0) = 3 AND COALESCE(pl.quantidade, 0) = 2 AND (c.foto_url_cloudinary IS NULL OR c.foto_url_cloudinary ~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text) AS integridade_ficha,
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
            WHEN COALESCE(at.quantidade, 0) <> 26 THEN 'ATRIBUTOS_INCOMPLETOS'::text
            ELSE NULL::text
        END,
        CASE
            WHEN COALESCE(co.quantidade, 0) <> 12 THEN 'CORPO_INCOMPLETO'::text
            ELSE NULL::text
        END,
        CASE
            WHEN COALESCE(po.quantidade, 0) = 0 THEN 'POSICOES_AUSENTES'::text
            ELSE NULL::text
        END,
        CASE
            WHEN COALESCE(pej.quantidade, 0) <> 3 THEN 'PE_INCOMPLETO'::text
            ELSE NULL::text
        END,
        CASE
            WHEN COALESCE(pl.quantidade, 0) <> 2 THEN 'PLAYSTYLES_INCOMPLETOS'::text
            ELSE NULL::text
        END,
        CASE
            WHEN c.foto_url_cloudinary IS NOT NULL AND c.foto_url_cloudinary !~ '^https://res\.cloudinary\.com/[A-Za-z0-9_-]+/image/upload/'::text THEN 'FOTO_URL_NAO_CANONICA'::text
            ELSE NULL::text
        END], NULL::text) AS pendencias,
    false AS build_publicada,
    'CONTRATO_PONTUACAO_FINAL_AUSENTE'::text AS build_indisponivel_codigo,
    c.visto_em AS catalogo_atualizado_em
   FROM clube_novo.carta_jogo c
     LEFT JOIN clube_novo.carta_posicao_principal_jogo cpp ON cpp.card_id = c.card_id
     LEFT JOIN clube_novo.posicao_jogo pp ON pp.id = cpp.posicao_id
     LEFT JOIN clube_novo.tipo_carta_jogo tc ON tc.tipo_carta_id = c.tipo_carta_id
     LEFT JOIN clube_novo.nacionalidade_jogo nj ON nj.codigo_jogo = c.codigo_nacionalidade
     LEFT JOIN clube_novo.clube_jogo cj ON cj.codigo_jogo = c.codigo_clube
     LEFT JOIN clube_novo.liga_jogo lj ON lj.codigo_jogo = c.codigo_liga
     LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('codigo', ca.codigo_atributo, 'indice_otimizador', ao.indice_otimizador, 'bit', a."bit", 'nome', COALESCE(a.nome_pt, a.nome_en, a.codigo), 'grupo', a.grupo, 'valor', ca.valor, 'pode_rodar', a.pode_rodar) ORDER BY ao.indice_otimizador, a.idx_casa, ca.codigo_atributo) AS itens,
            count(*)::integer AS quantidade
           FROM clube_novo.carta_atributo_jogo ca
             JOIN clube_novo.atributo_jogo a ON a.codigo = ca.codigo_atributo
             LEFT JOIN clube_novo.atributo_ordem_otimizador ao ON ao.codigo_atributo = ca.codigo_atributo
          WHERE ca.card_id = c.card_id) at ON true
     LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('codigo', cc.codigo_corpo, 'ordem', coo.pos, 'nome', COALESCE(coo.nome_pt, coo.nosso, coo.nome_en, cc.codigo_corpo), 'valor', cc.valor, 'usado_pelo_motor', coo.usado_pelo_motor, 'pode_rodar', coo.pode_rodar) ORDER BY coo.pos, cc.codigo_corpo) AS itens,
            count(*)::integer AS quantidade
           FROM clube_novo.carta_corpo_jogo cc
             JOIN clube_novo.corpo_ordem coo ON coo.codigo = cc.codigo_corpo
          WHERE cc.card_id = c.card_id) co ON true
     LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('id', cp.posicao_id, 'codigo', p.codigo_pt, 'nome', p.nome_pt, 'nivel_aptidao', cp.nivel_aptidao, 'nativa', cp.posicao_id = cpp.posicao_id) ORDER BY (cp.posicao_id = cpp.posicao_id) DESC, cp.nivel_aptidao DESC, p.id) AS itens,
            count(*)::integer AS quantidade
           FROM clube_novo.carta_posicao_jogo cp
             JOIN clube_novo.posicao_jogo p ON p.id = cp.posicao_id
          WHERE cp.card_id = c.card_id) po ON true
     LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('skill_id', ch.skill_id, 'ordem', ch.ordem, 'nome', COALESCE(h.nome_pt, h.nome_en, h.nome_no_motor, h.skill_id::text), 'tipo', h.tipo, 'fabricavel', h.fabricavel, 'so_goleiro', h.so_goleiro, 'vetada', h.vetada, 'novo_2027', h.novo_2027) ORDER BY ch.ordem, h.ordem, ch.skill_id) AS itens,
            count(*)::integer AS quantidade
           FROM clube_novo.carta_habilidade_jogo ch
             JOIN clube_novo.habilidade_jogo h ON h.skill_id = ch.skill_id
          WHERE ch.card_id = c.card_id) ha ON true
     LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('bit', ce.bit_estilo_ia, 'codigo', e.codigo, 'nome', COALESCE(e.nome_tela, e.nome_pt, e.nome_en, e.codigo), 'descricao', e.descricao_pt, 'pode_rodar', e.pode_rodar) ORDER BY ce.bit_estilo_ia) AS itens,
            count(*)::integer AS quantidade
           FROM clube_novo.carta_estilo_ia_jogo ce
             JOIN clube_novo.estilo_ia e ON e."bit" = ce.bit_estilo_ia
          WHERE ce.card_id = c.card_id) ei ON true
     LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('campo', cp.campo, 'valor', cp.valor, 'codigo', p.codigo, 'nome', COALESCE(p.nome_pt, p.nome_en, p.codigo), 'valor_bonus', p.valor_bonus, 'pode_rodar', p.pode_rodar) ORDER BY cp.campo) AS itens,
            count(*)::integer AS quantidade
           FROM clube_novo.carta_pe_jogo cp
             JOIN clube_novo.pe p ON p.campo = cp.campo AND p.valor = cp.valor
          WHERE cp.card_id = c.card_id) pej ON true
     LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('slot', cp.slot_fisico, 'id', cp.playstyle_id, 'codigo', p.codigo_jogo, 'nome', COALESCE(p.nome_tela, p.nome_pt, p.nome_en, p.codigo_jogo), 'valor_raw', cp.valor_raw, 'ativo_catalogo', p.ativo, 'pode_rodar', p.pode_rodar) ORDER BY cp.slot_fisico, cp.playstyle_id) AS itens,
            count(*)::integer AS quantidade
           FROM clube_novo.carta_playstyle_jogo cp
             JOIN clube_novo.playstyle p ON p.id_jogo = cp.playstyle_id
          WHERE cp.card_id = c.card_id) pl ON true
     LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('slot', ci.slot, 'codigo', ci.codigo_impeto, 'nome', COALESCE(ij.nome_pt, ij.nome_en, ci.codigo_impeto::text), 'vaga', ci.vaga, 'ordem', ci.ordem, 'condicional', ci.condicional, 'condicao_estado', ij.condicao_estado, 'pode_rodar', ij.pode_rodar, 'efeitos', COALESCE(ef.itens, '[]'::jsonb)) ORDER BY ci.ordem, ci.slot) AS itens,
            count(*)::integer AS quantidade
           FROM clube_novo.carta_impeto_jogo ci
             LEFT JOIN clube_novo.impeto_jogo ij ON ij.codigo_jogo = ci.codigo_impeto
             LEFT JOIN LATERAL ( SELECT jsonb_agg(jsonb_build_object('codigo_atributo', ia.codigo_atributo, 'delta', ia.delta, 'status_validacao', ia.status_validacao) ORDER BY ia.ordem, ia.codigo_atributo) AS itens
                   FROM clube_novo.impeto_atributo_jogo ia
                  WHERE ia.codigo_impeto = ci.codigo_impeto) ef ON true
          WHERE ci.card_id = c.card_id) im ON true;

comment on view public.frontend_ficha_v1 is 'Contrato SELECT-only da parte cadastral da Ficha. Relacoes normalizadas ja chegam agregadas; Build/score permanecem bloqueados ate contrato de publicacao explicito.';
alter view public.frontend_ficha_v1 owner to clube_frontend_view_owner;
revoke all privileges on public.frontend_ficha_v1 from public, anon, authenticated, service_role;
grant select on public.frontend_ficha_v1 to anon, authenticated;
grant all privileges on public.frontend_ficha_v1 to service_role;

create view public.frontend_ficha_build_v1 as
WITH corpo AS (
         SELECT b.id AS build_bonificador_id,
            l_1.funcao_id,
            jsonb_agg(jsonb_build_object('ordem', o.pos, 'nome', o.nome_pt, 'codigo', o.codigo, 'valor_no_card', cc.valor, 'peso', m.peso, 'direcao', m.direcao, 'cortes',
                CASE
                    WHEN m.corpo_pos IS NULL THEN NULL::jsonb
                    ELSE jsonb_build_array(m.corte1, m.corte2, m.corte3, m.corte4)
                END, 'pontos', (b.bonus_fisico_detalhe ->> o.nosso)::numeric) ORDER BY o.pos) AS medidas
           FROM clube_novo.build_linha_card l_1
             JOIN clube_novo.build_bonificador b ON b.id = l_1.build_bonificador_id
             JOIN clube_novo.corpo_ordem o ON o.usado_pelo_motor
             LEFT JOIN clube_novo.carta_corpo_jogo cc ON cc.card_id = l_1.card_id AND cc.codigo_corpo = o.codigo
             LEFT JOIN clube_novo.bonificador_molde_corpo m ON m.funcao_id = l_1.funcao_id AND m.corpo_pos = o.pos
          GROUP BY b.id, l_1.funcao_id
        ), tec AS (
         SELECT t_1.tecnico_id,
            jsonb_agg(jsonb_build_object('codigo_atributo', t_1.codigo_atributo, 'delta', t_1.delta) ORDER BY t_1.ordem) AS boosts
           FROM clube_novo.tecnico_atributo_jogo t_1
          GROUP BY t_1.tecnico_id
        )
 SELECT v.linha_id,
    v.card_id,
    v.funcao_id,
    v.posicao_id,
    v.build_otimizador_id,
    v.build_bonificador_id,
    'clube-frontend-ficha-build-v1'::text AS schema_versao,
    v.publicacao_linha_fingerprint_v2,
    c.medidas AS corpo_medidas,
    v.bonus_fisico_total AS corpo_total,
    f.pes AS pe,
    v.bonus_pe AS pe_total,
    f.estilos_ia AS ia_estilos,
    v.bonus_ia AS ia_total,
    v.tecnico_id,
    t.boosts AS tecnico_boosts,
    v.impeto_adicional_codigo,
    l.impeto_condicional_codigo,
    l.impeto_condicional_nivel,
    v.barras,
    v.habilidades_adicionais,
    v.atributos_finais,
    v.arows_snapshot,
    v.bonus_posicao,
    v.bonus_playstyle_1,
    v.bonus_playstyle_2,
    v.bonus_total_bonificador,
    v.pontuacao_otimizador_normalizada,
    v.overall_final,
    v.topo_funcao,
    v.percentual_topo,
    v.estado_final,
    v.motivo_final,
    v.publicada_em,
    NULL::jsonb AS atributos_etapas,
    pa.pontos AS pontos_por_atributo
   FROM clube_novo.build_pontuacao_final_v2 v
     JOIN clube_novo.build_linha_card l ON l.id = v.linha_id
     LEFT JOIN corpo c ON c.build_bonificador_id = v.build_bonificador_id AND c.funcao_id = v.funcao_id
     LEFT JOIN tec t ON t.tecnico_id = v.tecnico_id
     LEFT JOIN frontend_ficha_v1 f ON f.card_id = v.card_id
     LEFT JOIN LATERAL ( SELECT jsonb_agg(fn_pts_regua((a.linha ->> 2)::numeric, (a.linha ->> 1)::integer, (bo.atributos_internos ->> (a.idx - 1)::integer)::numeric) ORDER BY a.idx) AS pontos
           FROM clube_novo.build_otimizador bo,
            LATERAL jsonb_array_elements(v.arows_snapshot) WITH ORDINALITY a(linha, idx)
          WHERE bo.id = v.build_otimizador_id AND bo.atributos_internos IS NOT NULL) pa ON true
  WHERE v.estado_final = 'publicada'::text;

alter view public.frontend_ficha_build_v1 owner to postgres;
revoke all privileges on public.frontend_ficha_build_v1 from public, anon, authenticated, service_role;
grant maintain, references, select, trigger, truncate on public.frontend_ficha_build_v1 to anon;
grant all privileges on public.frontend_ficha_build_v1 to authenticated;
grant all privileges on public.frontend_ficha_build_v1 to service_role;

create view public.frontend_ficha_builds_v1 as
WITH cards AS (
         SELECT frontend_ficha_v1.card_id
           FROM frontend_ficha_v1
        ), melhor AS (
         SELECT DISTINCT ON (b.card_id, b.funcao_id) b.card_id,
            b.funcao_id,
            b.linha_id,
            b.posicao_id,
            b.overall_final,
            b.percentual_topo,
            b.topo_funcao,
            b.estado_final
           FROM frontend_ficha_build_v1 b
          WHERE b.overall_final IS NOT NULL
          ORDER BY b.card_id, b.funcao_id, b.overall_final DESC, b.linha_id
        )
 SELECT c.card_id,
    f.id AS funcao_id,
    f.rotulo AS funcao_nome,
    f.sigla AS funcao_sigla,
    f.posicoes AS funcao_posicoes,
    f.familia AS funcao_familia,
    f.grupo AS funcao_grupo,
    f.ordem AS funcao_ordem,
    m.linha_id,
    m.posicao_id,
    m.overall_final,
    m.percentual_topo,
    m.topo_funcao,
    m.estado_final,
    m.linha_id IS NOT NULL AS tem_build
   FROM cards c
     CROSS JOIN clube_novo.funcao_sistema f
     LEFT JOIN melhor m ON m.card_id = c.card_id AND m.funcao_id = f.id
  WHERE f.ativa;

alter view public.frontend_ficha_builds_v1 owner to postgres;
revoke all privileges on public.frontend_ficha_builds_v1 from public, anon, authenticated, service_role;
grant maintain, references, select, trigger, truncate on public.frontend_ficha_builds_v1 to anon;
grant all privileges on public.frontend_ficha_builds_v1 to authenticated;
grant all privileges on public.frontend_ficha_builds_v1 to service_role;

commit;

