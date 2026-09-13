create table if not exists clube_novo.bonificador_altura_politica_v1 (
 versao text primary key, estado text not null check(estado in('preparada','ativa')),
 regra jsonb not null, criado_em timestamptz not null default now()
);
alter table clube_novo.bonificador_altura_politica_v1 enable row level security;
revoke all on clube_novo.bonificador_altura_politica_v1 from public,anon,authenticated;
grant select on clube_novo.bonificador_altura_politica_v1 to service_role;
insert into clube_novo.bonificador_altura_politica_v1(versao,estado,regra)
values('altura-independente-20260909-v1','preparada',jsonb_build_object(
 'funcoes_ativas',jsonb_build_array(1,4,5,6,17,18,19),'peso',5,
 'direcao',1,'demais_funcoes',0,'inversoes_base',jsonb_build_array(4,6),
 'faixas_goleiros',jsonb_build_array(179,184,189,194),
 'faixas_linha',jsonb_build_array(171,178,184,191),
 'demais_parcelas','preservacao exata; nenhum denominador recalculado',
 'normalizacao','inalterada','ia','decisao de implantacao separada',
 'molde_base',(select jsonb_agg(to_jsonb(m) order by funcao_id,corpo_pos) from clube_novo.bonificador_molde_corpo m)))
on conflict(versao) do nothing;

create or replace function clube_novo.separar_altura_v1(p_detalhe jsonb,p_funcao bigint,p_aplicar boolean default false)
returns jsonb language plpgsql immutable set search_path='' as $$
declare a numeric;n numeric;o numeric;d jsonb;
begin
 if p_funcao is null or p_funcao not between 1 and 19 or p_aplicar is null
  or jsonb_typeof(p_detalhe) is distinct from 'object' then raise exception 'Entrada de altura inválida'; end if;
 if (select count(*) from jsonb_each(p_detalhe))<>12 or not p_detalhe?'altura'
  or exists(select 1 from jsonb_each(p_detalhe)e where jsonb_typeof(e.value)<>'number') then
  raise exception 'Detalhe físico completo com 12 parcelas é obrigatório'; end if;
 a:=(p_detalhe->>'altura')::numeric;
 n:=case when not p_aplicar then a when p_funcao in(4,6) then -a
  when p_funcao in(1,5,17,18,19) then a else 0 end;
 select sum(value::text::numeric) into o from jsonb_each(p_detalhe) where key<>'altura';
 d:=jsonb_set(p_detalhe,'{altura}',to_jsonb(n));
 return jsonb_build_object('politica','altura-independente-20260909-v1',
 'altura_anterior',a,'altura',n,'restante_corpo',o,'total',o+n,'detalhe',d,'delta',n-a);
end $$;
revoke all on function clube_novo.separar_altura_v1(jsonb,bigint,boolean) from public,anon,authenticated;
grant execute on function clube_novo.separar_altura_v1(jsonb,bigint,boolean) to service_role;
comment on table clube_novo.bonificador_altura_politica_v1 is 'Regra aprovada de altura independente. Estado preparada não ativa motores nem altera notas.';
