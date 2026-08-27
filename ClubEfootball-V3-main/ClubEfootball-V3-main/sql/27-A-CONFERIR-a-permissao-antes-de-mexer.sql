-- ============================================================================
--  27-A · CONFERIR A PERMISSAO — SO OLHA. NAO MUDA NADA. — 17/08/2026
-- ============================================================================
--  ⛔ RODE ESTE PRIMEIRO. Ele nao altera nada, so responde tres perguntas.
--
--  POR QUE ISTO EXISTE, e e serio:
--
--  A tela nova (encaixe-web) roda no navegador, entao a chave dela fica visivel
--  para quem abrir o arquivo. Tem que ser a chave `anon`, que so faz o que as
--  regras do banco (RLS) deixarem.
--
--  O PERIGO: se o seu config.txt usar a chave `anon` — e nao a `service_role` —
--  entao LIGAR o RLS quebra TODOS os programas da pasta de uma vez: o
--  SUBIR-BASE, o grava_direto do motor, o ENCHER-O-BANCO, tudo.
--
--  Por isso nada e ligado antes de olhar. Rode, me mande o resultado, e so
--  depois a gente decide.
-- ============================================================================

-- ------------------------------------------- 1. QUAIS TABELAS JA TEM RLS
--  rls_ligado = false na maioria significa: hoje quem tem qualquer chave
--  valida le e escreve. E por isso que a tela web ainda nao pode ser publicada.
select c.relname                as tabela,
       c.relrowsecurity         as rls_ligado,
       c.relforcerowsecurity    as rls_forcado
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r'
order by c.relrowsecurity desc, c.relname;

-- --------------------------------------- 2. O QUE A CHAVE PUBLICA PODE HOJE
--  `anon` e a role da chave publica. Se aparecer INSERT, UPDATE ou DELETE
--  aqui, qualquer pessoa com a chave do HTML pode escrever no seu banco.
select table_name  as tabela,
       string_agg(distinct privilege_type, ', ' order by privilege_type) as pode
from information_schema.role_table_grants
where grantee = 'anon' and table_schema = 'public'
group by table_name
order by table_name;

-- --------------------------------------------- 3. AS POLITICAS QUE JA EXISTEM
select schemaname, tablename, policyname, roles, cmd
from pg_policies
where schemaname = 'public'
order by tablename, policyname;

-- ============================================================================
--  COMO LER O RESULTADO
--
--  Bloco 1 — se quase tudo vier `rls_ligado = false`, e o esperado: o banco
--            hoje confia na chave, nao na regra.
--
--  Bloco 2 — este e o que importa. Se `anon` aparecer com INSERT/UPDATE/DELETE
--            em qualquer tabela, a tela web NAO pode ser publicada como esta.
--
--  Bloco 3 — provavelmente vem vazio. Politica nenhuma ainda.
--
--  ⛔ ANTES DE LIGAR QUALQUER COISA, uma pergunta que so voce responde:
--     o SUPABASE_KEY do seu config.txt e a `service_role` ou a `anon`?
--     No painel: Settings -> API. A `service_role` vem marcada como secreta.
--     Se for a `anon`, a gente troca o config.txt para a service_role ANTES
--     de mexer em RLS — senao a pasta inteira para de escrever no banco.
-- ============================================================================
