-- Classificacao e conteudo publicados como uma unica fotografia por grau.
CREATE MATERIALIZED VIEW clube_novo.boxes_leitura_pronta_v1 AS
WITH vinculos AS MATERIALIZED (
 SELECT DISTINCT ON (x.estado_box='em_andamento',x.box_nome,x.card_id)
  x.estado_box='em_andamento' andamento,x.box_nome box,x.card_id,x.data_oferta
 FROM clube_novo.carta_box_oferta_v1 x
 WHERE x.estado_box IN ('em_andamento','finalizada','cadastrada')
 AND (x.estado_box='em_andamento' OR NOT EXISTS(
  SELECT 1 FROM clube_novo.carta_box_oferta_v1 a WHERE a.estado_box='em_andamento' AND a.box_nome=x.box_nome))
 ORDER BY x.estado_box='em_andamento',x.box_nome,x.card_id,x.box_id DESC
), identidades AS MATERIALIZED (
 SELECT c.card_id,c.nome,c.overall,c.foto_url_cloudinary foto_url,
  (SELECT p.codigo_pt FROM clube_novo.carta_posicao_principal_jogo cp
   JOIN clube_novo.posicao_jogo p ON p.id=cp.posicao_id
   WHERE cp.card_id=c.card_id ORDER BY cp.posicao_id LIMIT 1) posicao
 FROM clube_novo.carta_jogo c JOIN (SELECT DISTINCT card_id FROM vinculos) v USING(card_id)
), notas AS MATERIALIZED (
 SELECT g.degrau,m.card_id,m.analises
 FROM generate_series(1,3) g(degrau)
 CROSS JOIN LATERAL clube_novo.site_novo_boxes_melhores_linhas_v1(
  (SELECT array_agg(card_id) FROM identidades),g.degrau) m
), base AS (
 SELECT v.andamento,v.box,v.data_oferta,g.degrau,c.*,
  coalesce(n.analises,'[]'::jsonb) analises,
  (n.analises#>>'{0,pontuacao}')::numeric pontuacao,
  clube_novo.contratacao_estrelas_v1(n.analises#>>'{0,codigo}') estrelas
 FROM vinculos v JOIN identidades c USING(card_id)
 CROSS JOIN generate_series(1,3) g(degrau)
 LEFT JOIN notas n ON n.card_id=v.card_id AND n.degrau=g.degrau
), grupos AS (
 SELECT andamento,degrau,box,count(*)::integer total_cards,max(data_oferta) data_oferta,
  max(pontuacao) melhor_pontuacao,
  count(*) FILTER(WHERE estrelas=5) e5,count(*) FILTER(WHERE estrelas=4) e4,
  count(*) FILTER(WHERE estrelas=3) e3,count(*) FILTER(WHERE estrelas=2) e2,count(*) FILTER(WHERE estrelas=1) e1,
  string_agg(nome,' ') nomes,
  jsonb_agg(jsonb_build_object('card_id',card_id,'nome',nome,'posicao',posicao,
   'overall',overall,'foto_url',foto_url,'pontuacao_maxima',pontuacao,'analises',analises,
   'regua_vigente',(analises#>>'{0,regua_vigente}')::boolean)
   ORDER BY estrelas DESC NULLS LAST,pontuacao DESC NULLS LAST,card_id COLLATE "C") cards
 FROM base GROUP BY andamento,degrau,box
)
SELECT *,
 row_number() OVER(PARTITION BY andamento,degrau ORDER BY e5 DESC,e4 DESC,e3 DESC,e2 DESC,e1 DESC,melhor_pontuacao DESC NULLS LAST,box COLLATE "C") ordem_melhores,
 row_number() OVER(PARTITION BY andamento,degrau ORDER BY data_oferta DESC NULLS LAST,box COLLATE "C") ordem_ultimas
FROM grupos;
CREATE UNIQUE INDEX boxes_leitura_pronta_v1_pk ON clube_novo.boxes_leitura_pronta_v1(andamento,degrau,box);
CREATE INDEX boxes_leitura_pronta_melhores_idx ON clube_novo.boxes_leitura_pronta_v1(andamento,degrau,ordem_melhores);
CREATE INDEX boxes_leitura_pronta_ultimas_idx ON clube_novo.boxes_leitura_pronta_v1(andamento,degrau,ordem_ultimas);
REVOKE ALL ON clube_novo.boxes_leitura_pronta_v1 FROM PUBLIC,anon,authenticated,service_role;

CREATE TABLE clube_novo.boxes_leitura_revisao_v1 (
 id boolean PRIMARY KEY DEFAULT true CHECK(id),solicitada bigint NOT NULL DEFAULT 1,
 aplicada bigint NOT NULL DEFAULT 0,atualizada_em timestamptz
);
ALTER TABLE clube_novo.boxes_leitura_revisao_v1 ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON clube_novo.boxes_leitura_revisao_v1 FROM PUBLIC,anon,authenticated,service_role;
INSERT INTO clube_novo.boxes_leitura_revisao_v1(id,solicitada,aplicada,atualizada_em) VALUES(true,1,1,clock_timestamp());
CREATE FUNCTION clube_novo.boxes_leitura_invalidar_v1() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
 UPDATE clube_novo.boxes_leitura_revisao_v1 SET solicitada=solicitada+1 WHERE id;
 RETURN NULL;
END $$;
REVOKE ALL ON FUNCTION clube_novo.boxes_leitura_invalidar_v1() FROM PUBLIC;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['build_publicacao_linha_ativa_v1','box_contexto_contratacao_v1','box_card_em_andamento_v1',
 'carta_jogo','carta_posicao_principal_jogo','carta_playstyle_jogo','playstyle','posicao_jogo',
 'regua_vigente_v1','regua_contratacao_faixa_v1','regua_contratacao_versao_v1','funcao_sistema'] LOOP
 EXECUTE format('CREATE TRIGGER boxes_leitura_invalidar AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON clube_novo.%I FOR EACH STATEMENT EXECUTE FUNCTION clube_novo.boxes_leitura_invalidar_v1()',t);
 END LOOP;
END $$;
CREATE FUNCTION clube_novo.boxes_leitura_atualizar_v1() RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' SET statement_timeout='50s' SET jit=off AS $$
DECLARE revisao bigint; BEGIN
 IF NOT pg_try_advisory_xact_lock(hashtext('clube_novo.boxes_leitura_pronta_v1')) THEN RETURN false; END IF;
 SELECT solicitada INTO revisao FROM clube_novo.boxes_leitura_revisao_v1 WHERE id AND solicitada>aplicada;
 IF revisao IS NULL THEN RETURN false; END IF;
 REFRESH MATERIALIZED VIEW CONCURRENTLY clube_novo.boxes_leitura_pronta_v1;
 UPDATE clube_novo.boxes_leitura_revisao_v1 SET aplicada=revisao,atualizada_em=clock_timestamp() WHERE id;
 RETURN true;
END $$;
REVOKE ALL ON FUNCTION clube_novo.boxes_leitura_atualizar_v1() FROM PUBLIC;
SELECT cron.schedule('boxes_leitura_pronta_v1','* * * * *','select clube_novo.boxes_leitura_atualizar_v1();');

CREATE FUNCTION clube_novo.site_novo_boxes_leitura_v1(p_andamento boolean,p_box text,p_busca text,p_limite integer,p_offset integer,p_ordem text,p_degrau integer)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' SET jit=off AS $$
DECLARE resposta jsonb; BEGIN
 IF p_degrau IS NULL OR p_degrau NOT IN(1,2,3) OR p_limite IS NULL OR p_limite NOT BETWEEN 1 AND 60
 OR p_offset IS NULL OR p_offset NOT BETWEEN 0 AND 100000 OR p_busca IS NULL OR length(p_busca)>100
 OR length(p_box)>500 OR p_ordem IS NULL OR p_ordem NOT IN('recentes','pontuacao') THEN
 RAISE EXCEPTION 'Parametros invalidos' USING errcode='22023'; END IF;
 IF p_box IS NULL THEN
 WITH filtradas AS MATERIALIZED (
  SELECT * FROM clube_novo.boxes_leitura_pronta_v1 b WHERE b.andamento=p_andamento AND b.degrau=p_degrau
  AND (btrim(p_busca)='' OR clube_novo.site_novo_texto_corresponde_v1(b.box,p_busca)
   OR clube_novo.site_novo_texto_corresponde_v1(b.nomes,p_busca))
 ), pagina AS (
  SELECT * FROM filtradas ORDER BY CASE WHEN p_ordem='pontuacao' THEN ordem_melhores ELSE ordem_ultimas END
  LIMIT p_limite OFFSET p_offset
 )
 SELECT jsonb_build_object('total',(SELECT count(*) FROM filtradas),
  'total_cards',(SELECT coalesce(sum(total_cards),0) FROM filtradas),
  'itens',coalesce((SELECT jsonb_agg(jsonb_build_object('box',p.box,'total_cards',p.total_cards,
   'data_oferta',p.data_oferta,'data_rotulo',coalesce(to_char(p.data_oferta,'DD/MM/YYYY'),'Data não informada'),
   'melhor_pontuacao',p.melhor_pontuacao,'e5',p.e5,'e4',p.e4,'e3',p.e3,'e2',p.e2,'e1',p.e1,
   'cards',(SELECT jsonb_agg(item ORDER BY ord) FROM jsonb_array_elements(p.cards) WITH ORDINALITY c(item,ord) WHERE ord<=3))
   ORDER BY CASE WHEN p_ordem='pontuacao' THEN p.ordem_melhores ELSE p.ordem_ultimas END) FROM pagina p),'[]'::jsonb)) INTO resposta;
 ELSE
 WITH escolhida AS (SELECT * FROM clube_novo.boxes_leitura_pronta_v1 WHERE andamento=p_andamento AND degrau=p_degrau AND box=p_box),
 pagina AS (SELECT item,ord FROM escolhida e CROSS JOIN LATERAL jsonb_array_elements(e.cards) WITH ORDINALITY c(item,ord) ORDER BY ord LIMIT p_limite OFFSET p_offset)
 SELECT jsonb_build_object('total',coalesce((SELECT total_cards FROM escolhida),0),
  'total_cards',coalesce((SELECT total_cards FROM escolhida),0),
  'itens',coalesce((SELECT jsonb_agg(item ORDER BY ord) FROM pagina),'[]'::jsonb)) INTO resposta;
 END IF;
 RETURN resposta||jsonb_build_object('contrato','site-novo-boxes-v1','versao',1,'degrau',p_degrau,
 'modo',CASE WHEN p_box IS NULL THEN 'boxes' ELSE 'cards' END,'box',p_box,'busca',p_busca,
 'ordem',p_ordem,'limite',p_limite,'offset',p_offset,'tem_mais',(resposta->>'total')::bigint>p_offset+p_limite,
 'status',CASE WHEN jsonb_array_length(resposta->'itens')=0 THEN 'vazio' ELSE 'pronto' END,
 'regua',(SELECT jsonb_agg(jsonb_build_object('codigo',f.codigo,'rotulo',f.rotulo,'percentual_minimo',f.percentual_minimo) ORDER BY f.ordem)
 FROM clube_novo.regua_contratacao_faixa_v1 f JOIN clube_novo.regua_contratacao_versao_v1 v ON v.versao=f.regua_versao AND v.estado='vigente'));
END $$;
REVOKE ALL ON FUNCTION clube_novo.site_novo_boxes_leitura_v1(boolean,text,text,integer,integer,text,integer) FROM PUBLIC;

CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_calculo_v1(p_box text DEFAULT NULL,p_busca text DEFAULT '',p_limite integer DEFAULT 24,p_offset integer DEFAULT 0,p_ordem text DEFAULT 'recentes',p_degrau integer DEFAULT 3)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' SET jit=off AS $$
SELECT clube_novo.site_novo_boxes_leitura_v1(false,p_box,p_busca,p_limite,p_offset,p_ordem,p_degrau);
$$;
CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_em_andamento_calculo_v1(p_box text DEFAULT NULL,p_busca text DEFAULT '',p_limite integer DEFAULT 24,p_offset integer DEFAULT 0,p_degrau integer DEFAULT 3)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' SET jit=off AS $$
SELECT clube_novo.site_novo_boxes_leitura_v1(true,p_box,p_busca,p_limite,p_offset,'pontuacao',p_degrau);
$$;
NOTIFY pgrst,'reload schema';
