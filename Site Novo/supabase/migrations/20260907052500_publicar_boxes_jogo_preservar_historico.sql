-- A tela em andamento aceita somente a captura do jogo. O catálogo histórico
-- preserva as fontes comerciais anteriores comprovadas, exceto a sincronização
-- externa substituída e os rótulos físicos de variação sem fonte comercial.

create or replace view clube_novo.carta_box_oferta_v1
with (security_invoker=true) as
select m.card_id,x.box_id,x.box_nome,x.estado_box,x.data_oferta,x.origem_fingerprint
from clube_novo.box_card_em_andamento_v1 m
join clube_novo.box_contexto_contratacao_v1 x on x.box_id=m.box_id
where x.oferta_fonte is not null
  and x.oferta_fonte<>'https://efhub.com/pt-BR'
  and nullif(btrim(x.box_nome),'') is not null;

do $block$
declare v_sql text;
begin
  v_sql := pg_get_functiondef('clube_novo.site_novo_boxes_em_andamento_calculo_v1(text,text,integer,integer,integer)'::regprocedure);
  if strpos(v_sql,'and x.oferta_fonte is not null')=0 then
    raise exception 'filtro anterior da tela de boxes em andamento nao encontrado';
  end if;
  v_sql := replace(v_sql,'and x.oferta_fonte is not null','and x.oferta_fonte=''jogo:CmdGetMyclubAgentlist''');
  execute v_sql;
end
$block$;

comment on view clube_novo.carta_box_oferta_v1 is
  'Leitura de boxes comerciais comprovadas; exclui a antiga fonte externa e os rotulos fisicos de variacao.';
