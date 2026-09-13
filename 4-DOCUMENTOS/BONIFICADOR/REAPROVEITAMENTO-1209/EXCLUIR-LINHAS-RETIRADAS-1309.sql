CREATE OR REPLACE FUNCTION clube_novo.reaproveitar_bonificador_lote_fatia_v1(p_lote uuid, p_limite integer DEFAULT 25)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
 lote clube_novo.otimizador_lote_producao_v3%rowtype;
 d clube_novo.build_linha_card%rowtype;
 fonte record;
 antes clube_novo.recalculo_1209_entrada_antes_v1%rowtype;
 entrada jsonb; esperado jsonb; prova jsonb; erro text; regra text;
 estado_item text; motivo_item text; antes_igual boolean;
 processadas integer:=0; reutilizadas integer:=0; recalcular integer:=0; bloqueadas integer:=0;
 origem_linha bigint; origem_bonus bigint;
begin
 if p_lote is null or p_limite is null or p_limite not between 1 and 100 then
  raise exception 'Lote explícito e limite de 1 a 100 obrigatórios';
 end if;
 perform pg_advisory_xact_lock(hashtextextended('reaproveitar-bonus-lote:'||p_lote::text,0));
 select * into lote from clube_novo.otimizador_lote_producao_v3 where id=p_lote for share;
 if not found or lote.estado<>'pausado' or lote.tipo_lote<>'integral'
    or lote.preparo_fingerprint_final is null
    or lote.contrato_fingerprint is distinct from clube_novo.otimizador_producao_contrato_fingerprint_v3(public.otimizador_regua_v2()) then
  raise exception 'Reaproveitamento exige lote integral preparado, pausado e da régua vigente';
 end if;
 regra:=clube_novo.bonificador_conferencia_regra_fingerprint_v1();
 for d in
  select l.* from clube_novo.build_linha_card l
  where l.lote_producao_id=p_lote and l.execucao_tipo='producao'
   and l.lote_teste_id is null and l.estado<>'invalida' and l.estado_otimizador<>'interrompido' and l.build_bonificador_id is null
   and not exists(select 1 from clube_novo.bonificador_reaproveitamento_lote_v1 a
     where a.linha_id=l.id and a.entrada_fingerprint=l.carta_fingerprint and a.regra_fingerprint=regra)
  order by l.id limit p_limite
 loop
  processadas:=processadas+1; origem_linha:=null; origem_bonus:=null; prova:='{}'::jsonb;
  estado_item:='recalcular'; motivo_item:='Nenhum resultado com identidade, entradas e componentes vigentes comprovados';
  begin
   entrada:=clube_novo.bonificador_carta_v1(d.card_id);
   if coalesce((entrada->>'pode_rodar')::boolean,false)=false
      or d.carta_fingerprint is distinct from clube_novo.bonificador_carta_fingerprint_v1(d.card_id)
      or not exists(select 1 from clube_novo.carta_jogo c where c.card_id=d.card_id and c.roda_motor
          and not coalesce(c.jogador_indisponivel,false) and c.extraido_em::text=d.carta_versao) then
    raise exception 'Entrada destino indisponível, incompleta ou fora da versão vigente';
   end if;
   esperado:=clube_novo.bonificador_componentes_vigentes_v1(d.card_id,d.funcao_id,d.posicao_id);
   select * into antes from clube_novo.recalculo_1209_entrada_antes_v1 where card_id=d.card_id;
   antes_igual:=found and coalesce((antes.entrada_bonificador->>'pode_rodar')::boolean,false)
     and (antes.entrada_bonificador-array['nome','slot1_nome','slot2_nome','proveniencia'])
       is not distinct from (entrada-array['nome','slot1_nome','slot2_nome','proveniencia']);
   for fonte in
    select s.id linha_id,b.id bonus_id
    from clube_novo.build_linha_card s
    cross join lateral (
      select s.build_bonificador_id id,2 prioridade
      union all select v.novo_id,0 from clube_novo.bonificador_altura_ia_sucessor_v13 v where v.linha_id=s.id
      union all select i.build_bonificador_id_novo,1 from clube_novo.bonificador_correcao_item_v1 i
        where i.build_linha_card_id=s.id and i.estado_item='preparado'
    ) candidato
    join clube_novo.build_bonificador b on b.id=candidato.id
    where s.id<>d.id and s.card_id=d.card_id and s.funcao_id=d.funcao_id and s.posicao_id=d.posicao_id
      and s.execucao_tipo='producao' and s.lote_teste_id is null
      and s.impeto_condicional_codigo is not distinct from d.impeto_condicional_codigo
      and s.impeto_condicional_nivel is not distinct from d.impeto_condicional_nivel
      and b.carta_fingerprint=s.carta_fingerprint and b.carta_versao=s.carta_versao
      and b.entrada_bonificador_fingerprint=b.carta_fingerprint
      and ((b.carta_fingerprint=d.carta_fingerprint and b.carta_versao=d.carta_versao)
        or (antes_igual and b.carta_fingerprint=antes.carta_fingerprint
             and b.carta_versao=(antes.carta->>'extraido_em')::timestamptz::text))
      and clube_novo.bonificador_resultado_conforme_componentes_v1(to_jsonb(b),esperado)
    order by candidato.prioridade,b.id desc,s.id desc
   loop
    prova:=clube_novo.reaproveitar_bonificador_conforme_v1(d.id,fonte.linha_id,fonte.bonus_id,'lote-integral:'||p_lote::text);
    origem_linha:=fonte.linha_id; origem_bonus:=fonte.bonus_id;
    estado_item:='reaproveitado'; motivo_item:='Valores preservados; entradas e componentes conferidos';
    exit;
   end loop;
  exception when others then
   estado_item:='bloqueado'; motivo_item:=sqlerrm; prova:=jsonb_build_object('sqlstate',sqlstate);
  end;
  insert into clube_novo.bonificador_reaproveitamento_lote_v1
   (lote_id,linha_id,estado,origem_linha_id,origem_bonus_id,entrada_fingerprint,regra_fingerprint,motivo,prova)
  values(p_lote,d.id,estado_item,origem_linha,origem_bonus,d.carta_fingerprint,regra,motivo_item,prova)
  on conflict(linha_id) do update set estado=excluded.estado,origem_linha_id=excluded.origem_linha_id,
   origem_bonus_id=excluded.origem_bonus_id,entrada_fingerprint=excluded.entrada_fingerprint,
   regra_fingerprint=excluded.regra_fingerprint,motivo=excluded.motivo,prova=excluded.prova,conferido_em=now();
  if estado_item='reaproveitado' then reutilizadas:=reutilizadas+1;
  elsif estado_item='recalcular' then recalcular:=recalcular+1; else bloqueadas:=bloqueadas+1; end if;
 end loop;
 return jsonb_build_object('lote_id',p_lote,'processadas',processadas,'reaproveitadas',reutilizadas,
   'recalcular',recalcular,'bloqueadas',bloqueadas,'sem_recalculo',true);
end $function$
;
CREATE OR REPLACE FUNCTION public.bonificador_integral_status_v1(p_lote_id uuid DEFAULT NULL::uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
end $function$
;
CREATE OR REPLACE FUNCTION public.bonificador_contexto_lote_integral_v1(p_lote_id uuid, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0)
 RETURNS TABLE(build_linha_card_id bigint, card_id text, carta_nome text, carta_tipo text, carta_box text, carta_overall integer, funcao_id bigint, funcao_codigo text, funcao_nome text, posicao_id integer, posicao_codigo text, posicao_nome text, carta_versao text, carta_fingerprint text, contrato_versao text, contrato_fingerprint text, formula_fingerprint text)
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
end $function$
;
