begin;

drop trigger if exists build_linha_publicavel_gate_v3 on clube_novo.build_linha_card;
drop function if exists clube_novo.validar_build_linha_publicavel_v3();
drop table if exists clube_novo.build_linha_card;
drop table if exists clube_novo.build_bonificador;
drop table if exists clube_novo.build_otimizador;

-- Este rollback retorna ao estado seguro sem destino de Build.
-- O desenho V2 foi revogado e não deve ser restaurado como runtime.

commit;
