create or replace view clube_novo.box_catalogo_jogo_atual_v1 with (security_invoker=true) as
with ultima as (
 select captura_id,capturado_em,executavel_sha256 from clube_novo.box_captura_jogo_v1
 where payload->>'cobertura'='catalogo_agentes_carregado'
 order by capturado_em desc,captura_id desc limit 1
)
select a.agente_jogo_id,a.titulo,
 case when a.inicio_epoch>0 then to_timestamp(a.inicio_epoch) end as inicio_oferta,
 case when a.fim_epoch>0 then to_timestamp(a.fim_epoch) end as fim_oferta,
 u.captura_id,u.capturado_em,u.executavel_sha256,
 case when a.inicio_epoch>extract(epoch from now()) then 'futura'
      when a.fim_epoch>0 and a.fim_epoch<=extract(epoch from now()) then 'encerrada'
      else 'disponivel_na_captura' end as situacao,
 'jogo:CmdGetMyclubAgentlist'::text as fonte
from ultima u join clube_novo.box_agente_captura_jogo_v1 a using(captura_id);
revoke all on clube_novo.box_catalogo_jogo_atual_v1 from public,anon,authenticated;
grant select on clube_novo.box_catalogo_jogo_atual_v1 to service_role;
comment on view clube_novo.box_catalogo_jogo_atual_v1 is 'Ultimo catalogo de agentes capturado pelo extrator; datas oficiais e instante de captura explicitos. Independente de participantes. Nao prova ausencia de ofertas de outras colecoes.';
