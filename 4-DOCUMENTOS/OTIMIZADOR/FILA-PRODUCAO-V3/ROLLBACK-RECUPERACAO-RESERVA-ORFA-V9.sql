-- Rollback de contrato V9.
-- Não desfaz uma recuperação já registrada: a evidência de fila e as linhas
-- preservadas permanecem intactas. Só remove a porta de recuperação para futuras
-- chamadas, sem reabrir caminho para a fonte legada.

begin;

revoke all on function public.otimizador_producao_recuperar_reserva_orfa_v9(uuid, bigint, boolean)
  from public, anon, authenticated, service_role;
drop function if exists public.otimizador_producao_recuperar_reserva_orfa_v9(uuid, bigint, boolean);

commit;
