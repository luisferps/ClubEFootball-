begin;

-- Esta é a única camada que traduz valores históricos. Os consumidores não
-- leem nem comparam os rótulos/valores brutos usados nos INSERTs abaixo.
do $$
begin
  if (select count(*) from clube_novo.carta_jogo) <> 43072 then
    raise exception 'cardinalidade de carta_jogo mudou';
  end if;
  if exists (
    select 1 from clube_novo.carta_jogo c
    left join clube_novo.posicao_jogo p on p.codigo_en=c.posicao
    where p.id is null or not p.pode_rodar
  ) then
    raise exception 'posição principal sem identidade apta';
  end if;
  if exists (
    select c.card_id from clube_novo.carta_jogo c
    join clube_novo.posicao_jogo p on p.codigo_en=c.posicao
    group by c.card_id having count(*) <> 1
  ) then
    raise exception 'posição principal ambígua';
  end if;
  if (select array_agg(pe order by pe) from (select distinct pe from clube_novo.carta_jogo) x)
     is distinct from array['Direito','Esquerdo']::text[] then
    raise exception 'vocabulário histórico de pé dominante mudou';
  end if;
  if exists (
    select 1 from clube_novo.carta_jogo c
    left join clube_novo.pe u on u.campo='pe_ruim_uso' and u.valor=c.pe_ruim_uso
    left join clube_novo.pe p on p.campo='pe_ruim_precisao' and p.valor=c.pe_ruim_precisao
    where u.valor is null or p.valor is null or not u.pode_rodar or not p.pode_rodar
  ) then
    raise exception 'pé ruim sem identidade composta apta';
  end if;
  if exists (
    select 1 from clube_novo.carta_jogo c
    left join clube_novo.playstyle p
      on p.bit=c.slot_ofensivo_id and p.slot in ('ofensivo','ambos')
    where p.id_jogo is null or not p.pode_rodar
  ) then
    raise exception 'playstyle ofensivo sem identidade apta';
  end if;
  if exists (
    select 1 from clube_novo.carta_jogo c
    left join clube_novo.playstyle p
      on p.indice=c.slot_defensivo_id and p.slot in ('defensivo','ambos')
    where p.id_jogo is null or not p.pode_rodar
  ) then
    raise exception 'playstyle defensivo sem identidade apta';
  end if;
end $$;

create table clube_novo.carta_posicao_principal_jogo (
  card_id text primary key references clube_novo.carta_jogo(card_id) on delete cascade,
  posicao_id integer not null references clube_novo.posicao_jogo(id)
);

insert into clube_novo.carta_posicao_principal_jogo(card_id,posicao_id)
select c.card_id,p.id
from clube_novo.carta_jogo c
join clube_novo.posicao_jogo p on p.codigo_en=c.posicao;

create table clube_novo.carta_pe_jogo (
  card_id text not null references clube_novo.carta_jogo(card_id) on delete cascade,
  campo text not null,
  valor integer not null,
  primary key(card_id,campo),
  foreign key(campo,valor) references clube_novo.pe(campo,valor),
  check (campo in ('pe_dominante','pe_ruim_uso','pe_ruim_precisao'))
);

insert into clube_novo.carta_pe_jogo(card_id,campo,valor)
select card_id,'pe_dominante',case pe when 'Direito' then 0 when 'Esquerdo' then 1 end
from clube_novo.carta_jogo
union all
select card_id,'pe_ruim_uso',pe_ruim_uso from clube_novo.carta_jogo
union all
select card_id,'pe_ruim_precisao',pe_ruim_precisao from clube_novo.carta_jogo;

create table clube_novo.carta_playstyle_jogo (
  card_id text not null references clube_novo.carta_jogo(card_id) on delete cascade,
  slot_fisico smallint not null check (slot_fisico in (1,2)),
  playstyle_id integer not null references clube_novo.playstyle(id_jogo),
  valor_raw integer not null,
  primary key(card_id,slot_fisico)
);

insert into clube_novo.carta_playstyle_jogo(card_id,slot_fisico,playstyle_id,valor_raw)
select c.card_id,1,p.id_jogo,c.slot_ofensivo_id
from clube_novo.carta_jogo c
join clube_novo.playstyle p
  on p.bit=c.slot_ofensivo_id and p.slot in ('ofensivo','ambos')
union all
select c.card_id,2,p.id_jogo,c.slot_defensivo_id
from clube_novo.carta_jogo c
join clube_novo.playstyle p
  on p.indice=c.slot_defensivo_id and p.slot in ('defensivo','ambos');

do $$
begin
  if (select count(*) from clube_novo.carta_posicao_principal_jogo) <> 43072 then
    raise exception 'readback posição principal incompleto';
  end if;
  if (select count(*) from clube_novo.carta_pe_jogo) <> 129216
     or exists (select 1 from clube_novo.carta_pe_jogo group by card_id having count(*) <> 3) then
    raise exception 'readback de pé incompleto';
  end if;
  if (select count(*) from clube_novo.carta_playstyle_jogo) <> 86144
     or exists (select 1 from clube_novo.carta_playstyle_jogo group by card_id having count(*) <> 2) then
    raise exception 'readback de playstyle incompleto';
  end if;
end $$;

alter table clube_novo.carta_posicao_principal_jogo enable row level security;
alter table clube_novo.carta_pe_jogo enable row level security;
alter table clube_novo.carta_playstyle_jogo enable row level security;

create policy carta_posicao_principal_service_read
on clube_novo.carta_posicao_principal_jogo for select to service_role using (true);
create policy carta_pe_service_read
on clube_novo.carta_pe_jogo for select to service_role using (true);
create policy carta_playstyle_service_read
on clube_novo.carta_playstyle_jogo for select to service_role using (true);

revoke all on clube_novo.carta_posicao_principal_jogo from public, anon, authenticated;
revoke all on clube_novo.carta_pe_jogo from public, anon, authenticated;
revoke all on clube_novo.carta_playstyle_jogo from public, anon, authenticated;
grant select on clube_novo.carta_posicao_principal_jogo to service_role;
grant select on clube_novo.carta_pe_jogo to service_role;
grant select on clube_novo.carta_playstyle_jogo to service_role;

comment on table clube_novo.carta_posicao_principal_jogo is
  'Identidade canônica da posição principal; o consumidor usa posicao_id, não rótulo.';
comment on table clube_novo.carta_pe_jogo is
  'Identidades físicas de pé por FK composta (campo,valor); nomes são apresentação.';
comment on table clube_novo.carta_playstyle_jogo is
  'Playstyles canônicos por id_jogo; slot 1 vem do bit e slot 2 do índice físico.';

commit;
