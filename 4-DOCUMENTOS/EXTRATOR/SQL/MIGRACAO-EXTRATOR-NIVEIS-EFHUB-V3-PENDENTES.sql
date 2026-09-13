-- V3: nível zero ou sem evidência é pendência de coleta.
-- A lista é derivada do estado atual e desaparece automaticamente quando uma
-- evidência válida é gravada. A fila do Otimizador já exige essa evidência.

begin;

create or replace view clube_novo.carta_nivel_pendente_v1
with (security_barrier=true)
as
select
  c.card_id,
  c.nome,
  c.tipo,
  c.overall,
  c.level_cap as nivel_cadastral_nao_comprovado,
  'nivel_maximo_nao_coletado'::text as motivo
from clube_novo.carta_jogo c
where c.tipo_carta_id<>'player_delete_list'
  and c.roda_motor is not false
  and (
    c.codigo_tipo_carta_fisico=any(array[1,3,4,5,6,7])
    or (c.codigo_tipo_carta_fisico=0 and c.tipo_carta_id='player_type_0_subtype_0')
  )
  and not exists (
    select 1 from clube_novo.carta_nivel_evidencia_v1 e where e.card_id=c.card_id
  );

revoke all on clube_novo.carta_nivel_pendente_v1 from public,anon,authenticated;
grant select on clube_novo.carta_nivel_pendente_v1 to service_role;

comment on view clube_novo.carta_nivel_pendente_v1 is
  'Cartas elegiveis ao catalogo que continuam sem nivel comprovado. Level_cap zero ou ausente e pendencia, nunca nivel valido ou orcamento zero.';

notify pgrst,'reload schema';
commit;
