-- Teste temporario autorizado pelo usuario em 06/09/2026.
-- Unica configuracao alterada: authenticator.statement_timeout 8s -> 60s.
-- anon=3s, authenticated=8s e service_role=60s permanecem intactos.
SET lock_timeout = '3s';
DO $guard$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticator'
    AND 'statement_timeout=8s'=ANY(rolconfig)) THEN
    RAISE EXCEPTION 'Preflight divergente: authenticator nao esta em 8s';
  END IF;
END;
$guard$;
ALTER ROLE authenticator SET statement_timeout = '60s';
NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';
