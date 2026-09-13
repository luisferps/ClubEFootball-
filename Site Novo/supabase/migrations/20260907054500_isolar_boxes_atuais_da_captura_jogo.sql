-- CmdGetMyclubAgentlist descreve somente o que a sessão atual carregou.
-- A captura é isolada por fonte e jamais encerra ou apaga as 11 ofertas atuais
-- já confirmadas pela sincronização existente.

do $block$
declare
  v_sql text;
  v_old text := 'and (x.oferta_fonte=''https://efhub.com/pt-BR'' or (x.oferta_fonte=''jogo:CmdGetMyclubAgentlist'' and not exists(select 1 from jsonb_array_elements(p->''boxes'') b where (b->>''agente_id'')::bigint=x.agente_jogo_id)))';
  v_new text := 'and x.oferta_fonte=''jogo:CmdGetMyclubAgentlist'' and not exists(select 1 from jsonb_array_elements(p->''boxes'') b where (b->>''agente_id'')::bigint=x.agente_jogo_id)';
begin
  v_sql := pg_get_functiondef('clube_novo.sincronizar_boxes_jogo_v1(jsonb)'::regprocedure);
  if (length(v_sql)-length(replace(v_sql,v_old,'')))/length(v_old) <> 2 then
    raise exception 'RPC de boxes atuais divergiu do contrato esperado; nenhuma alteração aplicada';
  end if;
  execute replace(v_sql,v_old,v_new);
end
$block$;

revoke all on function clube_novo.sincronizar_boxes_jogo_v1(jsonb)
  from public, anon, authenticated;
grant execute on function clube_novo.sincronizar_boxes_jogo_v1(jsonb)
  to service_role;

comment on function clube_novo.sincronizar_boxes_jogo_v1(jsonb) is
  'Registra somente ofertas atuais da própria fonte CmdGetMyclubAgentlist; não altera ofertas atuais de outra fonte e não representa o acervo histórico.';
