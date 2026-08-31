-- ROLLBACK DA FILA PRODUTIVA V3 — ARTEFATO PREPARADO, NAO APLICADO
--
-- Segurança: este rollback só é permitido antes de qualquer lote V3 ser criado.
-- Depois disso ele PARA, para nunca apagar linhas, resultados ou auditoria reais.

begin;

do $rollback$
begin
  if exists(select 1 from clube_novo.otimizador_lote_producao_v3) then
    raise exception 'rollback recusado: existe lote V3. Arquivamento/retenção explícitos são necessários; nada será apagado.';
  end if;
end
$rollback$;

drop function if exists public.otimizador_producao_falhar_lote_v3(uuid,text);
drop function if exists public.otimizador_producao_bloquear_linha_v3(uuid,bigint,uuid,text);
drop function if exists public.otimizador_producao_concluir_linha_v3(uuid,bigint,uuid,jsonb);
drop function if exists public.otimizador_producao_reservar_linha_v3(uuid,uuid);
drop function if exists public.otimizador_producao_controlar_lote_v3(uuid,text,boolean);
drop function if exists public.otimizador_producao_criar_lote_v3(uuid,text,text,integer);
drop function if exists public.otimizador_producao_eventos_v3(uuid);
drop function if exists public.otimizador_producao_fila_v3(uuid);
drop function if exists public.otimizador_producao_contexto_lote_v3(uuid);
drop function if exists public.otimizador_producao_status_v3(uuid);
drop function if exists clube_novo.otimizador_producao_contrato_fingerprint_v3(jsonb);

drop table if exists clube_novo.otimizador_evento_producao_v3;
drop table if exists clube_novo.otimizador_lote_producao_linha_v3;
drop table if exists clube_novo.otimizador_lote_producao_carta_v3;
drop table if exists clube_novo.otimizador_lote_producao_v3;

commit;
