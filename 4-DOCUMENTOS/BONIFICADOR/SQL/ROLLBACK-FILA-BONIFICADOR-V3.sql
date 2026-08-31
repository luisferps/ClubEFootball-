-- Recuperação da fila V3. Só é válida antes de qualquer resultado Bonificador V3.
begin;
do $guard$
begin
  if exists (select 1 from clube_novo.build_linha_card where build_bonificador_id is not null) then
    raise exception 'rollback recusado: há resultado Bonificador; não apagar histórico automaticamente';
  end if;
end $guard$;
drop function if exists public.bonificador_contexto_fila_v3(integer,integer);
delete from clube_novo.bonificador_par;
commit;
