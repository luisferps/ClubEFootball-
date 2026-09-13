-- Editor pessoal: mesma conversão da nota, sem busca nem restrição estratégica.
create function clube_novo.pontos_atributo_regua_v3(p_valor numeric,p_alvo numeric,p_peso numeric)
returns numeric language sql immutable strict set search_path='' as $fn$
 with x as (select p_valor-p_alvo d,least(9,floor(abs(p_valor-p_alvo))) n)
 select case when d>=0 then p_peso*(n-0.06*n*(n-1))
   when p_peso=1 then 0 else -p_peso*(n+0.25*p_peso/12*n*(n-1)/2) end from x;
$fn$;
revoke all on function clube_novo.pontos_atributo_regua_v3(numeric,numeric,numeric) from public,anon,authenticated;
grant execute on function clube_novo.pontos_atributo_regua_v3(numeric,numeric,numeric) to service_role;
CREATE OR REPLACE FUNCTION build_editor.adicionais_v1(p_pos integer)
 RETURNS TABLE(codigo integer)
 LANGUAGE sql
 STABLE
 SET search_path TO ''
AS $function$
 select i.codigo_jogo from clube_novo.impeto_jogo i
 join clube_novo.impeto_atributo_jogo a on a.codigo_impeto=i.codigo_jogo
 join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=a.codigo_atributo
 where i.condicional=false and i.condicao_estado='tipo_e_comportamento_comprovados' and i.nome_pt is not null and i.nome_pt<>'Pacote total'
 group by i.codigo_jogo
 having count(*) between 1 and 4 and bool_and(a.delta=1 and a.status_validacao in ('comprovado_biblioteca_dt870','convencao_go_aprovada_usuario_delta_fisico'))
   and (p_pos=0 or not bool_or(o.indice_otimizador>=21));
