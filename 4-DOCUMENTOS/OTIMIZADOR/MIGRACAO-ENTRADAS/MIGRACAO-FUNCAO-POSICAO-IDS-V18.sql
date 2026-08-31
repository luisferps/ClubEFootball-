-- V18 — Relação canônica função -> posição para o Otimizador.
--
-- Não altera os 19 moldes, pesos, alvos, ordem, fórmula ou os textos legados.
-- Materializa somente a tradução já comprovada de 30 pares de código para IDs
-- canônicos e troca a fábrica de filas para consultar a relação por FK.

begin;

create table if not exists clube_novo.otimizador_funcao_posicao (
  funcao_id bigint not null,
  posicao_id integer not null,
  ordem smallint not null check (ordem between 1 and 12),
  primary key (funcao_id,posicao_id),
  unique (funcao_id,ordem),
  constraint otimizador_funcao_posicao_funcao_fk
    foreign key (funcao_id) references clube_novo.funcao_sistema(id)
    on update restrict on delete restrict,
  constraint otimizador_funcao_posicao_posicao_fk
    foreign key (posicao_id) references clube_novo.posicao_jogo(id)
    on update restrict on delete restrict
);
alter table clube_novo.otimizador_funcao_posicao enable row level security;
revoke all on table clube_novo.otimizador_funcao_posicao from public, anon, authenticated;

do $v18_pares$
declare
  v_origem integer;
  v_relacao integer;
begin
  if exists (
    select 1
    from clube_novo.funcao_sistema fs
    cross join lateral unnest(fs.posicoes) with ordinality u(codigo_pt,ordem)
    left join clube_novo.posicao_jogo p on p.codigo_pt=u.codigo_pt
    where fs.ativa and (p.id is null or not p.pode_rodar)
  ) then
    raise exception 'V18 recusada: existe posição de função sem ID canônico apto';
  end if;
  if exists (
    select 1
    from clube_novo.funcao_sistema fs
    cross join lateral unnest(fs.posicoes) with ordinality u(codigo_pt,ordem)
    join clube_novo.posicao_jogo p on p.codigo_pt=u.codigo_pt
    where fs.ativa
    group by fs.id,u.codigo_pt
    having count(*)<>1
  ) then
    raise exception 'V18 recusada: tradução função/posição ambígua';
  end if;

  insert into clube_novo.otimizador_funcao_posicao(funcao_id,posicao_id,ordem)
  select fs.id,p.id,u.ordem::smallint
  from clube_novo.funcao_sistema fs
  cross join lateral unnest(fs.posicoes) with ordinality u(codigo_pt,ordem)
  join clube_novo.posicao_jogo p on p.codigo_pt=u.codigo_pt
  where fs.ativa
  on conflict (funcao_id,posicao_id) do nothing;

  select count(*) into v_origem
  from clube_novo.funcao_sistema fs
  cross join lateral unnest(fs.posicoes) with ordinality u(codigo_pt,ordem)
  where fs.ativa;
  select count(*) into v_relacao from clube_novo.otimizador_funcao_posicao;
  if v_origem<>30 or v_relacao<>v_origem then
    raise exception 'V18 recusada: esperados 30 pares, origem=% relação=%',v_origem,v_relacao;
  end if;
end
$v18_pares$;

do $v18_consumidor$
declare
  r record;
  definicao text;
  antigo constant text := 'p.codigo_pt=any(fs.posicoes)';
  novo constant text := 'exists(select 1 from clube_novo.otimizador_funcao_posicao fp where fp.funcao_id=fs.id and fp.posicao_id=p.id)';
begin
  for r in
    select v.oid
    from (values
      ('public.otimizador_criar_amostra_teste_v3(uuid,text,text,text,text)'::regprocedure),
      ('public.otimizador_criar_amostra_controlada_50_v2(uuid,text,text,text,text,jsonb)'::regprocedure),
      ('public.otimizador_criar_fila_comparacao_legado_50_v1(uuid,text,text,text,text)'::regprocedure)
    ) as v(oid)
  loop
    select pg_get_functiondef(r.oid) into definicao;
    if position(antigo in definicao)=0 then
      raise exception 'V18 recusada: fábrica % ainda não contém a chamada textual esperada',r.oid::regprocedure;
    end if;
    execute replace(definicao,antigo,novo);
  end loop;
end
$v18_consumidor$;

revoke all on function public.otimizador_criar_amostra_teste_v3(uuid,text,text,text,text)
  from public, anon, authenticated;
revoke all on function public.otimizador_criar_amostra_controlada_50_v2(uuid,text,text,text,text,jsonb)
  from public, anon, authenticated;
revoke all on function public.otimizador_criar_fila_comparacao_legado_50_v1(uuid,text,text,text,text)
  from public, anon, authenticated;
grant execute on function public.otimizador_criar_amostra_teste_v3(uuid,text,text,text,text) to service_role;
grant execute on function public.otimizador_criar_amostra_controlada_50_v2(uuid,text,text,text,text,jsonb) to service_role;
grant execute on function public.otimizador_criar_fila_comparacao_legado_50_v1(uuid,text,text,text,text) to service_role;

commit;
