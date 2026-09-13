-- Motor independente do editor. Nenhuma chamada aos motores aposentados.
-- Fonte das regras: contratos físicos de clube_novo + especificação EDITOR-MOTOR.md.
begin;
create schema if not exists build_editor;
revoke all on schema build_editor from public, anon;
grant usage on schema build_editor to authenticated;

create table build_editor.build_pessoal (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references auth.users(id) on delete cascade,
  card_id text not null references clube_novo.carta_jogo(card_id),
  nome text not null check (length(btrim(nome)) between 1 and 80),
  revisao integer not null default 1 check (revisao > 0),
  pedido_id uuid not null,
  entrada jsonb not null,
  resultado jsonb not null,
  motor_versao text not null,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  unique(usuario_id, pedido_id)
);
create index build_pessoal_usuario_card on build_editor.build_pessoal(usuario_id,card_id,atualizado_em desc,id);
alter table build_editor.build_pessoal enable row level security;
create policy somente_dono on build_editor.build_pessoal for select to authenticated
  using (usuario_id=(select auth.uid()));
revoke all on build_editor.build_pessoal from public,anon,authenticated;

-- Cálculos puros: apenas a regra vigente, sem alternativas nem fallbacks históricos.
create function build_editor.atributo_v1(p_base numeric,p_barras integer,p_m numeric,p_boost numeric,p_impeto numeric,p_pct numeric,p_fixo numeric)
returns jsonb language sql immutable strict set search_path='' as $$
  with r as (select least(99,p_base+p_barras) ref),
  j as (select ref,case when p_m=1 then ref else least(99,greatest(40,ref+trunc(ref*(p_m-1)))) end+p_boost+p_impeto jogo from r)
  select jsonb_build_object('referencia',ref,'jogo',jogo,'sistema',jogo+ceil(ref*p_pct/100+p_fixo)) from j;
$$;
create function build_editor.faixa_corpo_v1(p_valor numeric,p_c1 numeric,p_c2 numeric,p_c3 numeric,p_c4 numeric)
returns integer language sql immutable strict set search_path='' as $$
 select case when p_valor<=p_c1 then -2 when p_valor<=p_c2 then -1 when p_valor<=p_c3 then 0 when p_valor<=p_c4 then 1 else 2 end;
$$;
create function build_editor.exigir_usuario_v1() returns uuid
language plpgsql stable security definer set search_path='' as $$
declare u uuid:=auth.uid();
begin
 if u is null or not exists(select 1 from auth.users where id=u and not is_anonymous) then
   raise exception using errcode='42501',message='Entre na sua conta para editar e salvar builds.';
 end if;
 return u;
end $$;

-- Catálogo adicional é explícito: não condicional, até quatro efeitos +1.
create function build_editor.adicionais_v1(p_pos integer) returns table(codigo integer)
language sql stable set search_path='' as $$
 select i.codigo_jogo from clube_novo.impeto_jogo i
 join clube_novo.impeto_atributo_jogo a on a.codigo_impeto=i.codigo_jogo
 join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=a.codigo_atributo
 where i.condicional=false and i.pode_rodar and i.nome_pt is not null and i.nome_pt<>'Pacote total'
 group by i.codigo_jogo
 having count(*) between 1 and 4 and bool_and(a.delta=1)
   and (p_pos=0 or not bool_or(o.indice_otimizador>=21));
$$;

