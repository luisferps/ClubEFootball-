-- Ficha V2: raw2/Conexao com o time foi confirmado visualmente como amarelo.
-- Remove o slug provisorio laranja antes que qualquer tipo o utilize.

do $preflight$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'clube_novo.tipo_impeto_cor_visual_jogo'::regclass
      and conname = 'tipo_impeto_cor_visual_jogo_cor_visual_check'
      and pg_get_constraintdef(oid) = 'CHECK ((cor_visual = ANY (ARRAY[''azul''::text, ''verde''::text, ''roxo''::text, ''laranja''::text, ''dourado''::text])))'
  ) then
    raise exception 'Restricao de cores divergiu antes da inclusao do amarelo';
  end if;

  if exists (
    select 1
    from clube_novo.tipo_impeto_cor_visual_jogo
    where cor_visual = 'laranja' or tipo_raw = 2
  ) then
    raise exception 'Laranja ou raw2 ja foi usado; aborte e audite antes de substituir';
  end if;
end
$preflight$;

alter table clube_novo.tipo_impeto_cor_visual_jogo
  drop constraint tipo_impeto_cor_visual_jogo_cor_visual_check,
  add constraint tipo_impeto_cor_visual_jogo_cor_visual_check
    check (cor_visual in ('azul','verde','roxo','amarelo','dourado'));

comment on column clube_novo.tipo_impeto_cor_visual_jogo.cor_visual is
  'Cor do Impeto aplicado: azul, verde, roxo, amarelo ou dourado. Cinza representa somente vaga vazia.';

