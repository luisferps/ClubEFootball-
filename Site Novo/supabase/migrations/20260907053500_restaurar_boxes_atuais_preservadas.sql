-- As 11 ofertas atuais já estavam confirmadas e permanecem válidas.
-- A investigação de CmdGetMyclubAgentlist passa a ser usada para complementar
-- boxes históricas, sem retirar a leitura pública atual.

create or replace view clube_novo.carta_box_oferta_v1
with (security_invoker=true) as
select m.card_id,x.box_id,x.box_nome,x.estado_box,x.data_oferta,x.origem_fingerprint
from clube_novo.box_card_em_andamento_v1 m
join clube_novo.box_contexto_contratacao_v1 x on x.box_id=m.box_id
where x.oferta_fonte is not null
  and nullif(btrim(x.box_nome),'') is not null;

do $block$
declare v_sql text;
begin
  v_sql := pg_get_functiondef('clube_novo.site_novo_boxes_em_andamento_calculo_v1(text,text,integer,integer,integer)'::regprocedure);
  if strpos(v_sql,'and x.oferta_fonte=''jogo:CmdGetMyclubAgentlist''')=0 then
    raise exception 'filtro temporario da tela de boxes em andamento nao encontrado';
  end if;
  v_sql := replace(v_sql,'and x.oferta_fonte=''jogo:CmdGetMyclubAgentlist''','and x.oferta_fonte is not null');
  v_sql := replace(v_sql,'clube_novo.box_sincronizacao_jogo_ordem_v1','clube_novo.box_sincronizacao_efhub_v1');
  execute v_sql;
end
$block$;

comment on view clube_novo.carta_box_oferta_v1 is
  'Leitura central das boxes comerciais comprovadas. A coleta histórica é complementar e não remove as ofertas atuais.';
