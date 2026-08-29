begin;

-- Pré-condições: identidade e endereço físico já materializados no modelo novo.
do $$
begin
  if not exists (select 1 from clube_novo.habilidade_jogo where skill_id=17 and bit_na_carta=676)
     or not exists (select 1 from clube_novo.habilidade_jogo where skill_id=33 and bit_na_carta=610) then
    raise exception 'ponte fisica skill_id -> bit nao confere para 17/33';
  end if;
  if (select count(distinct skill_id) from clube_novo.carta_habilidade_jogo) <> 65 then
    raise exception 'cardinalidade de skill_id usados mudou';
  end if;
end $$;

-- Corrige a projeção que separou skill_id e efeito em duas linhas legadas.
update clube_novo.habilidade_jogo
set efeito = '{"6":{"pct":2},"9":{"pct":3}}'::jsonb,
    efeito_por_codigo = '{"PB:530:6":{"pct":2},"PB:428:6":{"pct":3}}'::jsonb,
    efeito_legivel = 'Finalização +2% · Curva +3%',
    fabricavel = true,
    efeito_desconhecido = false,
    pode_rodar = true,
    falta_o_que = null,
    extras = coalesce(extras,'{}'::jsonb) || jsonb_build_object(
      'efeito_origem','contrato operacional anterior traduzido por skill_id 17 + bit 676',
      'efeito_chave_nova','codigo fisico do atributo')
where skill_id=17 and bit_na_carta=676;

update clube_novo.habilidade_jogo
set efeito = '{"5":{"pct":4},"9":{"pct":1}}'::jsonb,
    efeito_por_codigo = '{"PB:448:6":{"pct":4},"PB:428:6":{"pct":1}}'::jsonb,
    efeito_legivel = 'Passe alto +4% · Curva +1%',
    fabricavel = true,
    efeito_desconhecido = false,
    pode_rodar = true,
    falta_o_que = null,
    extras = coalesce(extras,'{}'::jsonb) || jsonb_build_object(
      'efeito_origem','contrato operacional anterior traduzido por skill_id 33 + bit 610',
      'efeito_chave_nova','codigo fisico do atributo')
where skill_id=33 and bit_na_carta=610;

create table clube_novo.habilidade_funcao_bloqueio_otimizador (
  skill_id integer not null references clube_novo.habilidade_jogo(skill_id),
  funcao_id bigint not null references clube_novo.funcao_sistema(id),
  origem text not null,
  carregado_em timestamptz not null default transaction_timestamp(),
  primary key (skill_id,funcao_id)
);

create table clube_novo.habilidade_funcao_incidencia_otimizador (
  skill_id integer not null references clube_novo.habilidade_jogo(skill_id),
  funcao_id bigint not null references clube_novo.funcao_sistema(id),
  incidencia_pct numeric(5,2) not null check (incidencia_pct between 0 and 100),
  origem text not null,
  carregado_em timestamptz not null default transaction_timestamp(),
  primary key (skill_id,funcao_id)
);

-- Tradução histórica isolada. O resultado persistido não contém nome como chave.
insert into clube_novo.habilidade_funcao_bloqueio_otimizador
  (skill_id,funcao_id,origem)
select distinct nh.skill_id,fs.id,
       'clube.bloqueio traduzido por nome_antigo -> bit fisico -> skill_id'
from clube.bloqueio b
join clube.habilidade oh on oh.nome_antigo=b.habilidade_nome
join clube_novo.habilidade_jogo nh on nh.bit_na_carta=oh.bit
join clube_novo.funcao_sistema fs on fs.codigo_legado=b.funcao_codigo;

with traduzida as (
  select nh.skill_id,coalesce(fs.id,fa.id_funcao) funcao_id,
         i.incidencia_pct
  from clube.habilidade_incidencia i
  join clube.habilidade oh on oh.nome_antigo=i.habilidade
  join clube_novo.habilidade_jogo nh on nh.bit_na_carta=oh.bit
  left join clube_novo.funcao_sistema fs
    on fs.rotulo=i.funcao_rotulo or fs.nome_legado=i.funcao_rotulo
  left join clube_novo.funcao_alias fa
    on fa.ativo and fa.nome_alias=i.funcao_rotulo
), canonica as (
  select skill_id,funcao_id,min(incidencia_pct) incidencia_pct,
         count(distinct incidencia_pct) valores_distintos
  from traduzida where funcao_id is not null
  group by skill_id,funcao_id
)
insert into clube_novo.habilidade_funcao_incidencia_otimizador
  (skill_id,funcao_id,incidencia_pct,origem)
select skill_id,funcao_id,incidencia_pct,
       'clube.habilidade_incidencia traduzida por bit fisico e funcao_id'
from canonica where valores_distintos=1;

do $$
begin
  if (select count(*) from clube_novo.habilidade_funcao_bloqueio_otimizador) <> 246 then
    raise exception 'bloqueio normalizado nao fechou 246 relacoes';
  end if;
  if (select count(*) from clube_novo.habilidade_funcao_incidencia_otimizador) <> 711 then
    raise exception 'incidencia normalizada nao fechou 711 relacoes canonicas';
  end if;
  if exists (
    select 1 from clube_novo.carta_habilidade_jogo ch
    join clube_novo.habilidade_jogo h using(skill_id)
    where not h.pode_rodar
  ) then
    raise exception 'ainda existe skill_id usado por carta com pode_rodar=false';
  end if;
  if (select count(*) from clube_novo.habilidade_jogo where not pode_rodar) <> 7 then
    raise exception 'esperadas exatamente 7 habilidades novas sem endereco na carta';
  end if;
end $$;

revoke all on table clube_novo.habilidade_funcao_bloqueio_otimizador from public,anon,authenticated;
revoke all on table clube_novo.habilidade_funcao_incidencia_otimizador from public,anon,authenticated;
grant usage on schema clube_novo to service_role;
grant select on table clube_novo.habilidade_funcao_bloqueio_otimizador to service_role;
grant select on table clube_novo.habilidade_funcao_incidencia_otimizador to service_role;

commit;

