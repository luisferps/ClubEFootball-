CREATE OR REPLACE FUNCTION public.extrator_aplicar_niveis_runtime_v1(p_captura jsonb, p_cartas jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
 v_contrato clube_novo.contrato_leitura_nivel_runtime_v1%rowtype;
 v_id uuid; v_instante timestamptz; v_sha text; v_rows integer; v_n integer; v_manifesto text;
 v_antiga clube_novo.nivel_runtime_captura_v1%rowtype;
begin
 if jsonb_typeof(p_captura) is distinct from 'object' or jsonb_typeof(p_cartas) is distinct from 'array' then
   raise exception 'nivel_runtime: captura objeto e cartas array obrigatorios';
 end if;
 v_rows:=jsonb_array_length(p_cartas);
 if v_rows<1 or v_rows>1000 then raise exception 'nivel_runtime: lote exige 1..1000 cartas'; end if;
 v_id:=(p_captura->>'captura_id')::uuid;
 v_instante:=(p_captura->>'capturado_em')::timestamptz;
 v_sha:=p_captura->>'executavel_sha256';
 if v_id is null or v_instante is null then raise exception 'nivel_runtime: identidade e instante obrigatorios'; end if;
 select * into v_contrato from clube_novo.contrato_leitura_nivel_runtime_v1
 where executavel_sha256=v_sha and executavel_versao=p_captura->>'executavel_versao' and ativo;
 if not found then raise exception 'nivel_runtime: executavel sem contrato fisico aprovado'; end if;
 if coalesce(p_captura->>'leitor_versao','')='' or jsonb_typeof(p_captura->'prova_json') is distinct from 'object' then
   raise exception 'nivel_runtime: leitor e prova da captura obrigatorios'; end if;
 if exists(select 1 from jsonb_array_elements(p_cartas)x
   where jsonb_typeof(x->'card_id') is distinct from 'string' or (x->>'card_id') !~ '^[0-9]+$'
   or jsonb_typeof(x->'nivel_maximo') is distinct from 'number'
   or (x->>'nivel_maximo') !~ '^[0-9]+$'
   or jsonb_typeof(x->'orcamento_real') is distinct from 'number'
   or (x->>'orcamento_real') !~ '^[0-9]+$'
   or jsonb_typeof(x->'prova_json') is distinct from 'object') then
   raise exception 'nivel_runtime: item invalido, ID textual e prova obrigatorios'; end if;
 if exists(select 1 from jsonb_array_elements(p_cartas)x where (x->>'nivel_maximo')::integer<1
   or (x->>'nivel_maximo')::integer>1000
   or (x->>'orcamento_real')::integer<>2*(x->>'nivel_maximo')::integer-2) then
   raise exception 'nivel_runtime: nivel ou formula invalidos'; end if;
 if (select count(distinct x->>'card_id') from jsonb_array_elements(p_cartas)x)<>v_rows then
   raise exception 'nivel_runtime: ID duplicado'; end if;
 if exists(select 1 from jsonb_array_elements(p_cartas)x left join clube_novo.carta_jogo c on c.card_id=x->>'card_id' where c.card_id is null) then
   raise exception 'nivel_runtime: carta ausente do cadastro, importar identidade primeiro'; end if;
 perform pg_advisory_xact_lock(hashtextextended('clubef-nivel-runtime-aplicar',0));
 if exists(select 1 from jsonb_array_elements(p_cartas)x join clube_novo.carta_nivel_evidencia_v1 e on e.card_id=x->>'card_id'
   where e.comprovado_em>v_instante or (e.comprovado_em=v_instante and e.nivel_maximo<>(x->>'nivel_maximo')::integer)) then
   raise exception 'nivel_runtime: captura antiga ou conflitante'; end if;
 v_manifesto:=encode(extensions.digest(convert_to(jsonb_build_object('captura',p_captura,'cartas',p_cartas)::text,'UTF8'),'sha256'),'hex');

 select * into v_antiga from clube_novo.nivel_runtime_captura_v1 where captura_id=v_id;
 if found then
   if v_antiga.manifesto_sha256<>v_manifesto then raise exception 'nivel_runtime: captura_id reutilizado com conteudo diferente'; end if;
   return jsonb_build_object('ok',true,'idempotente',true,'captura_id',v_id,'aplicadas',v_antiga.quantidade);
 end if;
 insert into clube_novo.nivel_runtime_captura_v1(captura_id,contrato_id,executavel_sha256,executavel_versao,leitor_versao,capturado_em,quantidade,manifesto_sha256,prova_json)
 values(v_id,v_contrato.contrato_id,v_sha,v_contrato.executavel_versao,p_captura->>'leitor_versao',v_instante,v_rows,v_manifesto,p_captura->'prova_json');
 insert into clube_novo.carta_nivel_historico_v1(captura_id,card_id,nivel_anterior,orcamento_anterior,cap_estimado_anterior,nivel_maximo,orcamento_real,prova_json)
 select v_id,c.card_id,c.level_cap,c.orcamento,c.cap_estimado,(x->>'nivel_maximo')::integer,(x->>'orcamento_real')::integer,x->'prova_json'
 from jsonb_array_elements(p_cartas)x join clube_novo.carta_jogo c on c.card_id=x->>'card_id';
 insert into clube_novo.carta_nivel_evidencia_v1(card_id,nivel_maximo,orcamento_real,fonte,contrato_id,captura_id,prova_json,comprovado_em)
 select x->>'card_id',(x->>'nivel_maximo')::integer,(x->>'orcamento_real')::integer,'memoria_jogo',v_contrato.contrato_id,v_id,x->'prova_json',v_instante
 from jsonb_array_elements(p_cartas)x
 on conflict(card_id) do update set nivel_maximo=excluded.nivel_maximo,orcamento_real=excluded.orcamento_real,contrato_id=excluded.contrato_id,captura_id=excluded.captura_id,prova_json=excluded.prova_json,comprovado_em=excluded.comprovado_em,atualizado_em=clock_timestamp();
 update clube_novo.carta_jogo c set level_cap=e.nivel_maximo,orcamento=e.orcamento_real,cap_estimado=false
 from clube_novo.carta_nivel_evidencia_v1 e where e.card_id=c.card_id and e.captura_id=v_id;
 get diagnostics v_n=row_count;
 if v_n<>v_rows or exists(select 1 from clube_novo.carta_nivel_evidencia_v1 e join clube_novo.carta_jogo c using(card_id)
   where e.captura_id=v_id and (c.level_cap is distinct from e.nivel_maximo or c.orcamento is distinct from e.orcamento_real or c.cap_estimado is distinct from false)) then
   raise exception 'nivel_runtime: falha na conferencia da gravacao'; end if;
 return jsonb_build_object('ok',true,'idempotente',false,'captura_id',v_id,'aplicadas',v_n,'contrato_id',v_contrato.contrato_id,'requer_renovar_entradas',true);
end;
$function$

;
