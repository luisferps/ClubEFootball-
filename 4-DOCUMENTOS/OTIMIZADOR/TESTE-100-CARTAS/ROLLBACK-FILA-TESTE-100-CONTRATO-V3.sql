begin;
drop function if exists public.otimizador_eventos_teste_v1(uuid);
drop function if exists public.otimizador_criar_amostra_teste_v2(uuid,text,text,text,text);
alter table clube_novo.build_linha_card
 drop column if exists otimizador_formula_fingerprint_esperado,
 drop column if exists otimizador_contrato_fingerprint_esperado,
 drop column if exists otimizador_motor_versao_esperada;
commit;
