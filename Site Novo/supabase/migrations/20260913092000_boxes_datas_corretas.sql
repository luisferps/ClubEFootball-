-- Data de observacao do legado nao e data de lancamento.
ALTER TABLE clube_novo.box_contexto_contratacao_v1 ADD COLUMN IF NOT EXISTS data_observada_legado date;
CREATE OR REPLACE FUNCTION clube_novo.box_data_titulo_v1(t text) RETURNS date
LANGUAGE plpgsql IMMUTABLE SET search_path='' AS $$
DECLARE m text[]; mes int; ano int;
BEGIN
 m:=regexp_match(btrim(t),'(?:^| )([0-9]{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [''’]?([0-9]{4}|[0-9]{2})$','i');
 IF m IS NULL THEN RETURN NULL; END IF;
 mes:=array_position(ARRAY['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'],lower(m[2]));
 ano:=m[3]::int; IF length(m[3])=2 THEN ano:=2000+ano; END IF;
 RETURN make_date(ano,mes,m[1]::int);
EXCEPTION WHEN datetime_field_overflow THEN RETURN NULL;
END $$;
REVOKE ALL ON FUNCTION clube_novo.box_data_titulo_v1(text) FROM PUBLIC;
CREATE OR REPLACE FUNCTION clube_novo.box_data_legado_validar_v1() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
 IF NEW.oferta_fonte LIKE 'legado:%' THEN
   IF TG_OP='INSERT' THEN NEW.data_observada_legado:=coalesce(NEW.data_observada_legado,NEW.data_oferta); END IF;
   NEW.data_oferta:=clube_novo.box_data_titulo_v1(NEW.box_nome);
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION clube_novo.box_data_legado_validar_v1() FROM PUBLIC;
UPDATE clube_novo.box_contexto_contratacao_v1
 SET data_observada_legado=data_oferta,data_oferta=clube_novo.box_data_titulo_v1(box_nome)
 WHERE oferta_fonte LIKE 'legado:%';
CREATE TRIGGER box_data_legado_validar BEFORE INSERT OR UPDATE OF box_nome,data_oferta,oferta_fonte
 ON clube_novo.box_contexto_contratacao_v1 FOR EACH ROW EXECUTE FUNCTION clube_novo.box_data_legado_validar_v1();
COMMENT ON COLUMN clube_novo.box_contexto_contratacao_v1.data_observada_legado IS 'Data visto preservada do acervo legado; nunca equivale a inicio de oferta.';
COMMENT ON COLUMN clube_novo.box_contexto_contratacao_v1.data_oferta IS 'Inicio informado pela fonte comercial; no acervo legado somente data completa explicita do titulo, senao NULL. Nunca usar data visto/captura.';

