CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_classificacao_v1(p_cards text[],p_degrau integer)
RETURNS TABLE(card_id text,analises jsonb) LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO '' SET jit TO 'off' SET work_mem TO '32MB' SET plan_cache_mode TO 'force_custom_plan' AS $$
with fonte as materialized (
 select a.card_id,a.linha_id,a.funcao_id,a.posicao_id,a.build_otimizador_id,a.nota_final,a.impeto_condicional_codigo,a.impeto_condicional_nivel
 from clube_novo.build_publicacao_exibivel_v3 a join (select distinct unnest(p_cards) card_id) ids on ids.card_id=a.card_id where a.nota_final::text not in ('NaN','Infinity','-Infinity')
), topos as materialized (
 select f.id funcao_id,t.nota_final topo from clube_novo.funcao_sistema f
 cross join lateral (select a.nota_final from clube_novo.build_publicacao_exibivel_v3 a
 where a.funcao_id=f.id and (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau) and a.nota_final::text not in ('NaN','Infinity','-Infinity')
 order by a.nota_final desc,a.linha_id limit 1) t
),
melhores as materialized (
 select distinct on (a.card_id) a.* from fonte a where (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
 order by a.card_id,a.nota_final desc,a.linha_id
)
select a.card_id,jsonb_build_array(jsonb_build_object('linha_id',a.linha_id::text,'funcao',f.rotulo,'posicao',p.codigo_pt,
'pontuacao',a.nota_final,'percentual_topo',100*a.nota_final/t.topo,
'codigo',r.codigo,'etiqueta',r.rotulo,'regua_versao',r.regua_versao))
from melhores a join topos t on t.funcao_id=a.funcao_id and t.topo>0
join clube_novo.funcao_sistema f on f.id=a.funcao_id join clube_novo.posicao_jogo p on p.id=a.posicao_id
cross join lateral (
 select r.* from clube_novo.regua_contratacao_faixa_v1 r join clube_novo.regua_contratacao_versao_v1 v on v.versao=r.regua_versao and v.estado='vigente'
 where 100*a.nota_final/t.topo>=r.percentual_minimo order by r.percentual_minimo desc limit 1
) r;
$$;
REVOKE ALL ON FUNCTION clube_novo.site_novo_boxes_classificacao_v1(text[],integer) FROM PUBLIC;
CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(p_cards text[],p_degrau integer)
RETURNS TABLE(card_id text,analises jsonb) LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO '' SET jit TO 'off' SET work_mem TO '32MB' SET plan_cache_mode TO 'force_custom_plan' AS $$
select m.card_id,jsonb_build_array((m.analises->0)||jsonb_build_object('regua_vigente',bo.contrato_fingerprint=rv.contrato_fingerprint))
from clube_novo.site_novo_boxes_classificacao_v1(p_cards,p_degrau) m
join clube_novo.build_publicacao_linha_ativa_v1 a on a.linha_id=(m.analises#>>'{0,linha_id}')::bigint
left join clube_novo.build_otimizador bo on bo.id=a.build_otimizador_id cross join clube_novo.regua_vigente_v1 rv;
$$;
REVOKE ALL ON FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(text[],integer) FROM PUBLIC;
ALTER FUNCTION clube_novo.site_novo_boxes_classificacao_v1(text[],integer) SET jit='off';
ALTER FUNCTION clube_novo.site_novo_boxes_classificacao_v1(text[],integer) SET work_mem='32MB';
ALTER FUNCTION clube_novo.site_novo_boxes_classificacao_v1(text[],integer) SET plan_cache_mode='force_custom_plan';
-- Leitura pronta instalada por SQL-BOXES-LEITURA-PRONTA.sql.
CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_calculo_v1(p_box text DEFAULT NULL,p_busca text DEFAULT '',p_limite integer DEFAULT 24,p_offset integer DEFAULT 0,p_ordem text DEFAULT 'recentes',p_degrau integer DEFAULT 3)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' SET jit=off AS $$
SELECT clube_novo.site_novo_boxes_leitura_v1(false,p_box,p_busca,p_limite,p_offset,p_ordem,p_degrau);
$$;
CREATE OR REPLACE FUNCTION clube_novo.site_novo_boxes_em_andamento_calculo_v1(p_box text DEFAULT NULL,p_busca text DEFAULT '',p_limite integer DEFAULT 24,p_offset integer DEFAULT 0,p_degrau integer DEFAULT 3)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' SET jit=off AS $$
SELECT clube_novo.site_novo_boxes_leitura_v1(true,p_box,p_busca,p_limite,p_offset,'pontuacao',p_degrau);
$$;
CREATE OR REPLACE FUNCTION clube_novo.site_novo_box_card_identidade_v1(p_card jsonb)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
 SET search_path TO ''
AS $function$
with pos as (
 select p.id,p.nome_pt from clube_novo.posicao_jogo p
 where p.codigo_pt=p_card->>'posicao'
)
select jsonb_build_object('posicao_nome',(select nome_pt from pos limit 1),
 'estilos',coalesce((select jsonb_agg(jsonb_build_object('id',s.playstyle_id,'nome',ps.nome_tela) order by s.slot_fisico)
 from clube_novo.carta_playstyle_jogo s join clube_novo.playstyle ps on ps.id_jogo=s.playstyle_id
 where s.card_id=p_card->>'card_id' and ps.nome_tela is not null and s.playstyle_id<>256), '[]'::jsonb));
$function$;
ALTER FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(text[],integer) SET jit TO 'off'; ALTER FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(text[],integer) SET plan_cache_mode TO 'force_custom_plan'; ALTER FUNCTION clube_novo.site_novo_boxes_melhores_linhas_v1(text[],integer) SET work_mem TO '32MB';
ALTER FUNCTION public.site_novo_boxes_em_andamento_v1(text,text,integer,integer,integer) SET jit TO 'off'; ALTER FUNCTION public.site_novo_boxes_em_andamento_v1(text,text,integer,integer,integer) SET plan_cache_mode TO 'force_custom_plan'; ALTER FUNCTION public.site_novo_boxes_v1(text,text,integer,integer,text,integer) SET jit TO 'off'; ALTER FUNCTION public.site_novo_boxes_v1(text,text,integer,integer,text,integer) SET plan_cache_mode TO 'force_custom_plan'; NOTIFY pgrst,'reload schema';
-- O prazo deve estar na entrada publica: o PostgREST aplica o limite do papel
-- antes de entrar nas funcoes internas. Mantem o limite restrito a estas RPCs.
ALTER FUNCTION public.site_novo_boxes_v1(text,text,integer,integer,text,integer) SET statement_timeout TO '10s';
ALTER FUNCTION public.site_novo_boxes_em_andamento_v1(text,text,integer,integer,integer) SET statement_timeout TO '10s';
NOTIFY pgrst,'reload schema';
