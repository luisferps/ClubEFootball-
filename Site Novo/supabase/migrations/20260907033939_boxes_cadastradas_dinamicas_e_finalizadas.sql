-- Boxes somente cadastradas acompanham a publicação do degrau escolhido.
-- Boxes finalizadas continuam lendo exclusivamente o snapshot congelado.
create or replace function clube_novo.site_novo_box_card_analise_snapshot_v1(
  p_box_id bigint,
  p_card_id text,
  p_degrau smallint
)
returns jsonb
language sql
stable
security definer
set search_path to ''
as $function$
  with historicas as (
    select
      linha.linha_id::text linha_id,
      s.funcao_rotulo funcao,
      coalesce(pos.codigo_pt,principal.codigo_pt,'') posicao,
      s.pontuacao_snapshot pontuacao,
      s.percentual_topo_snapshot percentual_topo,
      s.etiqueta_rotulo etiqueta,
      s.etiqueta_codigo codigo,
      s.regua_versao_snapshot regua_versao
    from clube_novo.box_card_contratacao_snapshot_v1 s
    left join clube_novo.funcao_sistema fs
      on lower(btrim(fs.rotulo))=lower(btrim(s.funcao_rotulo))
    left join lateral (
      select a.linha_id,a.posicao_id
      from clube_novo.build_publicacao_linha_ativa_v1 a
      where a.card_id=s.card_id and a.funcao_id=fs.id
        and (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
      order by abs(a.nota_final-s.pontuacao_snapshot),a.linha_id
      limit 1
    ) linha on true
    left join clube_novo.posicao_jogo pos on pos.id=linha.posicao_id
    left join lateral (
      select p.codigo_pt
      from clube_novo.carta_posicao_principal_jogo cp
      join clube_novo.posicao_jogo p on p.id=cp.posicao_id
      where cp.card_id=s.card_id
      order by cp.posicao_id
      limit 1
    ) principal on true
    where p_box_id is not null and s.box_id=p_box_id and s.card_id=p_card_id
  ),
  dinamicas_fonte as (
    select a.linha_id::text linha_id,fs.rotulo funcao,p.codigo_pt posicao,
      a.nota_final pontuacao,100::numeric*a.nota_final/topo.valor percentual_topo,
      row_number() over(partition by a.funcao_id order by a.nota_final desc,a.linha_id) rn
    from clube_novo.build_publicacao_linha_ativa_v1 a
    join clube_novo.funcao_sistema fs on fs.id=a.funcao_id
    join clube_novo.posicao_jogo p on p.id=a.posicao_id
    join lateral (
      select max(t.nota_final) valor
      from clube_novo.build_publicacao_linha_ativa_v1 t
      where t.funcao_id=a.funcao_id
        and t.nota_final::text not in ('NaN','Infinity','-Infinity')
    ) topo on topo.valor>0
    where p_box_id is null and a.card_id=p_card_id
      and (a.impeto_condicional_codigo is null or a.impeto_condicional_nivel=p_degrau)
      and a.nota_final::text not in ('NaN','Infinity','-Infinity')
  ),
  dinamicas as (
    select d.linha_id,d.funcao,d.posicao,d.pontuacao,d.percentual_topo,
      faixa.rotulo etiqueta,faixa.codigo,faixa.regua_versao
    from dinamicas_fonte d
    join lateral (
      select f.regua_versao,f.codigo,f.rotulo
      from clube_novo.regua_contratacao_faixa_v1 f
      join clube_novo.regua_contratacao_versao_v1 v
        on v.versao=f.regua_versao and v.estado='vigente'
      where d.percentual_topo>=f.percentual_minimo
      order by f.percentual_minimo desc
      limit 1
    ) faixa on true
    where d.rn=1
  ),
  analises as (
    select * from historicas
    union all
    select * from dinamicas
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id',a.linha_id,'funcao',a.funcao,'posicao',a.posicao,
    'pontuacao',a.pontuacao,'percentual_topo',a.percentual_topo,
    'etiqueta',a.etiqueta,'codigo',a.codigo,'regua_versao',a.regua_versao
  ) order by a.percentual_topo desc,a.pontuacao desc,a.funcao collate "C"),'[]'::jsonb)
  from analises a;
$function$;

revoke all on function clube_novo.site_novo_box_card_analise_snapshot_v1(bigint,text,smallint) from public;
grant execute on function clube_novo.site_novo_box_card_analise_snapshot_v1(bigint,text,smallint) to service_role;

comment on function clube_novo.site_novo_box_card_analise_snapshot_v1(bigint,text,smallint)
is 'Analise vigente para box cadastrada e snapshot imutavel para box finalizada.';
