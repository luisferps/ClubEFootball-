-- Validação somente leitura pós-migração.
begin read only;

select count(*) as impetos from clube_novo.impeto_jogo;
select condicao_estado, count(*) from clube_novo.impeto_jogo group by 1 order by 1;

select confirmado, count(*) as relacoes, count(distinct codigo_impeto) as impetos,
       min(delta) as delta_min, max(delta) as delta_max
from clube_novo.impeto_atributo_jogo
group by confirmado
order by confirmado desc;

select count(*) as orfaos
from clube_novo.impeto_atributo_jogo r
left join clube_novo.impeto_jogo i on i.codigo_jogo = r.codigo_impeto
left join clube_novo.atributo_jogo a on a.codigo = r.codigo_atributo
where i.codigo_jogo is null or a.codigo is null;

select count(*) as confirmadas_invalidas
from clube_novo.impeto_atributo_jogo
where confirmado and (
  delta is null or bit_delta is null or largura_delta is null
  or registro_origem is null or fonte_origem is null or endereco_origem is null
  or falta_o_que is not null
);

select codigo_impeto, codigo_atributo, ordem, delta, bit_delta,
       fonte_origem, registro_origem, endereco_origem
from clube_novo.impeto_atributo_jogo
where codigo_impeto = 30
order by ordem;

commit;

