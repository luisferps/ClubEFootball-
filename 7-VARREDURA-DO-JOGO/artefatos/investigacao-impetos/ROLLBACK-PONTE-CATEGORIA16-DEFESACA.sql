-- Recupera exatamente o estado fotografado antes da ponte categoria 16.
-- Falha fechada se alguma linha tiver sido alterada depois desta aplicação.

begin;
set local lock_timeout = '5s';
set local statement_timeout = '30s';

do $$
declare
  atualizados integer;
begin
  if (
    select count(*)
    from clube_novo.impeto_jogo
    where codigo_jogo = any(array[67,73,79,85,91,118,315,360,381,411,420,455,464,490])
      and secao_texto = 'Any3W'
      and id_texto = 65
  ) <> 14 then
    raise exception 'estado atual divergiu da aplicação selada; rollback cancelado';
  end if;

  update clube_novo.impeto_jogo
     set secao_texto = null,
         id_texto = null
   where codigo_jogo = any(array[67,73,79,85,91,118,315,360,381,411,420,455,464,490])
     and secao_texto = 'Any3W'
     and id_texto = 65;

  get diagnostics atualizados = row_count;
  if atualizados <> 14 then
    raise exception 'esperadas 14 linhas, revertidas %', atualizados;
  end if;
end $$;

commit;