create function build_editor.avaliar_v1(p_entrada jsonb) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare
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
 u:=build_editor.exigir_usuario_v1();
 if jsonb_typeof(p_entrada)<>'object' or octet_length(p_entrada::text)>16000 then raise exception 'Entrada inválida.'; end if;
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
 if jsonb_typeof(bars)<>'object' or jsonb_typeof(skills)<>'array' or jsonb_array_length(skills)>5
 or jsonb_typeof(impetos)<>'object' or jsonb_typeof(condicoes)<>'object' then raise exception 'Distribuição ou escolhas inválidas.'; end if;
 if (select count(*) from jsonb_object_keys(bars))<>10 then raise exception 'Informe exatamente as dez barras.'; end if;
 if exists(select 1 from jsonb_object_keys(bars) k where not exists(select 1 from clube_novo.otimizador_barra_atributo where barra=k)) then raise exception 'Barra desconhecida.'; end if;
 for r in select b.barra,min(ca.valor) minimo,count(*) quantidade from clube_novo.otimizador_barra_atributo b
 left join clube_novo.carta_atributo_jogo ca on ca.codigo_atributo=b.codigo_atributo and ca.card_id=cid group by b.barra loop
   if r.minimo is null or jsonb_typeof(bars->r.barra)<>'number' or (bars->>r.barra)!~'^[0-9]+$' then raise exception 'Barra inválida: %',r.barra; end if;
   n:=(bars->>r.barra)::integer; limite:=greatest(0,least(25,99-r.minimo));
   if card.orcamento=0 then limite:=0; end if;
   if n>limite then raise exception 'Limite da barra %: %.',r.barra,limite; end if;
   maximos:=maximos||jsonb_build_object(r.barra,limite);
   if n>0 then select acumulado into barpoints from clube_novo.otimizador_custo_nivel where nivel=n;
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
      and (pos=0 or not h.so_goleiro) and (pos<>0 or not h.so_de_linha)) then raise exception 'Habilidade não adicionável: %.',codigo; end if;
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
 if exists(select 1 from jsonb_object_keys(impetos) k where not exists(select 1 from clube_novo.carta_impeto_jogo where card_id=cid and slot=k::integer and vaga and codigo_impeto is null)) then raise exception 'Ímpeto nativo não pode ser substituído.'; end if;
 if exists(select 1 from jsonb_object_keys(condicoes) k where not exists(select 1 from clube_novo.carta_impeto_jogo where card_id=cid and slot=k::integer and condicional)) then raise exception 'Condição de ímpeto inválida.'; end if;
 for slot in select ci.* from clube_novo.carta_impeto_jogo ci where ci.card_id=cid order by ci.slot loop
   codigo:=slot.codigo_impeto; nivel:=null;
   if slot.vaga and codigo is null then
     codigo:=nullif(impetos->>slot.slot::text,'')::integer;
     if codigo is not null and codigo not in (select c.codigo from build_editor.adicionais_v1(pos) c) then raise exception 'Ímpeto adicional não permitido.'; end if;
   end if;
   if codigo is null then continue; end if;
   if not exists(select 1 from clube_novo.impeto_jogo i where i.codigo_jogo=codigo and pode_rodar) then raise exception 'Ímpeto não confirmado.'; end if;
   if slot.condicional then
     select coalesce((select efeito_maximo::integer from clube_novo.impeto_condicao_parametro_faixa_jogo where codigo_impeto=codigo),max(delta)) into limite from clube_novo.impeto_atributo_jogo where codigo_impeto=codigo;
     nivel:=coalesce((condicoes->>slot.slot::text)::integer,limite);
     if limite is null or nivel<0 or nivel>limite then raise exception 'Nível condicional inválido.'; end if;
   end if;
   contador:=0;
   for a in select codigo_atributo,delta from clube_novo.impeto_atributo_jogo where codigo_impeto=codigo loop
     contador:=contador+1;
     if a.delta is null then raise exception 'Efeito de ímpeto não confirmado.'; end if;
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
   attrs:=attrs||jsonb_build_array(jsonb_build_object('codigo',r.codigo_atributo,'nome',r.nome_pt,'indice',r.indice_otimizador,'base',r.valor,'referencia',v->'referencia','final',v->'jogo'));
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
 select case when bs.slot='ofensivo' then 1 else 2 end into primary_slot from clube_novo.bonificador_posicao_slot bs where bs.posicao_id=pos;
 if primary_slot is null then raise exception 'Prioridade dos estilos não confirmada.'; end if;
 select nullif(playstyle_id,0) into main_style from clube_novo.carta_playstyle_jogo where card_id=cid and slot_fisico=primary_slot;
 select nullif(playstyle_id,0) into other_style from clube_novo.carta_playstyle_jogo where card_id=cid and slot_fisico=3-primary_slot;
 if main_style is null then main_style:=other_style; other_style:=null; end if;
 if exists(select 1 from clube_novo.bonificador_regra_playstyle where playstyle_id=main_style and posicao_id=pos and funcao_id=fid and da_bonus) then style_bonus:=(par->>'estilo_ativo')::numeric; end if;
 if exists(select 1 from clube_novo.bonificador_regra_playstyle where playstyle_id=other_style and posicao_id=pos and da_bonus) then style_bonus:=style_bonus+(par->>'estilo_ativo_secundario')::numeric; end if;
 total:=numerator/denominator*100+body_bonus+foot_bonus+ia_bonus+style_bonus;
 if total is null then raise exception 'Parcela da nota não confirmada.'; end if;
 return jsonb_build_object('motor','editor-independente-v1','card_id',cid,'nota_final',total,'atributos',attrs,
   'pontos',jsonb_build_object('total',card.orcamento,'gastos',cost,'restantes',card.orcamento-cost),'limites_barras',maximos,'impetos',equipped);
end $$;

