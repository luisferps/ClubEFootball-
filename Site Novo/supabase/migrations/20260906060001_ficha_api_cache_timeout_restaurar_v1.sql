-- Restauracao apos duas leituras HTTP 503/PGRST002 no teste autorizado.
SET lock_timeout = '3s';
DO $guard$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticator'
    AND 'statement_timeout=60s'=ANY(rolconfig)) THEN
    RAISE EXCEPTION 'Preflight divergente: authenticator nao esta em 60s';
  END IF;
END;
$guard$;
ALTER ROLE authenticator SET statement_timeout = '8s';
NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';
