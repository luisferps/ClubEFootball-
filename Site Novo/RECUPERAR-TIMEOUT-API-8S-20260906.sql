-- Recuperacao do teste temporario de carregamento da API.
-- Nao altera anon, authenticated, service_role, lock_timeout ou filas.
ALTER ROLE authenticator SET statement_timeout = '8s';
NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';
