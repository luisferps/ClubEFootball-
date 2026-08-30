-- Ponte formal e estritamente delimitada para a categoria física 16 de Ímpetos.
-- A lista foi obtida de PlayerBooster.bin bit137/w5 no run 20260830-005609.
-- Não altera código, efeitos, condições, slots de cartas, motor ou flags.

begin;
set local lock_timeout = '5s';
set local statement_timeout = '30s';

do $$
declare
  atualizados integer;
begin
  if not exists (
    select 1
    from clube_novo.texto_do_jogo
    where secao = 'Any3W'
      and id_texto = 65
      and texto = 'Defesaça'
      and fonte_cpk_sha256 = '2419045a081a151f8a0cdcc70a9ca0c4ca1ca265b8467b9c182623baa05338db'
      and fonte_arquivo_sha256 = '306741adab8376ed64620b618ae9721d316ae548b126419730b9bd5ff5f525a9'
  ) then
    raise exception 'texto físico Any3W:65 não confere com a prova selada';
  end if;

  if (
    select count(*)
    from clube_novo.impeto_jogo
    where codigo_jogo = any(array[67,73,79,85,91,118,315,360,381,411,420,455,464,490])
      and secao_texto is null
      and id_texto is null
  ) <> 14 then
    raise exception 'estado anterior dos 14 vínculos não confere; nenhuma linha foi alterada';
  end if;

  update clube_novo.impeto_jogo
     set secao_texto = 'Any3W',
         id_texto = 65
   where codigo_jogo = any(array[67,73,79,85,91,118,315,360,381,411,420,455,464,490])
     and secao_texto is null
     and id_texto is null;

  get diagnostics atualizados = row_count;
  if atualizados <> 14 then
    raise exception 'esperadas 14 linhas, atualizadas %', atualizados;
  end if;
end $$;

commit;
