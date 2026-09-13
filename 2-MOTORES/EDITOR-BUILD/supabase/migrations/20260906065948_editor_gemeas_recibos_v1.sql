begin;
create table build_editor.recibo(
 usuario_id uuid not null references auth.users(id) on delete cascade,
 pedido_id uuid not null,
 resposta jsonb not null,
 criado_em timestamptz not null default now(),
 primary key(usuario_id,pedido_id)
);
alter table build_editor.recibo enable row level security;
revoke all on build_editor.recibo from public,anon,authenticated;
create or replace function build_editor.salvar_v1(p_entrada jsonb,p_nome text,p_pedido_id uuid,p_id uuid default null,p_revisao integer default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u uuid; resultado jsonb; receipt jsonb; saved build_editor.build_pessoal%rowtype;
begin
 u:=build_editor.exigir_usuario_v1();
 if p_pedido_id is null or p_nome is null or length(btrim(p_nome)) not between 1 and 80 then raise exception 'Informe um nome de até 80 caracteres.'; end if;
 -- O mesmo pedido pode ser repetido após perda de rede sem duplicar a gravação.
 perform pg_advisory_xact_lock(hashtextextended(u::text||p_pedido_id::text,0));
 select resposta into receipt from build_editor.recibo where usuario_id=u and pedido_id=p_pedido_id;
 if found then
   if receipt->'entrada'<>p_entrada or receipt->>'nome'<>btrim(p_nome) or (p_id is not null and p_id::text<>receipt->>'id') then raise exception 'Identificador de envio já usado para outro conteúdo.'; end if;
   return receipt;
 end if;
 if p_id is not null then
   select * into saved from build_editor.build_pessoal where id=p_id and usuario_id=u for update;
   if not found then raise exception using errcode='42501',message='Build pessoal não encontrada. Não é permitido sobrescrever builds de outro usuário ou do sistema.'; end if;
   if saved.card_id is distinct from p_entrada->>'card_id' then raise exception 'Não é permitido mudar a carta de uma build existente.'; end if;
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
 receipt:=to_jsonb(saved)-'usuario_id'-'pedido_id';
 insert into build_editor.recibo(usuario_id,pedido_id,resposta) values(u,p_pedido_id,receipt);
 return receipt;
end $$;


create function build_editor.gemea_v1(p_entrada jsonb,p_sai integer,p_entra integer) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare antes jsonb; depois jsonb; nova jsonb; habilidades jsonb;
begin
 perform build_editor.exigir_usuario_v1();
 if p_sai=p_entra or not (p_entrada->'habilidades' @> jsonb_build_array(p_sai))
 or p_entrada->'habilidades' @> jsonb_build_array(p_entra) then raise exception 'Escolha uma habilidade presente para substituir por uma gêmea disponível.'; end if;
 if not exists(select 1 from clube_novo.habilidade_jogo a join clube_novo.habilidade_jogo b on b.skill_id=p_entra
   where a.skill_id=p_sai and a.tipo='comum' and b.tipo='comum'
   and p_entra=any(a.gemeas) and a.efeito_por_codigo=b.efeito_por_codigo) then raise exception 'Essa habilidade não pode substituir a escolhida como gêmea.'; end if;
 antes:=build_editor.avaliar_v1(p_entrada);
 select jsonb_agg(case when value::integer=p_sai then p_entra else value::integer end order by ord)
 into habilidades from jsonb_array_elements_text(p_entrada->'habilidades') with ordinality x(value,ord);
 nova:=jsonb_set(p_entrada,'{habilidades}',habilidades);
 depois:=build_editor.avaliar_v1(nova);
 if antes->'nota_final'<>depois->'nota_final' or antes->'atributos'<>depois->'atributos' then raise exception 'A troca alteraria a avaliação; não é uma substituição equivalente.'; end if;
 return jsonb_build_object('entrada',nova,'resultado',depois);
end $$;
revoke all on function build_editor.gemea_v1(jsonb,integer,integer) from public,anon;
grant execute on function build_editor.gemea_v1(jsonb,integer,integer) to authenticated;
create function public.site_novo_editor_gemea_v1(p_entrada jsonb,p_sai integer,p_entra integer) returns jsonb
language sql security invoker set search_path='' as $$select build_editor.gemea_v1(p_entrada,p_sai,p_entra)$$;
revoke all on function public.site_novo_editor_gemea_v1(jsonb,integer,integer) from public,anon;
grant execute on function public.site_novo_editor_gemea_v1(jsonb,integer,integer) to authenticated;
commit;
