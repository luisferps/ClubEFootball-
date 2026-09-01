-- Recuperação da instalação V4. Não apaga resultados de Bonificador.
begin;
drop function if exists public.gravar_build_bonificador_v4(jsonb);
drop function if exists public.bonificador_contexto_fila_v4(integer,integer);
commit;
