with refs as materialized (
 select l.id linha_id,l.build_bonificador_id antigo_id from clube_novo.build_linha_card l where l.build_bonificador_id is not null
 union select i.build_linha_card_id,i.build_bonificador_id_novo from clube_novo.bonificador_correcao_item_v1 i where i.build_bonificador_id_novo is not null and i.estado_item='preparado'
), fisicos as materialized (
 select card_id,max(playstyle_id) filter(where slot_fisico=1)::integer a,max(playstyle_id) filter(where slot_fisico=2)::integer d from clube_novo.carta_playstyle_jogo group by card_id
), estilos as materialized (
 select card_id,case when a<>256 and ((a>>6)&3) in (0,2) then a when d<>256 and ((d>>6)&3) in (0,2) then d else 256 end ataque,
 case when d<>256 and ((d>>6)&3) in (1,2) then d when a<>256 and ((a>>6)&3) in (1,2) then a else 256 end defesa
 from fisicos
), base as materialized (
 select r.*,l.card_id,l.funcao_id,l.posicao_id,e.ataque,e.defesa,b.bonus_playstyle_1 antigo_1,b.bonus_playstyle_2 antigo_2,b.bonus_total antigo_total,
 b.motor_versao,b.formula_fingerprint,b.carta_fingerprint,b.entrada_bonificador_fingerprint,l.carta_fingerprint linha_fp,l.estado_otimizador,l.build_otimizador_id,
 (p.linha_id is not null) publicada,p.nota_final,
 (b.carta_fingerprint is not distinct from l.carta_fingerprint and b.entrada_bonificador_fingerprint is not distinct from l.carta_fingerprint and b.carta_versao is not distinct from l.carta_versao and coalesce(cardinality(b.faltou),-1)=0) compativel
 from refs r join clube_novo.build_linha_card l on l.id=r.linha_id join clube_novo.build_bonificador b on b.id=r.antigo_id join estilos e on e.card_id=l.card_id
 left join clube_novo.build_publicacao_linha_ativa_v1 p on p.linha_id=l.id
 where l.estado<>'invalida' and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 x where x.linha_anterior_id=l.id)
), chaves as materialized (select distinct funcao_id,posicao_id,ataque,defesa from base),
esperados as materialized (select *,clube_novo.conferir_bonus_estilo_0909_v1(funcao_id,posicao_id,ataque,defesa) esperado from chaves),
auditoria as (
select b.*,e.esperado,(e.esperado->>'bonus_ataque')::numeric novo_1,(e.esperado->>'bonus_defesa')::numeric novo_2 from base b join esperados e using(funcao_id,posicao_id,ataque,defesa)
)
insert into clube_novo.correcao_estilos_item_v12(
linha_id,antigo_id,card_id,funcao_id,posicao_id,carta_fingerprint,otimizador_id,otimizador_fingerprint,
ataque,defesa,esperado,novo_1,novo_2,era_publicada,nota_anterior,publicacao_anterior)
select a.linha_id,a.antigo_id,a.card_id,a.funcao_id,a.posicao_id,a.linha_fp,l.build_otimizador_id,l.snapshot_otimizador_fingerprint,
a.ataque,a.defesa,a.esperado,a.novo_1,a.novo_2,a.publicada,a.nota_final,to_jsonb(p)
from auditoria a join clube_novo.build_linha_card l on l.id=a.linha_id
left join clube_novo.build_publicacao_linha_ativa_v1 p on p.linha_id=a.linha_id
where a.compativel and a.esperado->>'pode_calcular'='true'
and a.motor_versao='v11-0709-estilo-posicao-oficial-v1'
and a.formula_fingerprint='2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879'
and (a.antigo_1,a.antigo_2) is distinct from (a.novo_1,a.novo_2)
on conflict(linha_id) do nothing;
insert into clube_novo.correcao_estilos_execucao_v12(id,auditoria)
select 'estilos-funcao-20260909-v1',jsonb_build_object(
 'total_auditado',178528,'total_corrigir',count(*),'publicadas_corrigir',count(*) filter(where era_publicada),
 'lotes_antes',(select jsonb_agg(to_jsonb(l)) from clube_novo.bonificador_correcao_lote_v1 l),
 'prioridades_fingerprint',(select md5(string_agg(concat_ws('|',lote_id,build_linha_card_id,estado_item,tentativas,
 prioridade_grupo,prioridade_overall,prioridade_card_id,prioridade_funcao_id,prioridade_posicao_id),';' order by lote_id,build_linha_card_id))
 from clube_novo.bonificador_correcao_item_v1))
from clube_novo.correcao_estilos_item_v12
on conflict(id) do nothing;
select public.correcao_estilos_status_v12();
