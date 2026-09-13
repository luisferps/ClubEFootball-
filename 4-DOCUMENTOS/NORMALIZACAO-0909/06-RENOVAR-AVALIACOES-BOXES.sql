begin;
create table clube_novo.box_avaliacao_revisao_0909 (
 box_id bigint not null, card_id text not null, degrau smallint not null check(degrau between 1 and 3),
 versao text not null, capturado_em timestamptz not null default now(),
 analises jsonb not null check(jsonb_typeof(analises)='array'),
 primary key(box_id,card_id,degrau)
);
alter table clube_novo.box_avaliacao_revisao_0909 enable row level security;
revoke all on clube_novo.box_avaliacao_revisao_0909 from public,anon,authenticated;
grant select on clube_novo.box_avaliacao_revisao_0909 to service_role;
comment on table clube_novo.box_avaliacao_revisao_0909 is 'Revisão autorizada em 09/09/2026 das avaliações congeladas após normalização. Histórico original preservado. Fotografia por degrau; sem alteração dos motores.';
with publicadas as materialized (
 select * from clube_novo.build_publicacao_exibivel_v3
 where nota_final::text not in ('NaN','Infinity','-Infinity')
), topos as (
 select funcao_id,max(nota_final) valor from publicadas group by funcao_id
), candidatas as (
 select a.card_id,a.funcao_id,a.linha_id,a.nota_final,p.codigo_pt posicao,f.rotulo funcao,
 g.degrau,100*a.nota_final/t.valor percentual_topo,
 row_number() over(partition by a.card_id,a.funcao_id,g.degrau order by a.nota_final desc,a.linha_id) rn
 from publicadas a join topos t using(funcao_id)
 join clube_novo.funcao_sistema f on f.id=a.funcao_id
 join clube_novo.posicao_jogo p on p.id=a.posicao_id
 cross join generate_series(1,3) g(degrau)
 where t.valor>0 and (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=g.degrau)
), analises as (
 select c.card_id,c.degrau,jsonb_agg(jsonb_build_object(
 'linha_id',c.linha_id::text,'funcao',c.funcao,'posicao',c.posicao,'pontuacao',c.nota_final,
 'percentual_topo',c.percentual_topo,'etiqueta',f.rotulo,'codigo',f.codigo,'regua_versao',f.regua_versao
 ) order by c.percentual_topo desc,c.nota_final desc,c.funcao collate "C") itens
 from candidatas c
 join lateral (
 select f.* from clube_novo.regua_contratacao_faixa_v1 f join clube_novo.regua_contratacao_versao_v1 v on v.versao=f.regua_versao and v.estado='vigente'
 where c.percentual_topo>=f.percentual_minimo order by f.percentual_minimo desc limit 1
 ) f on true where c.rn=1 group by c.card_id,c.degrau
), vinculos as (
 select distinct x.box_id,x.card_id from clube_novo.carta_box_oferta_v1 x
 where x.box_id is not null and x.estado_box in ('finalizada','cadastrada')
 and not exists(select 1 from clube_novo.carta_box_oferta_v1 a where a.box_nome=x.box_nome and a.estado_box='em_andamento')
)
insert into clube_novo.box_avaliacao_revisao_0909(box_id,card_id,degrau,versao,analises)
 select v.box_id,v.card_id,g.degrau,'normalizacao-bonus-integral-20260909-v1',coalesce(a.itens,'[]'::jsonb)
 from vinculos v cross join generate_series(1,3) g(degrau)
 left join analises a on a.card_id=v.card_id and a.degrau=g.degrau;
alter function clube_novo.site_novo_box_card_analise_snapshot_v1(bigint,text,smallint)
 rename to site_novo_box_card_analise_snapshot_original_0909;
create function clube_novo.site_novo_box_card_analise_snapshot_v1(p_box_id bigint,p_card_id text,p_degrau smallint)
 returns jsonb language sql stable security definer set search_path='' as $fn$
 select coalesce(
 (select r.analises from clube_novo.box_avaliacao_revisao_0909 r where r.box_id=p_box_id and r.card_id=p_card_id and r.degrau=p_degrau),
 clube_novo.site_novo_box_card_analise_snapshot_original_0909(p_box_id,p_card_id,p_degrau));
$fn$;
revoke all on function clube_novo.site_novo_box_card_analise_snapshot_v1(bigint,text,smallint) from public,anon,authenticated;
grant execute on function clube_novo.site_novo_box_card_analise_snapshot_v1(bigint,text,smallint) to service_role;
select jsonb_build_object('fotografias',count(*),'com_analise',count(*) filter(where analises<>'[]'::jsonb),'boxes',count(distinct box_id)) from clube_novo.box_avaliacao_revisao_0909;
commit;
