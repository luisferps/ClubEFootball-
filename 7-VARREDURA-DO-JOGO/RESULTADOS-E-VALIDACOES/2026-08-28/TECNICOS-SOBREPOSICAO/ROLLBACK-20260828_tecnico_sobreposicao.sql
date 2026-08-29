-- Rollback deliberado e reversível da extensão Sobreposição.
-- Não executar automaticamente.
begin;
set local lock_timeout = '10s';
select pg_advisory_xact_lock(hashtextextended('clubef-coach-overload-v1', 0));

delete from clube_novo.tecnico_estilo_jogo
where tecnico_id=17609097478250 and codigo_estilo='overload';

update clube_novo.estilo_jogo_tecnico
set bit=null,
    largura=null,
    pode_rodar=false,
    falta_o_que='campo físico da proficiência ainda não localizado no Coach.bin atual',
    confirmado_em=now()
where codigo='overload';

delete from clube_novo.mapa_do_jogo
where assunto='tecnico.estilo.sobreposicao' and arquivo='Coach.bin';

comment on table clube_novo.estilo_jogo_tecnico is
  'Catálogo vivo, separado do playstyle de jogador. Cinco estilos têm campo físico provado; Sobreposição permanece bloqueada.';
comment on table clube_novo.tecnico_estilo_jogo is
  'Proficiências físicas 0..99 por técnico e estilo de jogo da equipe, com proveniência por associação.';

do $$
begin
  if (select count(*) from clube_novo.tecnico_estilo_jogo) <> 7390 then
    raise exception 'rollback: relações de estilo != 7390';
  end if;
  if exists (select 1 from clube_novo.tecnico_estilo_jogo where codigo_estilo='overload') then
    raise exception 'rollback: relação de Sobreposição permaneceu';
  end if;
end $$;
commit;
