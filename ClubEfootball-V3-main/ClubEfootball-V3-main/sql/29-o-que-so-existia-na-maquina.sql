-- ============================================================================
--  29 · O QUE SÓ EXISTIA NA MÁQUINA DO LUIS — 17/08/2026
-- ============================================================================
--  Ordem do Luis, 17/08:
--    "Eu acho que o mais importante agora é colocar isso aqui no banco de
--     dados também. Porque, em suma, se sumir não é tanto ferrado."
--
--  Ele está certo. Estes quatro arquivos são os ÚNICOS insumos que não têm
--  fonte externa nenhuma. Tudo o mais o sistema recoleta do efHub, do efScout
--  ou do efootballdb. Estes não:
--
--    falta_por_card.json .......... 2.420 cartas · o espaço de habilidades
--    raras_por_card.json ............. 707 cartas · as habilidades raras
--    impeto_conferido_no_jogo.json ... 291 cartas · O LUIS OLHOU NO JOGO
--    CONFERIDO.json .................... 6 cartas · com o "como" de cada uma
--
--  As 291 são o caso grave: é o Luis abrindo carta por carta dentro do
--  eFootball e anotando o que viu. Não se recoleta. Perdeu, perdeu.
--
--  ============================================================================
--  POR QUE UMA TABELA SÓ, E NÃO QUATRO
--
--  Porque os quatro têm a mesma forma: uma chave (quase sempre o id da carta)
--  apontando para um valor. E porque assim, no dia em que aparecer um quinto
--  arquivo desses, ele entra sem SQL nenhum — só muda a coluna `arquivo`.
--
--  ⚠️ AS REGRAS ESCRITAS VÃO JUNTO. Os arquivos não têm só dado: têm as
--     chaves `_regra`, `_como_usar`, `ordem_do_luis`, `_aviso` — que explicam
--     POR QUE cada coisa é assim. Elas entram na mesma tabela, com a chave do
--     jeito que está. Perder o dado é ruim; perder o porquê é pior, porque aí
--     alguém "conserta" o que estava certo.
--
--  ⛔ SÓ ACRESCENTA. Nenhuma tabela existente é tocada.
-- ============================================================================

create table if not exists insumo_local (
  arquivo        text        not null,
  chave          text        not null,
  valor          jsonb       not null,
  atualizado_em  timestamptz not null default now(),
  primary key (arquivo, chave)
);

comment on table insumo_local is
  'Os insumos que so existiam na maquina do Luis e nao tem fonte externa: espaco de habilidades, raras, e o que ele conferiu dentro do jogo. A coluna `chave` e o id da carta, ou o nome de uma nota (_regra, _como_usar) quando o registro e documentacao.';

create index if not exists insumo_local_arquivo on insumo_local (arquivo);

-- ------------------------------------------- A LEITURA PÚBLICA
--  Mesma regra das outras: a chave do navegador LÊ, e não escreve.
alter table insumo_local enable row level security;

do $$
begin
  if not exists (select 1 from pg_policies
                 where schemaname = 'public' and tablename = 'insumo_local'
                   and policyname = 'insumo_local_leitura_publica') then
    create policy insumo_local_leitura_publica on public.insumo_local
      for select to anon, authenticated using (true);
    raise notice 'criei a politica de leitura em insumo_local';
  else
    raise notice 'a politica ja existia';
  end if;
end $$;

revoke insert, update, delete on public.insumo_local from anon;

-- ============================================================================
--  CONFERÊNCIA — rode depois de subir
-- ============================================================================
select arquivo,
       count(*) filter (where chave not like '\_%') as cartas,
       count(*) filter (where chave     like '\_%') as notas,
       count(*)                                     as total
from insumo_local
group by arquivo
order by arquivo;
