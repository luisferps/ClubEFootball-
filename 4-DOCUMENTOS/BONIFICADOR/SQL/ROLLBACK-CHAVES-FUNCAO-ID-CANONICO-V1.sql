-- Recupera as RPCs imediatamente anteriores à troca de chave textual -> ID.
begin;
drop function public.bonificador_pares_v1(integer,integer);
do $rollback$
declare d text;
begin
  for d in
    select definicao from clube_novo.bonificador_migracao_snapshot_v2
    order by case when chave like 'funcao:bonificador_regua_v1%' then 1 else 2 end
  loop execute d; end loop;
end
$rollback$;
drop table clube_novo.bonificador_migracao_snapshot_v2;
commit;
