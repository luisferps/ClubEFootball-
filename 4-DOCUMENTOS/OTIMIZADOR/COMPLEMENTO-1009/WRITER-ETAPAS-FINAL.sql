CREATE OR REPLACE FUNCTION public.complemento_importar_v14(p_linha_id bigint, p_contexto text, p_resultado jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare l clube_novo.build_linha_card%rowtype; o clube_novo.build_otimizador%rowtype;
 rec clube_novo.complemento_recibo_v14%rowtype; ctx jsonb; ed jsonb; inp jsonb;
 ids integer[]; comp integer[]; novo bigint; fp text; fis jsonb; internos jsonb; fin jsonb; sid integer;
begin
 fp:=encode(extensions.digest(convert_to(p_resultado::text,'UTF8'),'sha256'),'hex');
 select * into l from clube_novo.build_linha_card where id=p_linha_id for update;
 if not found then raise exception 'Linha inexistente'; end if;
 select * into rec from clube_novo.complemento_recibo_v14 where linha_id=p_linha_id
  and build_anterior_id=(p_resultado->'correcao_pontual'->>'build_anterior')::bigint;
 if found then
  if rec.resultado_fingerprint<>fp or rec.contexto_fingerprint<>p_contexto then raise exception 'Recibo diverge do JSON'; end if;
  return jsonb_build_object('ok',true,'idempotente',true,'linha_id',p_linha_id,'build_novo_id',rec.build_novo_id,'fingerprint',fp);
 end if;
 select dados into ctx from clube_novo.complemento_contexto_v14 where fingerprint=p_contexto;
 if not found then raise exception 'Contexto desconhecido'; end if;
 if not exists(select 1 from clube_novo.carta_jogo c where c.card_id=l.card_id and c.orcamento>0 and c.sem_evolucao=false and c.codigo_tipo_carta_fisico in(0,1,5,6)) then raise exception 'Carta nao aceita adicionais confirmadas'; end if;
 if nullif(p_resultado->>'impeto_condicional_codigo','')::integer is distinct from l.impeto_condicional_codigo
 or nullif(p_resultado->>'impeto_condicional_nivel','')::integer is distinct from l.impeto_condicional_nivel
 then raise exception 'Degrau condicional divergiu'; end if;
 select * into o from clube_novo.build_otimizador where id=l.build_otimizador_id;
 if not found or o.id is distinct from (p_resultado->'correcao_pontual'->>'build_anterior')::bigint
 or o.resultado_fingerprint is distinct from p_resultado->'correcao_pontual'->>'resultado_anterior_fingerprint'
 or l.estado='invalida' or l.estado_otimizador<>'concluido' or l.execucao_tipo<>'producao'
 or o.carta_fingerprint is distinct from l.carta_fingerprint
 then raise exception 'Linha mudou: baixar novamente, nao sobrescrever'; end if;
 if exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 q where q.linha_id=l.id and q.finalizada_em is null)
 then raise exception 'Linha pertence a fila do Otimizador'; end if;
 if p_resultado->>'card_id' is distinct from l.card_id or (p_resultado->>'funcao_id')::bigint is distinct from l.funcao_id
 or p_resultado->'barras' is distinct from o.barras or (p_resultado->>'tecnico_id')::bigint is distinct from o.tecnico_id
 then raise exception 'Complemento alterou identidade ou distribuicao'; end if;
 select array_agg(value::integer order by ord) into ids from jsonb_array_elements_text(p_resultado->'habilidades') with ordinality t(value,ord);
 select array_agg(value::integer order by ord) into comp from jsonb_array_elements_text(p_resultado->'habilidades_complementares') with ordinality t(value,ord);
 if cardinality(ids)>5 or coalesce(cardinality(comp),0)=0 or ids is distinct from o.habilidades_adicionais||comp
 or cardinality(ids)<>(select count(distinct x) from unnest(ids) x)
 then raise exception 'Complemento invalido ou substituiu habilidade original'; end if;
 if exists(select 1 from clube_novo.carta_habilidade_jogo h where h.card_id=l.card_id and h.skill_id=any(comp))
 or exists(select 1 from clube_novo.habilidade_funcao_bloqueio_otimizador b where b.funcao_id=l.funcao_id and b.skill_id=any(ids))
 then raise exception 'Habilidade nativa duplicada ou bloqueada'; end if;
 foreach sid in array comp loop
  if not exists(select 1 from clube_novo.habilidade_jogo h where h.skill_id=sid and h.fabricavel and h.pode_rodar)
  then raise exception 'Habilidade nao fabricavel'; end if;
  if sid in (48,69) then
   if not exists(select 1 from jsonb_array_elements(ctx->'pesos') x where (x->>'funcao_id')::bigint=l.funcao_id and x->>'codigo_atributo'='PB:530:6' and (x->>'peso')::numeric in(7,12))
    or (sid=69 and not exists(select 1 from jsonb_array_elements(ctx->'pesos') x where (x->>'funcao_id')::bigint=l.funcao_id and x->>'codigo_atributo'='PB:498:6' and (x->>'peso')::numeric in(7,12)))
   then raise exception 'Excecao fora da funcao aprovada'; end if;
  elsif not exists(select 1 from jsonb_array_elements(ctx->'ranking') x where (x->>'funcao_id')::bigint=l.funcao_id and (x->>'skill_id')::integer=sid and (x->>'cartas_com')::bigint*10 >= (x->>'cartas_total')::bigint)
   or exists(select 1 from clube_novo.habilidade_jogo where skill_id=sid and vetada)
  then raise exception 'Candidata abaixo do corte ou vetada'; end if;
 end loop;
 inp:=jsonb_build_object('card_id',l.card_id,'funcao_id',l.funcao_id,'posicao_id',l.posicao_id,
  'tecnico_id',o.tecnico_id,'barras',o.barras,'habilidades',to_jsonb(ids),
  'impetos',coalesce((select jsonb_object_agg(ci.slot::text,o.impeto_adicional_codigo) from clube_novo.carta_impeto_jogo ci
  where ci.card_id=l.card_id and ci.vaga and ci.codigo_impeto is null and o.impeto_adicional_codigo is not null),'{}'::jsonb),'condicoes',coalesce((select jsonb_object_agg(ci.slot::text,l.impeto_condicional_nivel) from clube_novo.carta_impeto_jogo ci where ci.card_id=l.card_id and ci.condicional and ci.codigo_impeto=l.impeto_condicional_codigo),'{}'::jsonb));
 ed:=build_editor.avaliar_v1(inp);
 select jsonb_agg(x->'jogo' order by (x->>'indice')::integer),
  jsonb_agg(x->'sistema' order by (x->>'indice')::integer)
 into fis,internos from jsonb_array_elements(ed->'atributos') x;
 if fis is distinct from p_resultado->'vals_tela' or internos is distinct from p_resultado->'vals'
 or (ed->>'pontuacao_motor_bruta')::numeric is distinct from (p_resultado->>'b1')::numeric
 or jsonb_array_length(p_resultado->'cadeia')<>26 then raise exception 'Editor e recompositor divergem'; end if;
 if exists(select 1 from jsonb_array_elements(p_resultado->'cadeia') with ordinality c(x,n)
 where (x->>'attr')::integer is distinct from n-1
 or x->'na_tela' is distinct from fis->((n-1)::integer)
 or x->'final' is distinct from internos->((n-1)::integer))
 then raise exception 'Cadeia de atributos divergiu'; end if;
 insert into clube_novo.build_otimizador(tecnico_id,barras,impeto_adicional_codigo,habilidades_adicionais,pontuacao,
 contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,formula_fingerprint,resultado_fingerprint,motor_versao,
 builds_comparadas,builds_possiveis,atributos_finais,atributos_internos,arows_snapshot)
 values(o.tecnico_id,o.barras,o.impeto_adicional_codigo,ids,(p_resultado->>'b1')::numeric,
 o.contrato_versao,o.contrato_fingerprint,o.carta_versao,o.carta_fingerprint,o.formula_fingerprint,fp,o.motor_versao,
 o.builds_comparadas,o.builds_possiveis,fis,internos,clube_novo.arows_da_cadeia_v1(p_resultado->'cadeia')) returning id into novo;
 insert into clube_novo.complemento_recibo_v14 values(l.id,o.id,novo,p_contexto,fp,comp,p_resultado,now());
 update clube_novo.build_linha_card set build_otimizador_id=novo,snapshot_otimizador_fingerprint=fp,
 atualizado_em=clock_timestamp() where id=l.id;
 fin:=clube_novo.finalizar_publicar_linha_v1(l.id,'complemento_habilidades_v14');
 if fin->>'estado'='erro' then raise exception 'Finalizacao recusada: %',fin; end if;
 return jsonb_build_object('ok',true,'linha_id',l.id,'build_novo_id',novo,'fingerprint',fp,'finalizacao',fin);
end $function$

