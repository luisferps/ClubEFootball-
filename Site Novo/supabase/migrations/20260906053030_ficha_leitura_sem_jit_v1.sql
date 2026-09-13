-- O JIT da consulta composta excedia o timeout anon. Escopo: apenas esta RPC de leitura.
ALTER FUNCTION public.site_novo_ficha_v2(text,bigint) SET jit TO off;
NOTIFY pgrst,'reload schema';
