begin;

-- O Coach.bin já entrega o índice canônico do atributo (valor físico - 1).
-- A carga anterior resolveu esse índice por atributo_jogo.idx_casa, que não é
-- a ordem dos 26 atributos consumida pelo Otimizador. A correção muda somente
-- o endereço FK: indice físico -> atributo_ordem_otimizador -> codigo_atributo.

create temporary table tecnico_boost_v1 on commit drop as
select ta.tecnico_id,ta.ordem,o.codigo_atributo,ta.delta,ta.fonte,ta.cpk_origem,
       ta.arquivo,ta.registro,ta.bit,ta.largura,ta.hash_coach_bin,ta.confirmado,
       ta.carregado_em
from clube_novo.tecnico_atributo_jogo ta
join clube_novo.atributo_jogo a on a.codigo=ta.codigo_atributo
join clube_novo.atributo_ordem_otimizador o on o.indice_otimizador=a.idx_casa;

do $$
begin
  if (select count(*) from tecnico_boost_v1) <> 104
     or (select count(distinct (tecnico_id,ordem)) from tecnico_boost_v1) <> 104
     or exists(select 1 from tecnico_boost_v1 where delta<>1)
     or (select array_agg(codigo_atributo order by ordem) from tecnico_boost_v1
         where tecnico_id=17601312850052)
        <> array['PB:530:6','PB:434:6']::text[]
     or (select array_agg(codigo_atributo order by ordem) from tecnico_boost_v1
         where tecnico_id=17609097478250)
        <> array['PB:434:6','PB:408:6']::text[] then
    raise exception 'pré-voo dos 104 boosts físicos não fecha Capello/Conte';
  end if;
end $$;

delete from clube_novo.tecnico_atributo_jogo;
insert into clube_novo.tecnico_atributo_jogo(
  tecnico_id,ordem,codigo_atributo,delta,fonte,cpk_origem,arquivo,registro,bit,
  largura,hash_coach_bin,confirmado,carregado_em)
select tecnico_id,ordem,codigo_atributo,delta,fonte,cpk_origem,arquivo,registro,bit,
       largura,hash_coach_bin,confirmado,carregado_em
from tecnico_boost_v1;

do $$
begin
  if (select count(*) from clube_novo.tecnico_atributo_jogo) <> 104
     or exists(
       select 1 from clube_novo.tecnico_atributo_jogo ta
       left join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=ta.codigo_atributo
       where o.codigo_atributo is null)
     or (select array_agg(o.indice_otimizador order by ta.ordem)
         from clube_novo.tecnico_atributo_jogo ta
         join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=ta.codigo_atributo
         where ta.tecnico_id=17601312850052) <> array[6,10]::smallint[]
     or (select array_agg(o.indice_otimizador order by ta.ordem)
         from clube_novo.tecnico_atributo_jogo ta
         join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=ta.codigo_atributo
         where ta.tecnico_id=17609097478250) <> array[10,13]::smallint[] then
    raise exception 'readback dos boosts canônicos falhou';
  end if;
end $$;

commit;