$function$;
CREATE OR REPLACE FUNCTION build_editor.avaliar_v1(p_entrada jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
 presentation build_editor.build_pessoal%rowtype;
 raw_motor numeric:=0; ceiling_motor numeric:=0; normalized_motor numeric; style_effective jsonb; style_result jsonb;
 u uuid; cid text; fid bigint; pos integer; tid bigint; card clube_novo.carta_jogo%rowtype;
 bars jsonb; skills jsonb; impetos jsonb; condicoes jsonb; native_skills integer[]; added integer[];
 r record; a record; slot record; codigo integer; nivel integer; limite integer;
 m numeric:=1; prof integer; boost numeric; imp numeric; pct numeric; fixo numeric;
 v jsonb; attrs jsonb:='[]'; maximos jsonb:='{}'; equipped jsonb:='[]'; imp_values jsonb:='{}';
 cost integer:=0; n integer; barpoints integer; denominator numeric:=0; numerator numeric:=0;
 body_sum numeric:=0; body_max numeric:=0; body_bonus numeric; body_count integer:=0;
 par jsonb; foot_use integer; foot_precision integer; foot_bonus numeric; ia_bonus numeric; style_bonus numeric:=0;
 primary_slot integer; main_style integer; other_style integer; total numeric; contador integer:=0;
begin
 u:=auth.uid();
 if p_entrada is null or octet_length(p_entrada::text)>8192 then raise exception 'Entrada de build inválida ou muito grande.'; end if;
 if jsonb_typeof(p_entrada) is distinct from 'object' or octet_length(p_entrada::text)>16000 then raise exception 'Entrada inválida.'; end if;
 if exists(select 1 from jsonb_object_keys(p_entrada) k where k not in ('card_id','funcao_id','posicao_id','tecnico_id','barras','habilidades','impetos','condicoes')) then raise exception 'Campo de entrada não permitido.'; end if;
 cid:=p_entrada->>'card_id'; fid:=(p_entrada->>'funcao_id')::bigint; pos:=(p_entrada->>'posicao_id')::integer;
 tid:=nullif(p_entrada->>'tecnico_id','')::bigint;
 select * into card from clube_novo.carta_jogo where card_id=cid;
 if not found or card.orcamento is null or card.orcamento<0 then raise exception 'Carta sem orçamento confirmado.'; end if;
 if not exists(select 1 from clube_novo.funcao_sistema where id=fid and ativa and pode_rodar)
 or not exists(select 1 from clube_novo.otimizador_funcao_posicao where funcao_id=fid and posicao_id=pos)
 or not (exists(select 1 from clube_novo.carta_posicao_principal_jogo where card_id=cid and posicao_id=pos)
 or exists(select 1 from clube_novo.carta_posicao_jogo where card_id=cid and posicao_id=pos and nivel_aptidao>0)) then
   raise exception 'Função ou posição não permitida para esta carta.';
 end if;
 bars:=p_entrada->'barras'; skills:=p_entrada->'habilidades';
 impetos:=coalesce(p_entrada->'impetos','{}'); condicoes:=coalesce(p_entrada->'condicoes','{}');
 if jsonb_typeof(bars) is distinct from 'object' or jsonb_typeof(skills) is distinct from 'array' or jsonb_array_length(skills)>5
 or jsonb_typeof(impetos)<>'object' or jsonb_typeof(condicoes)<>'object' then raise exception 'Distribuição ou escolhas inválidas.'; end if;
 if (select count(*) from jsonb_object_keys(bars))<>10 then raise exception 'Informe exatamente as dez barras.'; end if;
 if exists(select 1 from jsonb_object_keys(bars) k where not exists(select 1 from clube_novo.otimizador_barra_atributo where barra=k)) then raise exception 'Barra desconhecida.'; end if;
 for r in select b.barra,min(ca.valor) minimo,count(*) quantidade from clube_novo.otimizador_barra_atributo b
 left join clube_novo.carta_atributo_jogo ca on ca.codigo_atributo=b.codigo_atributo and ca.card_id=cid group by b.barra loop
   if r.minimo is null or jsonb_typeof(bars->r.barra) is distinct from 'number' or (bars->>r.barra)!~'^[0-9]+$' then raise exception 'Barra inválida: %',r.barra; end if;
   n:=(bars->>r.barra)::integer; limite:=greatest(0,least(25,99-r.minimo));
   if card.orcamento=0 then limite:=0; end if;
   if n>limite then raise exception 'Limite da barra %: %.',r.barra,limite; end if;
   maximos:=maximos||jsonb_build_object(r.barra,limite);
   if n>0 then select acumulado into barpoints from clube_novo.otimizador_custo_nivel where otimizador_custo_nivel.nivel=n;
     if barpoints is null then raise exception 'Custo da barra não confirmado.'; end if;
     cost:=cost+barpoints;
   end if;
 end loop;
 if cost>card.orcamento then raise exception 'Pontos insuficientes: % de %.',cost,card.orcamento; end if;
 select coalesce(array_agg(skill_id),'{}') into native_skills from clube_novo.carta_habilidade_jogo where card_id=cid;
 if exists(select 1 from jsonb_array_elements(skills) x where jsonb_typeof(x)<>'number' or x::text!~'^[0-9]+$') then raise exception 'Habilidade inválida.'; end if;
 select coalesce(array_agg(value::integer),'{}') into added from jsonb_array_elements_text(skills);
 if cardinality(added)<>(select count(distinct x) from unnest(added) x) then raise exception 'Habilidade repetida.'; end if;
 foreach codigo in array added loop
   if codigo=any(native_skills) or not exists(select 1 from clube_novo.habilidade_jogo h where h.skill_id=codigo and h.tipo='comum'
      and (pos=0 or h.skill_id not in (44,45,47,49))) then raise exception 'Habilidade não adicionável: %.',codigo; end if;
 end loop;
 if exists(select 1 from clube_novo.habilidade_jogo h where h.skill_id=any(native_skills||added) and (h.efeito_por_codigo is null or h.efeito_desconhecido)) then
   raise exception 'Há habilidade sem valoração confirmada. Não é possível inventar a nota.';
 end if;
 if tid is not null then
   if not exists(select 1 from clube_novo.tecnico_jogo where id=tid and pode_rodar) then raise exception 'Técnico não confirmado.'; end if;
   select max(proficiencia) into prof from clube_novo.tecnico_estilo_jogo where tecnico_id=tid and confirmado;
   select multiplicador into m from clube_novo.otimizador_multiplicador where ponto=prof;
   if m is null then raise exception 'Proficiência do técnico sem multiplicador confirmado.'; end if;
 end if;
 if exists(select 1 from jsonb_object_keys(impetos) k where k not in ('1','2')) or exists(select 1 from jsonb_object_keys(condicoes) k where k not in ('1','2')) then raise exception 'Slot de ímpeto inválido.'; end if;
 if exists(select 1 from jsonb_object_keys(impetos) k where not exists(select 1 from clube_novo.carta_impeto_jogo where card_id=cid and carta_impeto_jogo.slot=k::integer and vaga and codigo_impeto is null)) then raise exception 'Ímpeto nativo não pode ser substituído.'; end if;
 if exists(select 1 from jsonb_object_keys(condicoes) k where not exists(select 1 from clube_novo.carta_impeto_jogo where card_id=cid and carta_impeto_jogo.slot=k::integer and condicional)) then raise exception 'Condição de ímpeto inválida.'; end if;
 for slot in select ci.* from clube_novo.carta_impeto_jogo ci where ci.card_id=cid order by ci.slot loop
   codigo:=slot.codigo_impeto; nivel:=null;
   if slot.vaga and codigo is null then
     codigo:=nullif(impetos->>slot.slot::text,'')::integer;
     if codigo is not null and codigo not in (select c.codigo from build_editor.adicionais_v1(pos) c) then raise exception 'Ímpeto adicional não permitido.'; end if;
   end if;
   if codigo is null then continue; end if;
   if not exists(select 1 from clube_novo.impeto_jogo i where i.codigo_jogo=codigo and i.condicao_estado='tipo_e_comportamento_comprovados') then raise exception 'Ímpeto não confirmado.'; end if;
   if slot.condicional then
     select coalesce((select efeito_maximo::integer from clube_novo.impeto_condicao_parametro_faixa_jogo where codigo_impeto=codigo),max(delta)) into limite from clube_novo.impeto_atributo_jogo where codigo_impeto=codigo;
     nivel:=coalesce((condicoes->>slot.slot::text)::integer,limite);
     if limite is null or nivel<1 or nivel>limite then raise exception 'Nível condicional inválido.'; end if;
   end if;
   contador:=0;
   for a in select codigo_atributo,delta,status_validacao from clube_novo.impeto_atributo_jogo where codigo_impeto=codigo loop
     contador:=contador+1;
     if a.delta is null or coalesce(a.status_validacao,'') not in ('comprovado_biblioteca_dt870','convencao_go_aprovada_usuario_delta_fisico') then raise exception 'Efeito de ímpeto não confirmado.'; end if;
     imp_values:=imp_values||jsonb_build_object(a.codigo_atributo,coalesce((imp_values->>a.codigo_atributo)::numeric,0)+coalesce(nivel,a.delta));
   end loop;
   if contador=0 then raise exception 'Ímpeto sem efeitos confirmados.'; end if;
   equipped:=equipped||jsonb_build_array(jsonb_build_object('slot',slot.slot,'codigo',codigo,'nivel',nivel));
 end loop;
 contador:=0;
 for r in select ca.codigo_atributo,ca.valor,o.indice_otimizador,mo.alvo,mo.peso,at.nome_pt
 from clube_novo.carta_atributo_jogo ca
 join clube_novo.atributo_ordem_otimizador o using(codigo_atributo)
 join clube_novo.atributo_jogo at on at.codigo=ca.codigo_atributo
 join clube_novo.otimizador_molde mo on mo.codigo_atributo=ca.codigo_atributo and mo.versao=5 and mo.funcao_id=fid
 where ca.card_id=cid order by o.indice_otimizador loop
   contador:=contador+1;
   if r.valor is null or r.peso is null or r.alvo is null then raise exception 'Atributo ou molde incompleto.'; end if;
   select coalesce(sum((bars->>barra)::integer),0) into barpoints from clube_novo.otimizador_barra_atributo where codigo_atributo=r.codigo_atributo;
   select coalesce(sum(delta),0) into boost from clube_novo.tecnico_atributo_jogo where tecnico_id=tid and codigo_atributo=r.codigo_atributo and confirmado;
   imp:=coalesce((imp_values->>r.codigo_atributo)::numeric,0);
   select coalesce(sum(pc) filter(where rara),0)+coalesce((sum(pc) filter(where not rara)+max(pc) filter(where not rara))/2,0),
     coalesce(sum(fl) filter(where rara),0)+coalesce((sum(fl) filter(where not rara)+max(fl) filter(where not rara))/2,0)
   into pct,fixo from (select h.tipo<>'comum' rara,coalesce((h.efeito_por_codigo->r.codigo_atributo->>'pct')::numeric,0) pc,
     coalesce((h.efeito_por_codigo->r.codigo_atributo->>'flat')::numeric,0) fl from clube_novo.habilidade_jogo h where h.skill_id=any(native_skills||added)) e;
   v:=build_editor.atributo_v1(r.valor,barpoints,m,boost,imp,pct,fixo);
   numerator:=numerator+r.peso*(v->>'sistema')::numeric; denominator:=denominator+r.peso*r.alvo;
   raw_motor:=raw_motor+clube_novo.pontos_atributo_regua_v3((v->>'sistema')::numeric,r.alvo,r.peso); ceiling_motor:=ceiling_motor+r.peso*4.68;
   attrs:=attrs||jsonb_build_array(jsonb_build_object('codigo',r.codigo_atributo,'nome',r.nome_pt,'indice',r.indice_otimizador,'base',r.valor,'referencia',v->'referencia','final',v->'jogo','jogo',v->'jogo','sistema',v->'sistema'));
 end loop;
 if contador<>26 or denominator<=0 then raise exception 'Faltam atributos ou molde vigente completo.'; end if;
 select jsonb_object_agg(bp.codigo,bp.valor) into par from clube_novo.bonificador_parametro bp;
 for r in select b.*,c.valor from clube_novo.bonificador_molde_corpo b
 join clube_novo.corpo_ordem o on o.pos=b.corpo_pos
 left join clube_novo.carta_corpo_jogo c on c.codigo_corpo=o.codigo and c.card_id=cid where b.funcao_id=fid loop
   body_count:=body_count+1;
   if r.valor is null or r.direcao not in (-1,0,1) or r.peso is null or r.corte1 is null or r.corte2 is null or r.corte3 is null or r.corte4 is null then raise exception 'Físico sem dados confirmados.'; end if;
   if r.direcao<>0 then
     body_sum:=body_sum+build_editor.faixa_corpo_v1(r.valor,r.corte1,r.corte2,r.corte3,r.corte4)*r.direcao*r.peso;
     body_max:=body_max+2*r.peso;
   end if;
 end loop;
 if body_count<>12 then raise exception 'Medidas físicas incompletas.'; end if;
 body_bonus:=case when body_max=0 then 0 else round(greatest(-1,least(1,body_sum/body_max))*(par->>'bonus_corpo_max')::numeric,4) end;
 select valor into foot_use from clube_novo.carta_pe_jogo where card_id=cid and campo='pe_ruim_uso';
 select valor into foot_precision from clube_novo.carta_pe_jogo where card_id=cid and campo='pe_ruim_precisao';
 foot_bonus:=round((par->>('pe_ruim_frequencia_'||foot_use))::numeric*(par->>('pe_ruim_precisao_'||foot_precision))::numeric*(par->>'pe_ruim_teto')::numeric,4);
 select round(least(count(*),(par->>'estilo_ia_teto')::numeric)/(par->>'estilo_ia_teto')::numeric*(par->>'estilo_ia_ponto')::numeric,4) into ia_bonus from clube_novo.carta_estilo_ia_jogo where card_id=cid;
 style_effective:=clube_novo.carta_estilos_efetivos_v12(cid);
 if coalesce((style_effective->>'pode_rodar')::boolean,false)=false then raise exception 'Estilos efetivos ainda não confirmados.'; end if;
 style_result:=clube_novo.conferir_bonus_estilo_0909_v1(fid,pos,(style_effective->>'ataque_id')::integer,(style_effective->>'defesa_id')::integer);
 if coalesce((style_result->>'pode_calcular')::boolean,false)=false then raise exception 'Ativação dos estilos ainda não confirmada.'; end if;
 style_bonus:=(style_result->>'bonus_total')::numeric;
 raw_motor:=round(raw_motor,1); ceiling_motor:=round(ceiling_motor,1);
 normalized_motor:=clube_novo.normalizar_motor_v3(fid,raw_motor,ceiling_motor);
 total:=normalized_motor+body_bonus+foot_bonus+ia_bonus+style_bonus;
 if total is null then raise exception 'Parcela da nota não confirmada.'; end if;
 v:=jsonb_build_object('motor','editor-independente-v1','normalizacao_versao','normalizacao-bonus-integral-20260909-v1','pontuacao_motor_bruta',raw_motor,'teto_motor',ceiling_motor,'pontuacao_motor_normalizada',normalized_motor,'bonus_total',body_bonus+foot_bonus+ia_bonus+style_bonus,'bonus_componentes',jsonb_build_object('corpo',body_bonus,'pe',foot_bonus,'ia',ia_bonus,'estilos',style_bonus),'card_id',cid,'nota_final',total,'atributos',attrs,
   'pontos',jsonb_build_object('total',card.orcamento,'gastos',cost,'restantes',card.orcamento-cost),'limites_barras',maximos,'impetos',equipped);
 presentation.entrada:=p_entrada;presentation.resultado:=v;presentation.card_id:=cid;presentation.funcao_base_id:=fid;
 return v||jsonb_build_object('ficha',build_editor.apresentar_v1(presentation)->'build');
end $function$;
CREATE OR REPLACE FUNCTION build_editor.apresentar_v1(b build_editor.build_pessoal)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE
 SET search_path TO ''
AS $function$
declare v jsonb; skills jsonb; suggestions jsonb; coach jsonb; boosts jsonb; fname text;
begin
 if b.resultado->>'normalizacao_versao' is distinct from 'normalizacao-bonus-integral-20260909-v1' then
   b.resultado:=build_editor.avaliar_v1(b.entrada)-'ficha';
 end if;
 select rotulo into fname from clube_novo.funcao_sistema where id=b.funcao_base_id;
 select coalesce(jsonb_agg(jsonb_build_object('id',h.skill_id,'nome',h.nome_pt) order by x.ord),'[]') into skills
 from jsonb_array_elements_text(b.entrada->'habilidades') with ordinality x(id,ord)
 join clube_novo.habilidade_jogo h on h.skill_id=x.id::integer;
 select coalesce(jsonb_agg(jsonb_build_object('id',q.id,'nome',q.nome,'substitui',q.substitui) order by q.nome),'[]') into suggestions from (
  select target.skill_id id,target.nome_pt nome,jsonb_agg(jsonb_build_object('id',source.skill_id,'nome',source.nome_pt) order by x.ord) substitui
  from jsonb_array_elements_text(b.entrada->'habilidades') with ordinality x(id,ord)
  join clube_novo.habilidade_jogo source on source.skill_id=x.id::integer
  join clube_novo.habilidade_jogo target on target.skill_id=any(source.gemeas) and target.efeito_por_codigo=source.efeito_por_codigo
  where target.tipo='comum' and not b.entrada->'habilidades' @> jsonb_build_array(target.skill_id)
    and not exists(select 1 from clube_novo.carta_habilidade_jogo ch where ch.card_id=b.card_id and ch.skill_id=target.skill_id)
    and ((b.entrada->>'posicao_id')::integer=0 or target.skill_id not in (44,45,47,49))
  group by target.skill_id,target.nome_pt
 ) q;
 select jsonb_build_object('id',t.id::text,'nome',t.nome_en,'atributos',
  coalesce((select jsonb_agg(jsonb_build_object('nome',a.nome_pt,'delta',ta.delta,'codigo_atributo',ta.codigo_atributo) order by ta.codigo_atributo)
   from clube_novo.tecnico_atributo_jogo ta join clube_novo.atributo_jogo a on a.codigo=ta.codigo_atributo where ta.tecnico_id=t.id and ta.confirmado),'[]'),
  'sugeridos','[]'::jsonb,'sugeridos_estado','pronto') into coach from clube_novo.tecnico_jogo t where t.id::text=b.entrada->>'tecnico_id';
 select coalesce(jsonb_agg(jsonb_build_object('slot',ci.slot,'codigo',i.codigo_jogo,'nome',i.nome_pt,
  'tipo',case when ci.vaga then 'adicional' else 'nativo' end,'vaga_original',ci.vaga,'condicional',ci.condicional,
  'condicao_nivel',x.value->'nivel','cor_visual',case i.tipo_condicao_raw when 0 then 'azul' when 1 then 'verde' when 2 then 'amarelo' when 3 then 'roxo' when 5 then 'dourado' else 'cinza' end,
  'delta_uniforme',(select max(case when ci.condicional then coalesce((x.value->>'nivel')::numeric,ia.delta) else ia.delta end) from clube_novo.impeto_atributo_jogo ia where ia.codigo_impeto=i.codigo_jogo),
  'efeitos',coalesce((select jsonb_agg(jsonb_build_object('nome',a.nome_pt,'delta',case when ci.condicional then coalesce((x.value->>'nivel')::numeric,ia.delta) else ia.delta end,'codigo_atributo',ia.codigo_atributo))
    from clube_novo.impeto_atributo_jogo ia join clube_novo.atributo_jogo a on a.codigo=ia.codigo_atributo where ia.codigo_impeto=i.codigo_jogo),'[]')) order by ci.slot),'[]') into boosts
 from clube_novo.carta_impeto_jogo ci
 left join lateral (select value from jsonb_array_elements(b.resultado->'impetos') where (value->>'slot')::integer=ci.slot) x on true
 left join clube_novo.impeto_jogo i on i.codigo_jogo=(x.value->>'codigo')::integer where ci.card_id=b.card_id;
 v:=jsonb_build_object('pessoal_id',b.id,'linha_id',null,'nota_final',b.resultado->'nota_final',
 'funcao',(select jsonb_build_object('id',f.id,'rotulo',f.rotulo) from clube_novo.funcao_sistema f where f.id=(b.entrada->>'funcao_id')::integer),
 'posicao',(select jsonb_build_object('id',p.id,'codigo',p.codigo_pt,'nome',p.nome_pt) from clube_novo.posicao_jogo p where p.id=(b.entrada->>'posicao_id')::integer),
 'barras',(select jsonb_agg(jsonb_build_object('chave',x.key,'valor',b.entrada->'barras'->x.key,'rotulo',x.label) order by x.ord)
 from (values(1,'shooting','Chute'),(2,'passing','Passe'),(3,'dribbling','Drible'),(4,'dexterity','Destreza'),(5,'lowerBodyStrength','Força Pernas'),(6,'aerialStrength','Força Aérea'),(7,'defending','Defesa'),(8,'gk1','GO Reflexo/Salto'),(9,'gk2','GO Defesa/Alcance'),(10,'gk3','GO Encaixe/Reflexos')) x(ord,key,label)),
 'pontos_distribuicao',b.resultado->'pontos'||'{"estado":"valido"}'::jsonb,'orcamento_total',b.resultado#>'{pontos,total}',
 'atributos_completos',true,'atributos',(select jsonb_agg(jsonb_build_object('codigo',a->>'codigo','nome',a->>'nome','indice',a->'indice','valor_base',a->'base','valor_final',a->'final','valor_jogo',a->'final','valor_sistema',a->'sistema','valor_pos_evolucao',a->'referencia',
   'grupo_tela',case when (a->>'indice')::int in(0,1,2,3,4,5,6,8,9) then 'ataque' when (a->>'indice')::int in(10,11,12,15,16) then 'atletismo' when (a->>'indice')::int in(7,13,14) then 'fisico' when (a->>'indice')::int between 17 and 20 then 'defesa' else 'goleiro' end) order by (a->>'indice')::integer) from jsonb_array_elements(b.resultado->'atributos') a),
 'tecnico',coach,'impetos',boosts,'habilidades_adicionadas',skills,'habilidades_sugeridas',suggestions,'habilidades_sugeridas_estado','pronto');
 return (to_jsonb(b)-'usuario_id'-'pedido_id'-'excluido_em')||jsonb_build_object('rotulo',fname||' '||b.numero,'build',v);
end $function$;
