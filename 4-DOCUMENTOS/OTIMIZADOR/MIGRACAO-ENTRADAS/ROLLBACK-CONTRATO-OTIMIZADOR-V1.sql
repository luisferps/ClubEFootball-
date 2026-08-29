begin;
drop function if exists public.otimizador_peso_ordem_v1();
drop function if exists public.otimizador_proxima_fila_v1(integer);
drop function if exists public.otimizador_pool_habilidades_v1(text,bigint);
drop function if exists public.otimizador_regua_v1();
drop function if exists public.otimizador_cartas_v1(jsonb);
drop function if exists public.otimizador_carta_v1(text);
drop table if exists clube_novo.atributo_ordem_otimizador;
commit;
