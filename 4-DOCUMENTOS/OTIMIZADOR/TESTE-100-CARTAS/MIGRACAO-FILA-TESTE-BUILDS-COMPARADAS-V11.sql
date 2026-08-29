-- V11: telemetria de auditoria. Não altera fórmula, pesos, fila, publicação ou seleção.
-- Cada unidade é uma candidata que chegou à comparação real de build na linha.
begin;

alter table clube_novo.build_otimizador
  add column if not exists builds_comparadas integer;

alter table clube_novo.build_otimizador
  drop constraint if exists build_otimizador_builds_comparadas_nao_negativas;
alter table clube_novo.build_otimizador
  add constraint build_otimizador_builds_comparadas_nao_negativas
  check (builds_comparadas is null or builds_comparadas >= 0);

create or replace function public.otimizador_concluir_linha_teste_v1(p_linha_id bigint,p_lote_id uuid,p_resultado jsonb)
returns bigint language plpgsql security definer set search_path=''
as $$
declare v_linha clube_novo.build_linha_card%rowtype; v_id bigint; v_habs integer[]; v_builds integer;
begin
 select * into v_linha from clube_novo.build_linha_card
  where id=p_linha_id and lote_teste_id=p_lote_id and execucao_tipo='teste_isolado' for update;
 if v_linha.id is null then raise exception 'linha de teste inexistente'; end if;
 if v_linha.build_otimizador_id is not null and v_linha.estado_otimizador='concluido' then return v_linha.build_otimizador_id; end if;
 if v_linha.estado_otimizador<>'processando' then raise exception 'linha nao esta processando'; end if;
 if p_resultado->>'card_id'<>v_linha.card_id or (p_resultado->>'funcao_id')::bigint<>v_linha.funcao_id
    or (p_resultado->>'posicao_id')::integer<>v_linha.posicao_id then raise exception 'resultado nao pertence a linha selada'; end if;
 if p_resultado->>'carta_versao'<>v_linha.carta_versao or p_resultado->>'carta_fingerprint'<>v_linha.carta_fingerprint
    or p_resultado->>'lote_fingerprint'<>v_linha.lote_teste_fingerprint then raise exception 'versao/fingerprint da entrada diverge'; end if;
 if p_resultado->>'formula_fingerprint'<>v_linha.otimizador_formula_fingerprint_esperado
    or p_resultado->>'contrato_fingerprint'<>v_linha.otimizador_contrato_fingerprint_esperado
    or p_resultado->>'motor_versao'<>v_linha.otimizador_motor_versao_esperada then raise exception 'selos do motor/contrato/formula divergem'; end if;
 if p_resultado ? 'builds_comparadas' then
   if jsonb_typeof(p_resultado->'builds_comparadas') <> 'number'
      or (p_resultado->>'builds_comparadas') !~ '^[0-9]+$' then
     raise exception 'telemetria builds_comparadas invalida';
   end if;
   v_builds := (p_resultado->>'builds_comparadas')::integer;
 end if;
 select coalesce(array_agg(x::integer),'{}'::integer[]) into v_habs
   from (select jsonb_array_elements_text(coalesce(p_resultado->'habilidades','[]'::jsonb)) x limit 5) q;
 insert into clube_novo.build_otimizador(tecnico_id,barras,impeto_adicional_codigo,habilidades_adicionais,pontuacao,
   contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,formula_fingerprint,resultado_fingerprint,motor_versao,builds_comparadas)
 values((p_resultado->>'tecnico_id')::bigint,p_resultado->'barras',null,v_habs,(p_resultado->>'b1')::numeric,
   coalesce(p_resultado#>>'{insumos,fonte}','otimizador_regua_v1'),p_resultado->>'contrato_fingerprint',
   v_linha.carta_versao,v_linha.carta_fingerprint,p_resultado->>'formula_fingerprint',
   encode(extensions.digest(p_resultado::text,'sha256'),'hex'),p_resultado->>'motor_versao',v_builds) returning id into v_id;
 update clube_novo.build_linha_card set build_otimizador_id=v_id,estado_otimizador='concluido',
   otimizador_finalizado_em=clock_timestamp(),otimizador_motor_versao=p_resultado->>'motor_versao',
   otimizador_contrato_versao=coalesce(p_resultado#>>'{insumos,fonte}','otimizador_regua_v1'),
   snapshot_otimizador_fingerprint=(select resultado_fingerprint from clube_novo.build_otimizador where id=v_id),
   erro_otimizador=null where id=v_linha.id;
 return v_id;
end $$;

create or replace function public.otimizador_fila_teste_v1(p_lote_id uuid)
returns jsonb language sql stable security definer set search_path=''
as $$
select coalesce(jsonb_agg(jsonb_build_object(
 'linha_id',l.id,'card_id',l.card_id,'funcao_id',l.funcao_id,
 'funcao_codigo_compat',f.codigo_legado,'funcao_nome',f.rotulo,
 'posicao_id',l.posicao_id,'posicao_codigo',p.codigo_pt,'posicao_nome',p.nome_pt,
 'ordem_card',l.amostra_ordem,'estado',l.estado_otimizador,
 'carta_versao',l.carta_versao,'carta_fingerprint',l.carta_fingerprint,
 'lote_fingerprint',l.lote_teste_fingerprint,'erro',l.erro_otimizador,
 'b1',b.pontuacao,'pontuacao_final',b.pontuacao,'barras',b.barras,
 'tecnico_id',b.tecnico_id,'habilidades_adicionais',b.habilidades_adicionais,
 'builds_comparadas',b.builds_comparadas,
 'segundos',case when l.otimizador_iniciado_em is not null and l.otimizador_finalizado_em is not null
                 then round(extract(epoch from (l.otimizador_finalizado_em-l.otimizador_iniciado_em))::numeric,2)
            end,
 'otimizador_iniciado_em',l.otimizador_iniciado_em,
 'otimizador_finalizado_em',l.otimizador_finalizado_em
) order by l.amostra_ordem,f.ordem,l.posicao_id),'[]'::jsonb)
from clube_novo.build_linha_card l
join clube_novo.funcao_sistema f on f.id=l.funcao_id
join clube_novo.posicao_jogo p on p.id=l.posicao_id
left join clube_novo.build_otimizador b on b.id=l.build_otimizador_id
where l.lote_teste_id=p_lote_id and l.execucao_tipo='teste_isolado';
$$;

revoke all on function public.otimizador_concluir_linha_teste_v1(bigint,uuid,jsonb) from public,anon,authenticated;
revoke all on function public.otimizador_fila_teste_v1(uuid) from public,anon,authenticated;
grant execute on function public.otimizador_concluir_linha_teste_v1(bigint,uuid,jsonb),public.otimizador_fila_teste_v1(uuid) to service_role;

commit;
