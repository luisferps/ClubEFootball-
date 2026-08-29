begin;

-- Reconstitui exatamente a projeção anterior: o índice físico era resolvido
-- por atributo_jogo.idx_casa. Metadados e proveniência permanecem intocados.
create temporary table tecnico_boost_rollback_v1 on commit drop as
select ta.tecnico_id,ta.ordem,a.codigo codigo_atributo,ta.delta,ta.fonte,
       ta.cpk_origem,ta.arquivo,ta.registro,ta.bit,ta.largura,ta.hash_coach_bin,
       ta.confirmado,ta.carregado_em
from clube_novo.tecnico_atributo_jogo ta
join clube_novo.atributo_ordem_otimizador o on o.codigo_atributo=ta.codigo_atributo
join clube_novo.atributo_jogo a on a.idx_casa=o.indice_otimizador;

do $$ begin
  if (select count(*) from tecnico_boost_rollback_v1)<>104 then
    raise exception 'rollback não reconstruiu 104 relações';
  end if;
end $$;

delete from clube_novo.tecnico_atributo_jogo;
insert into clube_novo.tecnico_atributo_jogo(
  tecnico_id,ordem,codigo_atributo,delta,fonte,cpk_origem,arquivo,registro,bit,
  largura,hash_coach_bin,confirmado,carregado_em)
select tecnico_id,ordem,codigo_atributo,delta,fonte,cpk_origem,arquivo,registro,bit,
       largura,hash_coach_bin,confirmado,carregado_em
from tecnico_boost_rollback_v1;

commit;
