begin;
create table build_editor.contador_build (
 usuario_id uuid not null references auth.users(id) on delete cascade,
 card_id text not null references clube_novo.carta_jogo(card_id),
 funcao_id integer not null references clube_novo.funcao_sistema(id),
 ultimo bigint not null check(ultimo>0),
 primary key(usuario_id,card_id,funcao_id)
);
alter table build_editor.contador_build enable row level security;
revoke all on build_editor.contador_build from public,anon,authenticated;
create policy contador_proprietario on build_editor.contador_build for select to authenticated using(usuario_id=(select auth.uid()));
alter table build_editor.build_pessoal add column funcao_base_id integer references clube_novo.funcao_sistema(id),
 add column numero bigint, add column excluido_em timestamptz;
with ranked as (
 select id,(entrada->>'funcao_id')::integer funcao,
 row_number() over(partition by usuario_id,card_id,entrada->>'funcao_id' order by criado_em,id) numero
 from build_editor.build_pessoal
)
update build_editor.build_pessoal b set funcao_base_id=r.funcao,numero=r.numero from ranked r where r.id=b.id;
insert into build_editor.contador_build select usuario_id,card_id,funcao_base_id,max(numero) from build_editor.build_pessoal group by usuario_id,card_id,funcao_base_id;
alter table build_editor.build_pessoal alter column funcao_base_id set not null,alter column numero set not null,
 add constraint build_numero_positivo check(numero>0),
 add constraint build_numero_unico unique(usuario_id,card_id,funcao_base_id,numero);
create function build_editor.numerar_v1() returns trigger language plpgsql set search_path='' as $$
begin
 if TG_OP='UPDATE' then
  if (new.usuario_id,new.card_id,new.funcao_base_id,new.numero) is distinct from (old.usuario_id,old.card_id,old.funcao_base_id,old.numero) then
   raise exception 'Identidade e número da build são permanentes.';
  end if;
 else
  new.funcao_base_id:=(new.entrada->>'funcao_id')::integer;
  insert into build_editor.contador_build as c(usuario_id,card_id,funcao_id,ultimo)
  values(new.usuario_id,new.card_id,new.funcao_base_id,1)
  on conflict(usuario_id,card_id,funcao_id) do update set ultimo=c.ultimo+1 returning ultimo into new.numero;
 end if;
 return new;
end $$;
revoke all on function build_editor.numerar_v1() from public,anon,authenticated;
create trigger build_identidade before insert or update on build_editor.build_pessoal for each row execute function build_editor.numerar_v1();

-- Projeção de leitura pessoal: somente dados canônicos e resultado já persistido.
create function build_editor.apresentar_v1(b build_editor.build_pessoal) returns jsonb language plpgsql stable set search_path='' as $$
declare v jsonb; skills jsonb; suggestions jsonb; coach jsonb; boosts jsonb; fname text;
begin
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
 'atributos_completos',true,'atributos',(select jsonb_agg(jsonb_build_object('codigo',a->>'codigo','nome',a->>'nome','indice',a->'indice','valor_base',a->'base','valor_final',a->'final','valor_pos_evolucao',a->'referencia',
   'grupo_tela',case when (a->>'indice')::int in(0,1,2,3,4,5,6,8,9) then 'ataque' when (a->>'indice')::int in(10,11,12,15,16) then 'atletismo' when (a->>'indice')::int in(7,13,14) then 'fisico' when (a->>'indice')::int between 17 and 20 then 'defesa' else 'goleiro' end) order by (a->>'indice')::integer) from jsonb_array_elements(b.resultado->'atributos') a),
 'tecnico',coach,'impetos',boosts,'habilidades_adicionadas',skills,'habilidades_sugeridas',suggestions,'habilidades_sugeridas_estado','pronto');
 return (to_jsonb(b)-'usuario_id'-'pedido_id'-'excluido_em')||jsonb_build_object('rotulo',fname||' '||b.numero,'build',v);
end $$;
revoke all on function build_editor.apresentar_v1(build_editor.build_pessoal) from public,anon,authenticated;
create or replace function build_editor.listar_v1(p_card_id text) returns jsonb language plpgsql stable security definer set search_path='' as $$
declare u uuid;
begin
 u:=build_editor.exigir_usuario_v1();
 return (select coalesce(jsonb_agg(build_editor.apresentar_v1(b) order by b.funcao_base_id,b.numero),'[]')
 from build_editor.build_pessoal b where b.usuario_id=u and b.card_id=p_card_id and b.excluido_em is null);
