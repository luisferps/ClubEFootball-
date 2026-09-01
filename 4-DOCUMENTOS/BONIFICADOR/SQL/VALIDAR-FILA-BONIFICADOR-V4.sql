-- Leitura pós-instalação da fila V4, sem escrever resultados.
select count(*) as linhas_visiveis,
       count(distinct card_id) as cartas_visiveis,
       count(distinct funcao_id) as funcoes_visiveis
from public.bonificador_contexto_fila_v4(5000,0);

select has_function_privilege('service_role','public.bonificador_contexto_fila_v4(integer,integer)','EXECUTE') as service_role_pode_ler,
       has_function_privilege('anon','public.bonificador_contexto_fila_v4(integer,integer)','EXECUTE') as anon_pode_ler,
       has_function_privilege('authenticated','public.bonificador_contexto_fila_v4(integer,integer)','EXECUTE') as authenticated_pode_ler,
       has_function_privilege('service_role','public.gravar_build_bonificador_v4(jsonb)','EXECUTE') as service_role_pode_gravar;
