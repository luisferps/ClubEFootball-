-- ============================================================================
--  27-B · FECHAR A cards_base E ABRIR A LEITURA DA TELA — 17/08/2026
-- ============================================================================
--  O QUE O 27-A MEDIU, e que fez este arquivo existir:
--
--    tabelas ............... 42
--    com RLS ligado ........ 41
--    ⛔ SEM RLS ............  1  ->  cards_base
--    politicas que existem .  3  ->  cards_efhub, pacotes, vigia_log (SELECT)
--
--  DUAS CONCLUSOES:
--
--  1. A CHAVE DO config.txt E A `service_role`. Esta provado, nao suposto:
--     a `builds` tem RLS ligado e NAO tem politica de INSERT. Mesmo assim o
--     motor gravou 12.326 linhas nela. So a service_role passa por cima de RLS.
--     -> Logo, mexer em politica NAO derruba programa nenhum da pasta.
--
--  2. A cards_base — as 6.469 cartas, o coracao do sistema — e a UNICA tabela
--     sem RLS. Hoje qualquer chave valida le E ESCREVE nela. Publicar a tela
--     com a chave `anon` sem fechar isso seria entregar a cards_base junto.
--
--  ⛔ SO ACRESCENTA PROTECAO. Nenhuma linha de dado e tocada.
--  ⛔ NENHUMA politica de INSERT, UPDATE ou DELETE e criada para `anon`.
--     A chave do HTML vai poder LER o que a tela mostra, e mais nada.
--  ⛔ A `meu_time` fica DE FORA de proposito: ela e o time do Luis. O time de
--     cada usuario vai ser outra coisa (navegador agora, login depois).
-- ============================================================================

-- ---------------------------------------------------------- 1. ANTES (olhe)
select c.relname as tabela, c.relrowsecurity as rls_ligado
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity;
--  Tem que aparecer a cards_base. Se aparecer mais alguma, PARE e me avise.

-- ------------------------------------------- 2. FECHAR A cards_base
alter table cards_base enable row level security;

-- ------------------------------- 3. A LEITURA PUBLICA, TABELA POR TABELA
--  Cada bloco cria a politica so se ela ainda nao existir, entao rodar de
--  novo nao quebra.
do $$
declare
  t text;
  -- ⛔ ESTA LISTA E O CONTRATO. Tabela que nao esta aqui continua fechada
  --    para a chave publica. Nao acrescentar sem pensar duas vezes.
  tabelas text[] := array[
    'cards_base',              -- as cartas
    'builds',                  -- o resultado do motor
    'bonus',                   -- o resultado do motor de bonus
    'funcoes',                 -- as 19 funcoes
    'campanha',                -- as box e suas cartas
    'insumo_player_type',      -- o tipo da carta
    'insumo_molde',            -- o alvo de cada funcao
    'insumo_habilidade',       -- o efeito de cada habilidade
    'insumo_tecnico',          -- os tecnicos
    'insumo_impeto_catalogo',  -- os impetos fabricaveis
    'insumo_bloqueio',         -- bloqueio por posicao
    'insumo_regra_funcao',     -- posicao x funcao
    'estilo_valor',            -- quanto vale cada estilo
    'traducao'                 -- o de-para dos nomes
  ];
begin
  foreach t in array tabelas loop
    if not exists (select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
                   where n.nspname='public' and c.relname=t) then
      raise notice 'PULEI: a tabela % nao existe', t;
      continue;
    end if;
    execute format('alter table public.%I enable row level security', t);
    if not exists (select 1 from pg_policies
                   where schemaname='public' and tablename=t
                     and policyname = t || '_leitura_publica') then
      execute format(
        'create policy %I on public.%I for select to anon, authenticated using (true)',
        t || '_leitura_publica', t);
      raise notice 'criei a politica de leitura em %', t;
    else
      raise notice 'ja existia em %', t;
    end if;
  end loop;
end $$;

-- ------------------------- 4. TIRAR A ESCRITA DA CHAVE PUBLICA, DE VEZ
--  O RLS ja bloqueia (nao existe politica de escrita). Isto e cinto e
--  suspensorio: mesmo que alguem crie uma politica larga por engano no
--  futuro, sem o GRANT a chave publica continua sem escrever.
--  ⚠️ NAO mexe na service_role: ela nao usa estes grants.
revoke insert, update, delete on all tables in schema public from anon;
alter default privileges in schema public revoke insert, update, delete on tables from anon;

-- ------------------------------------------------------- 5. DEPOIS (confira)
select 'sem RLS (tem que vir VAZIO)' as conferencia, c.relname as tabela
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity

union all

select 'anon ESCREVE em (tem que vir VAZIO)', table_name
from information_schema.role_table_grants
where grantee = 'anon' and table_schema = 'public'
  and privilege_type in ('INSERT','UPDATE','DELETE')

union all

select 'anon LE em', tablename
from pg_policies
where schemaname = 'public' and cmd = 'SELECT' and 'anon' = any(roles)
order by 1, 2;

-- ============================================================================
--  COMO LER O RESULTADO DO BLOCO 5
--
--    "sem RLS"        -> tem que vir VAZIO. Se sobrar tabela, ela esta aberta.
--    "anon ESCREVE"   -> tem que vir VAZIO. Se sobrar, alguem pode escrever
--                        com a chave do HTML.
--    "anon LE em"     -> as 14 da lista, e so elas.
--
--  DEPOIS DISSO, rode o SUBIR-BASE.bat e o motor uma vez para confirmar que a
--  service_role continua escrevendo normal. Deve continuar — mas conferir e
--  barato, e a alternativa e descobrir amanha.
-- ============================================================================
