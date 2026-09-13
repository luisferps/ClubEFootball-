update clube_novo.contrato_leitura_escritor_destino set colunas_escrita=array(select distinct c from unnest(colunas_escrita||array['contrato_extracao','contrato_campos_apresentacao']) c order by c),tipos_colunas=tipos_colunas||jsonb_build_object('contrato_extracao','text','contrato_campos_apresentacao','text') where destino_tabela='tecnico_jogo' and ativo;
create or replace function clube_novo.tg_data_apresentacao_tecnico_v1() returns trigger language plpgsql set search_path=pg_catalog,clube_novo as $$
begin
 if new.hash_campos_apresentacao is not null and new.carregado_campos_apresentacao_em is null then
  new.carregado_campos_apresentacao_em=statement_timestamp();
 end if;
 return new;
end $$;
revoke all on function clube_novo.tg_data_apresentacao_tecnico_v1() from public,anon,authenticated;
create trigger b_data_apresentacao_tecnico_v1 before insert or update on clube_novo.tecnico_jogo for each row execute function clube_novo.tg_data_apresentacao_tecnico_v1();