create function build_editor.salvar_v1(p_entrada jsonb,p_nome text,p_pedido_id uuid,p_id uuid default null,p_revisao integer default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u uuid; resultado jsonb; saved build_editor.build_pessoal%rowtype;
begin
 u:=build_editor.exigir_usuario_v1();
 if p_pedido_id is null or p_nome is null or length(btrim(p_nome)) not between 1 and 80 then raise exception 'Informe um nome de até 80 caracteres.'; end if;
 -- O mesmo pedido pode ser repetido após perda de rede sem duplicar a gravação.
 perform pg_advisory_xact_lock(hashtextextended(u::text||p_pedido_id::text,0));
 select * into saved from build_editor.build_pessoal where usuario_id=u and pedido_id=p_pedido_id;
 if found then
   if saved.entrada<>p_entrada or saved.nome<>btrim(p_nome) or (p_id is not null and p_id<>saved.id) then raise exception 'Identificador de envio já usado para outro conteúdo.'; end if;
   return to_jsonb(saved)-'usuario_id'-'pedido_id';
 end if;
 if p_id is not null then
   select * into saved from build_editor.build_pessoal where id=p_id and usuario_id=u for update;
   if not found then raise exception using errcode='42501',message='Build pessoal não encontrada. Não é permitido sobrescrever builds de outro usuário ou do sistema.'; end if;
   if p_revisao is null or saved.revisao<>p_revisao then raise exception using errcode='40001',message='Esta build foi alterada em outra sessão. Reabra a versão atual ou salve uma cópia.'; end if;
 end if;
 resultado:=build_editor.avaliar_v1(p_entrada);
 if p_id is null then
   insert into build_editor.build_pessoal(usuario_id,card_id,nome,pedido_id,entrada,resultado,motor_versao)
   values(u,p_entrada->>'card_id',btrim(p_nome),p_pedido_id,p_entrada,resultado,resultado->>'motor') returning * into saved;
 else
   update build_editor.build_pessoal set nome=btrim(p_nome),pedido_id=p_pedido_id,entrada=p_entrada,resultado=resultado,
     motor_versao=resultado->>'motor',revisao=revisao+1,atualizado_em=now()
   where id=p_id and usuario_id=u returning * into saved;
 end if;
 return to_jsonb(saved)-'usuario_id'-'pedido_id';
end $$;

create function build_editor.listar_v1(p_card_id text) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare u uuid; result jsonb;
begin
 u:=build_editor.exigir_usuario_v1();
 select coalesce(jsonb_agg(to_jsonb(b)-'usuario_id'-'pedido_id' order by atualizado_em desc,id),'[]') into result
 from build_editor.build_pessoal b where usuario_id=u and card_id=p_card_id;
 return result;
end $$;

create function build_editor.catalogo_v1(p_card_id text,p_posicao_id integer) returns jsonb
language plpgsql stable security definer set search_path='' as $$
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
     from clube_novo.habilidade_jogo h where h.tipo='comum' and (p_posicao_id=0 or not h.so_goleiro) and (p_posicao_id<>0 or not h.so_de_linha)
     and not exists(select 1 from clube_novo.carta_habilidade_jogo ch where ch.card_id=p_card_id and ch.skill_id=h.skill_id)),
  'tecnicos',(select coalesce(jsonb_agg(jsonb_build_object('id',t.id::text,'nome',t.nome_en,'proficiencia',(select max(proficiencia) from clube_novo.tecnico_estilo_jogo where tecnico_id=t.id and confirmado)) order by t.nome_en),'[]')
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
end $$;

-- API sem fórmulas: apenas decisões do usuário, atributos visíveis e resultado.
create function public.site_novo_editor_catalogo_v1(p_card_id text,p_posicao_id integer) returns jsonb language sql security invoker set search_path='' as $$select build_editor.catalogo_v1(p_card_id,p_posicao_id)$$;
create function public.site_novo_editor_avaliar_v1(p_entrada jsonb) returns jsonb language sql security invoker set search_path='' as $$select build_editor.avaliar_v1(p_entrada)$$;
create function public.site_novo_editor_salvar_v1(p_entrada jsonb,p_nome text,p_pedido_id uuid,p_id uuid default null,p_revisao integer default null) returns jsonb language sql security invoker set search_path='' as $$select build_editor.salvar_v1(p_entrada,p_nome,p_pedido_id,p_id,p_revisao)$$;
create function public.site_novo_editor_listar_v1(p_card_id text) returns jsonb language sql security invoker set search_path='' as $$select build_editor.listar_v1(p_card_id)$$;
revoke all on all functions in schema build_editor from public,anon,authenticated;
grant execute on function build_editor.avaliar_v1(jsonb),build_editor.salvar_v1(jsonb,text,uuid,uuid,integer),build_editor.listar_v1(text) to authenticated;
grant execute on function build_editor.catalogo_v1(text,integer) to authenticated;
revoke all on function public.site_novo_editor_catalogo_v1(text,integer) from public,anon;
grant execute on function public.site_novo_editor_catalogo_v1(text,integer) to authenticated;
revoke all on function public.site_novo_editor_avaliar_v1(jsonb),public.site_novo_editor_salvar_v1(jsonb,text,uuid,uuid,integer),public.site_novo_editor_listar_v1(text) from public,anon;
grant execute on function public.site_novo_editor_avaliar_v1(jsonb),public.site_novo_editor_salvar_v1(jsonb,text,uuid,uuid,integer),public.site_novo_editor_listar_v1(text) to authenticated;
commit;
