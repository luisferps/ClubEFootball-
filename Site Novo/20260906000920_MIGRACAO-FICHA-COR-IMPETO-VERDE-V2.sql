-- Ficha V2: raw1/Conexao ao vivo foi confirmado visualmente como verde.
-- A cor foi lida no hexagono dentro da arte de tres cartas independentes.

do $preflight$
begin
  if to_regclass('clube_novo.tipo_impeto_cor_visual_jogo') is null then
    raise exception 'Tabela de cores da Ficha V2 nao existe';
  end if;

  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'clube_novo.tipo_impeto_cor_visual_jogo'::regclass
      and conname = 'tipo_impeto_cor_visual_jogo_cor_visual_check'
      and pg_get_constraintdef(oid) = 'CHECK ((cor_visual = ANY (ARRAY[''azul''::text, ''roxo''::text, ''laranja''::text, ''dourado''::text])))'
  ) then
    raise exception 'Restricao de cores divergiu antes da inclusao do verde';
  end if;

  if exists (
    select 1
    from clube_novo.tipo_impeto_cor_visual_jogo
    where tipo_raw = 1
  ) then
    raise exception 'raw1 ja possui cor; aborte e audite antes de substituir';
  end if;
end
$preflight$;

alter table clube_novo.tipo_impeto_cor_visual_jogo
  drop constraint tipo_impeto_cor_visual_jogo_cor_visual_check,
  add constraint tipo_impeto_cor_visual_jogo_cor_visual_check
    check (cor_visual in ('azul','verde','roxo','laranja','dourado'));

comment on column clube_novo.tipo_impeto_cor_visual_jogo.cor_visual is
  'Cor do Impeto aplicado: azul, verde, roxo, laranja ou dourado. Cinza representa somente vaga vazia.';

