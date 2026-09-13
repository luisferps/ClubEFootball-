CREATE OR REPLACE FUNCTION build_editor.catalogo_v1(p_card_id text, p_posicao_id integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare result jsonb;
begin
 perform build_editor.exigir_usuario_v1();
 if not exists(select 1 from clube_novo.carta_jogo where card_id=p_card_id) then raise exception 'Carta não encontrada.'; end if;
 select jsonb_build_object(
  'funcoes',(select coalesce(jsonb_agg(jsonb_build_object('id',f.id,'nome',f.rotulo,'posicao',fp.posicao_id) order by f.ordem),'[]')
     from clube_novo.funcao_sistema f join clube_novo.otimizador_funcao_posicao fp on fp.funcao_id=f.id
     where f.ativa and f.pode_rodar and (exists(select 1 from clube_novo.carta_posicao_jogo cp where cp.card_id=p_card_id and cp.posicao_id=fp.posicao_id and cp.nivel_aptidao>0)
      or exists(select 1 from clube_novo.carta_posicao_principal_jogo pp where pp.card_id=p_card_id and pp.posicao_id=fp.posicao_id))),
  'habilidades',(select coalesce(jsonb_agg(jsonb_build_object('id',h.skill_id,'nome',h.nome_pt,'gemeas',h.gemeas,'avaliavel',h.efeito_por_codigo is not null and not h.efeito_desconhecido) order by h.nome_pt),'[]')
     from clube_novo.habilidade_jogo h where h.tipo='comum' and (p_posicao_id=0 or h.skill_id not in (44,45,47,49))
     and not exists(select 1 from clube_novo.carta_habilidade_jogo ch where ch.card_id=p_card_id and ch.skill_id=h.skill_id)),
  'tecnicos',(select coalesce(jsonb_agg(jsonb_build_object('id',t.id::text,'nome',t.nome_en,'atributos',(select coalesce(jsonb_agg(jsonb_build_object('codigo',ta.codigo_atributo,'nome',a.nome_pt,'delta',ta.delta) order by ta.codigo_atributo),'[]') from clube_novo.tecnico_atributo_jogo ta join clube_novo.atributo_jogo a on a.codigo=ta.codigo_atributo where ta.tecnico_id=t.id and ta.confirmado),'proficiencia',(select max(proficiencia) from clube_novo.tecnico_estilo_jogo where tecnico_id=t.id and confirmado)) order by t.nome_en),'[]')
     from clube_novo.tecnico_jogo t where t.pode_rodar and exists(select 1 from clube_novo.tecnico_estilo_jogo te where te.tecnico_id=t.id and confirmado)),
  'adicionais',(select coalesce(jsonb_agg(jsonb_build_object('codigo',i.codigo_jogo,'nome',i.nome_pt,'cor',i.tipo_condicao_raw,'efeitos',(select jsonb_agg(jsonb_build_object('nome',a.nome_pt,'delta',ia.delta)) from clube_novo.impeto_atributo_jogo ia join clube_novo.atributo_jogo a on a.codigo=ia.codigo_atributo where ia.codigo_impeto=i.codigo_jogo)) order by i.nome_pt),'[]')
    from clube_novo.impeto_jogo i join build_editor.adicionais_v1(p_posicao_id) c on c.codigo=i.codigo_jogo),
  'slots',(select coalesce(jsonb_agg(jsonb_build_object('slot',c.slot,'codigo',c.codigo_impeto,'nome',i.nome_pt,'vaga',c.vaga,'condicional',c.condicional,'cor',i.tipo_condicao_raw,
      'maximo',case when c.condicional then coalesce((select efeito_maximo from clube_novo.impeto_condicao_parametro_faixa_jogo where codigo_impeto=c.codigo_impeto),(select max(delta) from clube_novo.impeto_atributo_jogo where codigo_impeto=c.codigo_impeto)) end,
      'efeitos',(select jsonb_agg(jsonb_build_object('nome',a.nome_pt,'delta',ia.delta)) from clube_novo.impeto_atributo_jogo ia join clube_novo.atributo_jogo a on a.codigo=ia.codigo_atributo where ia.codigo_impeto=c.codigo_impeto)) order by c.slot),'[]')
    from clube_novo.carta_impeto_jogo c left join clube_novo.impeto_jogo i on i.codigo_jogo=c.codigo_impeto where c.card_id=p_card_id),
  'custos',(select jsonb_object_agg(nivel,acumulado) from clube_novo.otimizador_custo_nivel)
 ) into result;
 return result;
end $function$;
