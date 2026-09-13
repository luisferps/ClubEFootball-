-- A tabela historica aceita o par finalizada/anterior.
do $block$
declare v_sql text;
begin
  v_sql := pg_get_functiondef('clube_novo.sincronizar_boxes_jogo_v1(jsonb)'::regprocedure);
  if strpos(v_sql,'status_origem=''substituida_por_captura_do_jogo''')=0 then
    raise exception 'definicao anterior da RPC de boxes nao encontrada';
  end if;
  v_sql := replace(v_sql,'status_origem=''substituida_por_captura_do_jogo''','status_origem=''anterior''');
  execute v_sql;
end
$block$;

comment on function clube_novo.sincronizar_boxes_jogo_v1(jsonb) is
  'Aplica atomicamente a captura do jogo; ofertas substituídas fecham como finalizada/anterior.';
