create or replace function public.bonificador_integral_status_v1(p_lote_id uuid default null)
returns jsonb language plpgsql stable security definer set search_path='' as $$
declare lp clube_novo.otimizador_lote_producao_v3%rowtype; resumo jsonb; preparado boolean; regra text;
begin
 select * into lp from clube_novo.otimizador_lote_producao_v3
 where (p_lote_id is null or id=p_lote_id) and tipo_lote='integral'
 and contrato_fingerprint=clube_novo.otimizador_producao_contrato_fingerprint_v3(public.otimizador_regua_v2())
 order by criado_em desc limit 1;
 if not found then return jsonb_build_object('existe',false,'pode_reaproveitar',false,'pode_calcular',false); end if;
 preparado:=lp.preparo_fingerprint_final is not null and lp.estado='pausado';
 regra:=clube_novo.bonificador_conferencia_regra_fingerprint_v1();
 select jsonb_build_object('linhas',count(*),'vinculadas',count(*) filter(where l.build_bonificador_id is not null),
  'reaproveitadas',count(*) filter(where a.estado='reaproveitado'),
  'calcular_pendentes',count(*) filter(where a.estado='recalcular' and l.build_bonificador_id is null),
  'bloqueadas',count(*) filter(where a.estado='bloqueado' and l.build_bonificador_id is null),
  'nao_conferidas',count(*) filter(where l.build_bonificador_id is null and
      (a.linha_id is null or a.entrada_fingerprint is distinct from l.carta_fingerprint or a.regra_fingerprint is distinct from regra)))
 into resumo from clube_novo.build_linha_card l
 left join clube_novo.bonificador_reaproveitamento_lote_v1 a on a.linha_id=l.id
 where l.lote_producao_id=lp.id and l.execucao_tipo='producao' and l.lote_teste_id is null and l.estado<>'invalida' and l.estado_otimizador<>'interrompido';
 return resumo||jsonb_build_object('existe',true,'lote_id',lp.id,'estado',lp.estado,'preparado',preparado,
  'pode_reaproveitar',preparado and (resumo->>'nao_conferidas')::integer>0,
  'pode_calcular',preparado and (resumo->>'nao_conferidas')::integer=0
    and (resumo->>'bloqueadas')::integer=0 and (resumo->>'calcular_pendentes')::integer>0);
end $$;
revoke all on function public.bonificador_integral_status_v1(uuid) from public,anon,authenticated;
grant execute on function public.bonificador_integral_status_v1(uuid) to service_role;

create or replace function public.bonificador_integral_reaproveitar_v1(p_lote_id uuid,p_limite integer default 25)
returns jsonb language sql security definer set search_path='' as $$
 select clube_novo.reaproveitar_bonificador_lote_fatia_v1(p_lote_id,p_limite)
$$;
revoke all on function public.bonificador_integral_reaproveitar_v1(uuid,integer) from public,anon,authenticated;
grant execute on function public.bonificador_integral_reaproveitar_v1(uuid,integer) to service_role;

create or replace function public.bonificador_contexto_lote_integral_v1(p_lote_id uuid,p_limit integer default 100,p_offset integer default 0)
returns table(build_linha_card_id bigint,card_id text,carta_nome text,carta_tipo text,carta_box text,carta_overall integer,
 funcao_id bigint,funcao_codigo text,funcao_nome text,posicao_id integer,posicao_codigo text,posicao_nome text,
 carta_versao text,carta_fingerprint text,contrato_versao text,contrato_fingerprint text,formula_fingerprint text)
language plpgsql stable security definer set search_path='' as $$
declare st jsonb;
begin
 if p_lote_id is null then raise exception 'Lote integral explícito obrigatório'; end if;
 st:=public.bonificador_integral_status_v1(p_lote_id);
 if not coalesce((st->>'existe')::boolean,false) or not coalesce((st->>'preparado')::boolean,false)
  or (st->>'nao_conferidas')::integer>0 or (st->>'bloqueadas')::integer>0 then
  raise exception 'Conferência do lote integral ainda não permite calcular exceções: %',st;
 end if;
 return query
 with r as (select public.bonificador_regua_v4() v), regra as (select clube_novo.bonificador_conferencia_regra_fingerprint_v1() fp)
 select l.id,l.card_id,c.nome,c.tipo,c.box,c.overall,l.funcao_id,coalesce(f.sigla,''),f.rotulo,
  l.posicao_id,coalesce(p.codigo_pt,''),p.nome_pt,l.carta_versao,l.carta_fingerprint,
  r.v->>'contrato',r.v->>'contrato_fingerprint',r.v->>'formula_fingerprint'
 from clube_novo.build_linha_card l
 join clube_novo.bonificador_reaproveitamento_lote_v1 a on a.linha_id=l.id and a.lote_id=p_lote_id
 join clube_novo.carta_jogo c on c.card_id=l.card_id
 join clube_novo.funcao_sistema f on f.id=l.funcao_id
 join clube_novo.posicao_jogo p on p.id=l.posicao_id cross join r cross join regra
 where l.lote_producao_id=p_lote_id and a.estado='recalcular' and l.build_bonificador_id is null
  and l.execucao_tipo='producao' and l.lote_teste_id is null and l.estado<>'invalida' and l.estado_otimizador<>'interrompido'
  and c.roda_motor and not coalesce(c.jogador_indisponivel,false)
  and l.carta_versao=c.extraido_em::text and l.carta_fingerprint=clube_novo.bonificador_carta_fingerprint_v1(l.card_id)
  and a.entrada_fingerprint=l.carta_fingerprint and a.regra_fingerprint=regra.fp
  and coalesce((r.v->>'liberado_para_producao')::boolean,false)
 order by l.id limit least(greatest(p_limit,1),1000) offset greatest(p_offset,0);
end $$;
revoke all on function public.bonificador_contexto_lote_integral_v1(uuid,integer,integer) from public,anon,authenticated;
grant execute on function public.bonificador_contexto_lote_integral_v1(uuid,integer,integer) to service_role;
