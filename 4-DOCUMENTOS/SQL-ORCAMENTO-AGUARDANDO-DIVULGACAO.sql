create table clube_novo.carta_orcamento_aguardando_v1(card_id text primary key references clube_novo.carta_jogo(card_id),motivo text not null,registrado_em timestamptz not null default now());
alter table clube_novo.carta_orcamento_aguardando_v1 enable row level security;
revoke all on clube_novo.carta_orcamento_aguardando_v1 from public,anon,authenticated;
insert into clube_novo.carta_orcamento_aguardando_v1(card_id,motivo) values ('105863964635188','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.'),('105863964584785','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.'),('105863964636344','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.'),('105863964625602','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.'),('105863964635994','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.'),('105863964686707','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.'),('105863964642476','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.'),('105863964672716','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.'),('105861817219831','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.'),('105834436746221','Luis confirmou: campanha com orcamento ainda nao divulgado; aguardar nova atualizacao.');
CREATE OR REPLACE FUNCTION public.site_novo_ficha_v2(p_card_id text, p_linha_id bigint DEFAULT NULL::bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare d jsonb; ids integer[]; linha bigint; hs jsonb; v_selo boolean;
begin
  d := public.site_novo_ficha_sem_complemento_v14(p_card_id, p_linha_id);
  linha := (d#>>'{dados,build,linha_id}')::bigint;
  if linha is null then
    if exists(select 1 from clube_novo.carta_orcamento_aguardando_v1 a join clube_novo.carta_operacional_v1 c using(card_id)
      where a.card_id=p_card_id and not exists(select 1 from clube_novo.carta_nivel_evidencia_v1 e where e.card_id=a.card_id and e.nivel_maximo>=1 and e.orcamento_real=2*e.nivel_maximo-2))
    then d:=d || jsonb_build_object('mensagem','Orçamento ainda não divulgado. Aguardando uma próxima atualização do eFootball.','pendencia_orcamento','aguardando_divulgacao'); end if;
    return d;
  end if;

  select v.regua_vigente into v_selo from clube_novo.build_publicacao_exibivel_v3 v where v.linha_id = linha limit 1;
  d := jsonb_set(d, '{dados,build,regua_vigente}', to_jsonb(coalesce(v_selo,false)));


  select coalesce(c.habilidades, r.complementares) into ids
  from clube_novo.build_publicacao_exibivel_v3 v
  left join clube_novo.build_complemento_v14 c on c.build_id = v.build_otimizador_id
  left join clube_novo.complemento_recibo_v14 r on r.build_novo_id = v.build_otimizador_id
  where v.linha_id = linha
  limit 1;

  if coalesce(cardinality(ids),0) = 0 then return d; end if;

  select jsonb_agg(x || jsonb_build_object('complementar',(x->>'id')::integer = any(ids)) order by ord)
  into hs
  from jsonb_array_elements(d#>'{dados,build,habilidades_adicionadas}') with ordinality t(x,ord);

  return jsonb_set(d,'{dados,build,habilidades_adicionadas}', coalesce(hs,'[]'::jsonb));
end $function$;