end $$;
create function build_editor.excluir_v1(p_id uuid,p_revisao integer) returns jsonb language plpgsql security definer set search_path='' as $$
declare u uuid; b build_editor.build_pessoal%rowtype;
begin
 u:=build_editor.exigir_usuario_v1();
 select * into b from build_editor.build_pessoal where id=p_id and usuario_id=u for update;
 if not found then raise exception using errcode='42501',message='Build pessoal não encontrada.'; end if;
 if b.excluido_em is not null then return jsonb_build_object('id',b.id,'excluida',true); end if;
 if p_revisao is null or b.revisao<>p_revisao then raise exception using errcode='40001',message='A build mudou. Reabra a versão atual antes de excluir.'; end if;
 update build_editor.build_pessoal set excluido_em=now(),atualizado_em=now(),revisao=revisao+1 where id=p_id and usuario_id=u;
 return jsonb_build_object('id',p_id,'excluida',true);
end $$;
revoke all on function build_editor.excluir_v1(uuid,integer) from public,anon;
grant execute on function build_editor.excluir_v1(uuid,integer) to authenticated;
create function public.site_novo_editor_excluir_v1(p_id uuid,p_revisao integer) returns jsonb language sql security invoker set search_path='' as $$select build_editor.excluir_v1(p_id,p_revisao)$$;
revoke all on function public.site_novo_editor_excluir_v1(uuid,integer) from public,anon;
grant execute on function public.site_novo_editor_excluir_v1(uuid,integer) to authenticated;

CREATE OR REPLACE FUNCTION build_editor.salvar_v1(p_entrada jsonb, p_nome text, p_pedido_id uuid, p_id uuid DEFAULT NULL::uuid, p_revisao integer DEFAULT NULL::integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare u uuid; v_avaliacao jsonb; receipt jsonb; saved build_editor.build_pessoal%rowtype;
begin
 u:=build_editor.exigir_usuario_v1();
 if p_pedido_id is null or p_nome is null or length(btrim(p_nome)) not between 1 and 80 then raise exception 'Informe um nome de até 80 caracteres.'; end if;
 -- O mesmo pedido pode ser repetido após perda de rede sem duplicar a gravação.
 perform pg_advisory_xact_lock(hashtextextended(u::text||p_pedido_id::text,0));
 select resposta into receipt from build_editor.recibo where usuario_id=u and pedido_id=p_pedido_id;
 if found then
   if receipt->'entrada'<>p_entrada or receipt->>'nome'<>btrim(p_nome) or (p_id is not null and p_id::text<>receipt->>'id') then raise exception 'Identificador de envio já usado para outro conteúdo.'; end if;
   if exists(select 1 from build_editor.build_pessoal where id=(receipt->>'id')::uuid and excluido_em is not null) then raise exception 'Esta build foi excluída; salve uma nova cópia.'; end if;
   return receipt;
 end if;
 if p_id is not null then
   select * into saved from build_editor.build_pessoal where id=p_id and usuario_id=u and excluido_em is null for update;
   if not found then raise exception using errcode='42501',message='Build pessoal não encontrada. Não é permitido sobrescrever builds de outro usuário ou do sistema.'; end if;
   if saved.card_id is distinct from p_entrada->>'card_id' then raise exception 'Não é permitido mudar a carta de uma build existente.'; end if;
   if saved.funcao_base_id is distinct from (p_entrada->>'funcao_id')::integer then raise exception 'Para mudar a função, use Salvar Uma Cópia.'; end if;
   if p_revisao is null or saved.revisao<>p_revisao then raise exception using errcode='40001',message='Esta build foi alterada em outra sessão. Reabra a versão atual ou salve uma cópia.'; end if;
 end if;
 v_avaliacao:=build_editor.avaliar_v1(p_entrada);
 if p_id is null then
   insert into build_editor.build_pessoal(usuario_id,card_id,nome,pedido_id,entrada,resultado,motor_versao)
   values(u,p_entrada->>'card_id',btrim(p_nome),p_pedido_id,p_entrada,v_avaliacao,v_avaliacao->>'motor') returning * into saved;
 else
   update build_editor.build_pessoal set nome=btrim(p_nome),pedido_id=p_pedido_id,entrada=p_entrada,resultado=v_avaliacao,
     motor_versao=v_avaliacao->>'motor',revisao=revisao+1,atualizado_em=now()
   where id=p_id and usuario_id=u returning * into saved;
 end if;
 receipt:=build_editor.apresentar_v1(saved);
 insert into build_editor.recibo(usuario_id,pedido_id,resposta) values(u,p_pedido_id,receipt);
 return receipt;
end $function$;
notify pgrst,'reload schema';
commit;
