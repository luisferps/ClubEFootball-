create or replace function clube_novo.bonificador_conferir_resultado_atual_v1(r jsonb,cid text,fid bigint,pos integer)
returns boolean language plpgsql stable security invoker set search_path='' as $$
begin
 return clube_novo.bonificador_resultado_conforme_componentes_v1(r,clube_novo.bonificador_componentes_vigentes_v1(cid,fid,pos));
exception when others then return false;
end $$;
revoke all on function clube_novo.bonificador_conferir_resultado_atual_v1(jsonb,text,bigint,integer) from public,anon,authenticated;
CREATE OR REPLACE FUNCTION public.bonificador_contexto_fila_v7(p_limit integer DEFAULT 1000, p_offset integer DEFAULT 0)
 RETURNS TABLE(build_linha_card_id bigint, card_id text, carta_nome text, carta_tipo text, carta_box text, carta_overall integer, funcao_id bigint, funcao_codigo text, funcao_nome text, posicao_id integer, posicao_codigo text, posicao_nome text, carta_versao text, carta_fingerprint text, contrato_versao text, contrato_fingerprint text, formula_fingerprint text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  with regra_atual as materialized (select clube_novo.bonificador_conferencia_regra_fingerprint_v1() fp), candidatos as materialized (
    select l.id,l.card_id,l.funcao_id,l.posicao_id,l.carta_versao,l.carta_fingerprint,
           c.nome,c.tipo,c.box,c.overall,
           case when l.criado_em>=timestamptz '2026-09-04 22:00:00+00'
                     and c.chave_tipo_carta in ('Any2W:360','Any2W:361')
                then 0 else 1 end as prioridade_grupo
    from clube_novo.build_linha_card l
    join clube_novo.carta_jogo c on c.card_id=l.card_id
    left join clube_novo.build_bonificador b on b.id=l.build_bonificador_id
    left join clube_novo.bonificador_conferencia_vigente_v1 cv on cv.linha_id=l.id
    cross join regra_atual ra
    where coalesce((public.bonificador_regua_v4()->>'liberado_para_producao')::boolean,false)
      and l.execucao_tipo='producao'
      and l.lote_teste_id is null
      and l.estado<>'invalida'
      and not exists (select 1 from clube_novo.otimizador_lote_producao_v3 lp where lp.id=l.lote_producao_id and lp.estado='concluido')
      and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=l.id)
      and not (l.pendencias @> array['teste_nao_publicado'::text])
      and c.roda_motor is true
      and coalesce(c.jogador_indisponivel,false)=false
      and l.carta_versao=c.extraido_em::text
      and (
        b.id is null
        or b.carta_versao is distinct from l.carta_versao
        or b.carta_fingerprint is distinct from l.carta_fingerprint
        or b.entrada_bonificador_fingerprint is distinct from l.carta_fingerprint
        or case when cv.bonus_id=b.id and cv.card_id=l.card_id and cv.funcao_id=l.funcao_id and cv.posicao_id=l.posicao_id
                     and cv.entrada_fingerprint=l.carta_fingerprint and cv.resultado_fingerprint=b.resultado_fingerprint
                     and cv.regra_fingerprint=ra.fp
                then not cv.conforme
                else not clube_novo.bonificador_conferir_resultado_atual_v1(to_jsonb(b),l.card_id,l.funcao_id,l.posicao_id)
           end
      )
    order by prioridade_grupo,c.overall desc nulls last,l.card_id,l.funcao_id,l.posicao_id,l.id
    limit least(greatest(coalesce(p_limit,1000),1),5000)
    offset greatest(coalesce(p_offset,0),0)
  ), regua as (select public.bonificador_regua_v4() valor)
  select l.id,l.card_id,l.nome,l.tipo,l.box,l.overall,l.funcao_id,
         coalesce(f.sigla,'')::text,f.rotulo,l.posicao_id,
         coalesce(p.codigo_pt,'')::text,p.nome_pt,l.carta_versao,l.carta_fingerprint,
         r.valor->>'contrato',r.valor->>'contrato_fingerprint',r.valor->>'formula_fingerprint'
  from candidatos l
  join clube_novo.funcao_sistema f on f.id=l.funcao_id
  join clube_novo.posicao_jogo p on p.id=l.posicao_id
  cross join regua r
  order by l.prioridade_grupo,l.overall desc nulls last,l.card_id,l.funcao_id,l.posicao_id,l.id
$function$;

