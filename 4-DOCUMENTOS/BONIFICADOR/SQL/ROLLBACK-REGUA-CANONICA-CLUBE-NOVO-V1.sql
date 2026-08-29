-- Recupera exatamente as três RPCs do snapshot persistido pela migração.
begin;
do $rollback$
declare d text;
begin
  for d in
    select definicao from clube_novo.bonificador_migracao_snapshot_v1
    where chave like 'funcao:%'
    order by case when chave like 'funcao:bonificador_regua_v1%' then 1 when chave like 'funcao:bonificador_carta_v1%' then 2 else 3 end
  loop execute d; end loop;
end
$rollback$;
drop table clube_novo.bonificador_par;
drop table clube_novo.bonificador_regra_playstyle;
drop table clube_novo.bonificador_posicao_slot;
drop table clube_novo.bonificador_molde_corpo;
drop table clube_novo.bonificador_parametro;
drop table clube_novo.bonificador_migracao_snapshot_v1;
alter table clube_novo.corpo_ordem drop constraint corpo_ordem_pos_key;
commit;
