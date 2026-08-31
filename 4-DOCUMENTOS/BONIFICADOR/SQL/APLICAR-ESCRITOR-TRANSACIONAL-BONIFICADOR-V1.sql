-- Escritor transacional do Bonificador para o modelo clube_novo.
--
-- PRE-REQUISITO: APLICAR-COMPLETUDE-MOTORES-CARTA-V1.sql instalado, sem
-- pendencias em seu VALIDAR. Este arquivo NAO altera publicacao, Home ou box.
-- Ele tambem nao reativa public.gravar_bonus(jsonb), que permanece bloqueada.

begin;

do $preflight$
declare
  v_missing text;
begin
  if to_regprocedure('public.gravar_build_bonificador_v1(jsonb)') is not null then
    raise exception 'preflight: gravar_build_bonificador_v1(jsonb) ja existe; nada foi sobrescrito';
  end if;
  if to_regprocedure('public.bonificador_contexto_escrita_v2(integer,integer)') is not null then
    raise exception 'preflight: bonificador_contexto_escrita_v2(integer,integer) ja existe; nada foi sobrescrito';
  end if;

  if to_regprocedure('public.bonificador_carta_v1(text)') is null
     or to_regprocedure('public.bonificador_carta_sem_completude_v1(text)') is null
     or to_regprocedure('public.bonificador_regua_v1()') is null
     or to_regprocedure('clube_novo.carta_input_motor_canonico_v1(text)') is null
     or to_regclass('clube_novo.carta_completude_motor_versao') is null then
    raise exception 'preflight: o gate APLICAR-COMPLETUDE-MOTORES-CARTA-V1.sql nao esta instalado';
  end if;

  if to_regprocedure('extensions.digest(text,text)') is null then
    raise exception 'preflight: extensions.digest(text,text) nao esta disponivel';
  end if;
  if current_user <> 'postgres' then
    raise exception 'preflight: aplicar como postgres para fixar explicitamente o owner do SECURITY DEFINER';
  end if;

  select string_agg(x.objeto, ', ' order by x.objeto)
    into v_missing
  from (values
    ('clube_novo.build_bonificador'),
    ('clube_novo.build_linha_card'),
    ('clube_novo.carta_completude_motor_versao'),
    ('clube_novo.bonificador_par'),
    ('clube_novo.funcao_sistema')
  ) x(objeto)
  where to_regclass(x.objeto) is null;
  if v_missing is not null then
    raise exception 'preflight: tabelas operacionais ausentes: %', v_missing;
  end if;

  select string_agg(x.tabela || '.' || x.coluna, ', ' order by x.tabela, x.coluna)
    into v_missing
  from (values
    ('build_bonificador','id'),('build_bonificador','bonus_pe'),
    ('build_bonificador','bonus_fisico_total'),('build_bonificador','bonus_fisico_detalhe'),
    ('build_bonificador','bonus_posicao'),('build_bonificador','bonus_playstyle_1'),
    ('build_bonificador','bonus_playstyle_2'),('build_bonificador','bonus_ia'),
    ('build_bonificador','bonus_outros'),('build_bonificador','bonus_total'),
    ('build_bonificador','contrato_versao'),('build_bonificador','contrato_fingerprint'),
    ('build_bonificador','carta_versao'),('build_bonificador','carta_fingerprint'),
    ('build_bonificador','formula_fingerprint'),('build_bonificador','resultado_fingerprint'),
    ('build_bonificador','motor_versao'),
    ('build_linha_card','id'),('build_linha_card','card_id'),
    ('build_linha_card','funcao_id'),('build_linha_card','posicao_id'),
    ('build_linha_card','carta_versao'),('build_linha_card','carta_fingerprint'),
    ('build_linha_card','estado'),('build_linha_card','build_bonificador_id'),
    ('build_linha_card','build_otimizador_id'),
    ('build_linha_card','bonificador_motor_versao'),
    ('build_linha_card','bonificador_contrato_versao'),
    ('build_linha_card','snapshot_bonificador_fingerprint'),
    ('carta_completude_motor_versao','versao_id'),
    ('carta_completude_motor_versao','card_id'),
    ('carta_completude_motor_versao','regra_versao'),
    ('carta_completude_motor_versao','completude_fingerprint_sha256'),
    ('carta_completude_motor_versao','vigente'),
    ('carta_completude_motor_versao','apto_motor'),
    ('bonificador_par','card_id'),('bonificador_par','funcao_id'),
    ('funcao_sistema','id'),('funcao_sistema','codigo_legado'),
    ('funcao_sistema','pode_rodar')
  ) x(tabela,coluna)
  where not exists (
    select 1
    from information_schema.columns c
    where c.table_schema='clube_novo'
      and c.table_name=x.tabela
      and c.column_name=x.coluna
  );
  if v_missing is not null then
    raise exception 'preflight: colunas reais exigidas nao existem: %', v_missing;
  end if;

  if not exists (
    select 1
    from pg_trigger t
    join pg_class c on c.oid=t.tgrelid
    join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='clube_novo'
      and c.relname='build_linha_card'
      and t.tgname='build_linha_completude_motor_v1'
      and not t.tgisinternal
      and t.tgenabled <> 'D'
  ) then
    raise exception 'preflight: trigger universal de completude da build nao esta ativo';
  end if;

end
$preflight$;

-- Contexto de escrita privado. O cliente nao inventa IDs nem fingerprints:
-- recebe todos os selos do banco e o writer os recalcula antes de aceitar.
create function public.bonificador_contexto_escrita_v2(
  p_limit integer default 1000,
  p_offset integer default 0
)
returns table(
  build_linha_card_id bigint,
  card_id text,
  funcao_id bigint,
  funcao_codigo text,
  posicao_id integer,
  carta_versao text,
  carta_fingerprint text,
  contrato_versao text,
  contrato_fingerprint text,
  formula_fingerprint text
)
language plpgsql
stable
security definer
set search_path = ''
as $function$
declare
  v_regua jsonb;
  v_contrato_fingerprint text;
  v_formula_fingerprint text;
begin
  v_regua := public.bonificador_regua_v1();
  if not coalesce((v_regua->>'pode_rodar')::boolean,false) then
    raise exception 'contexto recusado: regua atual do Bonificador esta bloqueada: %',
      coalesce(v_regua->'falta_o_que','["regua sem resposta"]'::jsonb);
  end if;

  v_contrato_fingerprint := encode(extensions.digest(jsonb_build_object(
    'bonificador_regua_v1',pg_get_functiondef('public.bonificador_regua_v1()'::regprocedure),
    'bonificador_carta_v1',pg_get_functiondef('public.bonificador_carta_v1(text)'::regprocedure),
    'bonificador_carta_base_v1',pg_get_functiondef('public.bonificador_carta_sem_completude_v1(text)'::regprocedure)
  )::text,'sha256'),'hex');
  v_formula_fingerprint := encode(extensions.digest(v_regua::text,'sha256'),'hex');

  return query
  select
    l.id,p.card_id,p.funcao_id,f.codigo_legado,l.posicao_id,
    cm.regra_versao,cm.completude_fingerprint_sha256,
    'bonificador-regua-v1+bonificador-carta-v1'::text,
    v_contrato_fingerprint,v_formula_fingerprint
  from clube_novo.bonificador_par p
  join clube_novo.funcao_sistema f
    on f.id=p.funcao_id and f.pode_rodar
  join clube_novo.build_linha_card l
    on l.card_id=p.card_id and l.funcao_id=p.funcao_id
  join clube_novo.carta_completude_motor_versao cm
    on cm.card_id=l.card_id and cm.vigente and cm.apto_motor
  cross join lateral (select public.bonificador_carta_v1(p.card_id) pacote) g
  where l.estado='pendente'
    and l.build_otimizador_id is not null
    and l.build_bonificador_id is null
    and l.carta_versao=cm.regra_versao
    and l.carta_fingerprint=cm.completude_fingerprint_sha256
    and coalesce((g.pacote->>'pode_rodar')::boolean,false)
  order by l.id
  limit least(greatest(coalesce(p_limit,1000),1),5000)
  offset greatest(coalesce(p_offset,0),0);
end
$function$;

alter function public.bonificador_contexto_escrita_v2(integer,integer)
  owner to postgres;
revoke all on function public.bonificador_contexto_escrita_v2(integer,integer)
  from public, anon, authenticated;
grant execute on function public.bonificador_contexto_escrita_v2(integer,integer)
  to service_role;

create function public.gravar_build_bonificador_v1(p_resultado jsonb)
returns jsonb
language plpgsql
volatile
security definer
set search_path = ''
as $function$
declare
  v_linha clube_novo.build_linha_card%rowtype;
  v_comp clube_novo.carta_completude_motor_versao%rowtype;
  v_gate jsonb;
  v_regua jsonb;
  v_contrato_versao text := 'bonificador-regua-v1+bonificador-carta-v1';
  v_contrato_fingerprint text;
  v_formula_fingerprint text;
  v_canonico jsonb;
  v_resultado_fingerprint text;
  v_bonus_id bigint;
  v_existente clube_novo.build_bonificador%rowtype;
  v_ligacao bigint;
  v_bonus_pe numeric;
  v_bonus_fisico_total numeric;
  v_bonus_posicao numeric;
  v_bonus_playstyle_1 numeric;
  v_bonus_playstyle_2 numeric;
  v_bonus_ia numeric;
  v_bonus_total numeric;
  v_repeticao boolean := false;
begin
  if p_resultado is null or jsonb_typeof(p_resultado) <> 'object' then
    raise exception 'resultado recusado: p_resultado precisa ser um objeto JSON';
  end if;

  if not p_resultado ?& array[
    'build_linha_card_id','card_id','funcao_id','posicao_id',
    'carta_versao','carta_fingerprint','contrato_versao','contrato_fingerprint',
    'formula_fingerprint','motor_versao','bonus_pe','bonus_fisico_total',
    'bonus_fisico_detalhe','bonus_posicao','bonus_playstyle_1',
    'bonus_playstyle_2','bonus_ia','bonus_outros','bonus_total'
  ] then
    raise exception 'resultado recusado: faltam campos obrigatorios do contrato V1';
  end if;

  if p_resultado - array[
    'build_linha_card_id','card_id','funcao_id','posicao_id',
    'carta_versao','carta_fingerprint','contrato_versao','contrato_fingerprint',
    'formula_fingerprint','motor_versao','bonus_pe','bonus_fisico_total',
    'bonus_fisico_detalhe','bonus_posicao','bonus_playstyle_1',
    'bonus_playstyle_2','bonus_ia','bonus_outros','bonus_total'
  ] <> '{}'::jsonb then
    raise exception 'resultado recusado: o contrato V1 nao aceita campos desconhecidos: %',
      p_resultado - array[
        'build_linha_card_id','card_id','funcao_id','posicao_id',
        'carta_versao','carta_fingerprint','contrato_versao','contrato_fingerprint',
        'formula_fingerprint','motor_versao','bonus_pe','bonus_fisico_total',
        'bonus_fisico_detalhe','bonus_posicao','bonus_playstyle_1',
        'bonus_playstyle_2','bonus_ia','bonus_outros','bonus_total'
      ];
  end if;

  if jsonb_typeof(p_resultado->'build_linha_card_id') <> 'number'
     or jsonb_typeof(p_resultado->'funcao_id') <> 'number'
     or jsonb_typeof(p_resultado->'posicao_id') <> 'number' then
    raise exception 'resultado recusado: ids da linha, funcao e posicao precisam ser numericos';
  end if;
  if (p_resultado->>'build_linha_card_id')::numeric
       <> trunc((p_resultado->>'build_linha_card_id')::numeric)
     or (p_resultado->>'funcao_id')::numeric
       <> trunc((p_resultado->>'funcao_id')::numeric)
     or (p_resultado->>'posicao_id')::numeric
       <> trunc((p_resultado->>'posicao_id')::numeric) then
    raise exception 'resultado recusado: ids precisam ser numeros inteiros';
  end if;

  if jsonb_typeof(p_resultado->'bonus_pe') <> 'number'
     or jsonb_typeof(p_resultado->'bonus_fisico_total') <> 'number'
     or jsonb_typeof(p_resultado->'bonus_posicao') <> 'number'
     or jsonb_typeof(p_resultado->'bonus_playstyle_1') <> 'number'
     or jsonb_typeof(p_resultado->'bonus_playstyle_2') <> 'number'
     or jsonb_typeof(p_resultado->'bonus_ia') <> 'number'
     or jsonb_typeof(p_resultado->'bonus_total') <> 'number' then
    raise exception 'resultado recusado: todas as parcelas e o total precisam ser numeros explicitos';
  end if;

  if jsonb_typeof(p_resultado->'bonus_fisico_detalhe') <> 'object'
     or jsonb_typeof(p_resultado->'bonus_outros') <> 'object' then
    raise exception 'resultado recusado: bonus_fisico_detalhe e bonus_outros precisam ser objetos JSON';
  end if;
  if p_resultado->'bonus_outros' <> '{}'::jsonb then
    raise exception 'resultado recusado: bonus_outros ainda nao possui contrato de soma no writer V1';
  end if;
  if p_resultado->'bonus_fisico_detalhe' = '{}'::jsonb
     or exists (
       select 1
       from jsonb_each(p_resultado->'bonus_fisico_detalhe') d
       where jsonb_typeof(d.value) <> 'number'
     ) then
    raise exception 'resultado recusado: detalhe fisico precisa conter contribuicoes numericas';
  end if;

  if nullif(btrim(p_resultado->>'card_id'),'') is null
     or nullif(btrim(p_resultado->>'carta_versao'),'') is null
     or nullif(btrim(p_resultado->>'carta_fingerprint'),'') is null
     or nullif(btrim(p_resultado->>'contrato_versao'),'') is null
     or nullif(btrim(p_resultado->>'contrato_fingerprint'),'') is null
     or nullif(btrim(p_resultado->>'formula_fingerprint'),'') is null
     or nullif(btrim(p_resultado->>'motor_versao'),'') is null then
    raise exception 'resultado recusado: identidade e selos nao podem estar vazios';
  end if;

  v_bonus_pe := (p_resultado->>'bonus_pe')::numeric;
  v_bonus_fisico_total := (p_resultado->>'bonus_fisico_total')::numeric;
  v_bonus_posicao := (p_resultado->>'bonus_posicao')::numeric;
  v_bonus_playstyle_1 := (p_resultado->>'bonus_playstyle_1')::numeric;
  v_bonus_playstyle_2 := (p_resultado->>'bonus_playstyle_2')::numeric;
  v_bonus_ia := (p_resultado->>'bonus_ia')::numeric;
  v_bonus_total := (p_resultado->>'bonus_total')::numeric;

  if (select sum((d.value #>> '{}')::numeric)
      from jsonb_each(p_resultado->'bonus_fisico_detalhe') d)
     is distinct from v_bonus_fisico_total then
    raise exception 'resultado recusado: soma do detalhe fisico diverge de bonus_fisico_total';
  end if;

  if v_bonus_total is distinct from
       v_bonus_pe + v_bonus_fisico_total + v_bonus_posicao
       + v_bonus_playstyle_1 + v_bonus_playstyle_2 + v_bonus_ia then
    raise exception 'resultado recusado: bonus_total diverge das parcelas declaradas';
  end if;

  select * into v_linha
  from clube_novo.build_linha_card
  where id=(p_resultado->>'build_linha_card_id')::bigint;
  if v_linha.id is null then
    raise exception 'resultado recusado: build_linha_card % nao existe',
      p_resultado->>'build_linha_card_id';
  end if;

  if v_linha.card_id is distinct from p_resultado->>'card_id'
     or v_linha.funcao_id is distinct from (p_resultado->>'funcao_id')::bigint
     or v_linha.posicao_id is distinct from (p_resultado->>'posicao_id')::integer then
    raise exception 'resultado recusado: identidade card/funcao/posicao nao corresponde a linha bloqueada';
  end if;
  select * into v_comp
  from clube_novo.carta_completude_motor_versao
  where card_id=v_linha.card_id and vigente and apto_motor
  for share;
  if v_comp.versao_id is null then
    raise exception 'resultado recusado: carta % sem completude vigente e apta', v_linha.card_id;
  end if;

  -- Mesma ordem da invalidação por insumo: primeiro a versão, depois a linha.
  -- A releitura sob lock impede usar uma identidade que mudou entre as duas.
  select * into v_linha
  from clube_novo.build_linha_card
  where id=(p_resultado->>'build_linha_card_id')::bigint
  for update;
  if v_linha.id is null
     or v_linha.card_id is distinct from p_resultado->>'card_id'
     or v_linha.funcao_id is distinct from (p_resultado->>'funcao_id')::bigint
     or v_linha.posicao_id is distinct from (p_resultado->>'posicao_id')::integer then
    raise exception 'resultado recusado: identidade da linha mudou durante o lock';
  end if;

  if p_resultado->>'carta_versao' is distinct from v_comp.regra_versao
     or p_resultado->>'carta_fingerprint' is distinct from v_comp.completude_fingerprint_sha256
     or v_linha.carta_versao is distinct from v_comp.regra_versao
     or v_linha.carta_fingerprint is distinct from v_comp.completude_fingerprint_sha256 then
    raise exception 'resultado recusado: carta_versao/carta_fingerprint ficaram obsoletos';
  end if;

  v_gate := public.bonificador_carta_v1(v_linha.card_id);
  if not coalesce((v_gate->>'pode_rodar')::boolean,false)
     or v_gate->>'carta_versao' is distinct from v_comp.regra_versao
     or v_gate->>'carta_fingerprint' is distinct from v_comp.completude_fingerprint_sha256 then
    raise exception 'resultado recusado: gate atual do Bonificador fechou: %',
      coalesce(v_gate->'falta_o_que','["gate sem resposta"]'::jsonb);
  end if;

  v_regua := public.bonificador_regua_v1();
  if not coalesce((v_regua->>'pode_rodar')::boolean,false) then
    raise exception 'resultado recusado: regua atual do Bonificador fechou: %',
      coalesce(v_regua->'falta_o_que','["regua sem resposta"]'::jsonb);
  end if;
  v_contrato_fingerprint := encode(extensions.digest(jsonb_build_object(
    'bonificador_regua_v1',pg_get_functiondef('public.bonificador_regua_v1()'::regprocedure),
    'bonificador_carta_v1',pg_get_functiondef('public.bonificador_carta_v1(text)'::regprocedure),
    'bonificador_carta_base_v1',pg_get_functiondef('public.bonificador_carta_sem_completude_v1(text)'::regprocedure)
  )::text,'sha256'),'hex');
  v_formula_fingerprint := encode(extensions.digest(v_regua::text,'sha256'),'hex');
  if p_resultado->>'contrato_versao' is distinct from v_contrato_versao
     or p_resultado->>'contrato_fingerprint' is distinct from v_contrato_fingerprint
     or p_resultado->>'formula_fingerprint' is distinct from v_formula_fingerprint then
    raise exception 'resultado recusado: selos do contrato/formula ficaram obsoletos';
  end if;

  v_canonico := jsonb_build_object(
    'writer','public.gravar_build_bonificador_v1',
    'writer_contract','bonificador-writer-v1',
    'build_linha_card_id',v_linha.id,
    'card_id',v_linha.card_id,
    'funcao_id',v_linha.funcao_id,
    'posicao_id',v_linha.posicao_id,
    'carta_versao',v_comp.regra_versao,
    'carta_fingerprint',v_comp.completude_fingerprint_sha256,
    'contrato_versao',v_contrato_versao,
    'contrato_fingerprint',v_contrato_fingerprint,
    'formula_fingerprint',v_formula_fingerprint,
    'motor_versao',p_resultado->>'motor_versao',
    'bonus_pe',v_bonus_pe,
    'bonus_fisico_total',v_bonus_fisico_total,
    'bonus_fisico_detalhe',p_resultado->'bonus_fisico_detalhe',
    'bonus_posicao',v_bonus_posicao,
    'bonus_playstyle_1',v_bonus_playstyle_1,
    'bonus_playstyle_2',v_bonus_playstyle_2,
    'bonus_ia',v_bonus_ia,
    'bonus_outros',p_resultado->'bonus_outros',
    'bonus_total',v_bonus_total
  );
  v_resultado_fingerprint := encode(
    extensions.digest(v_canonico::text,'sha256'),'hex'
  );

  select * into v_existente
  from clube_novo.build_bonificador
  where resultado_fingerprint=v_resultado_fingerprint;

  if v_existente.id is not null then
    if v_existente.bonus_pe is distinct from v_bonus_pe
       or v_existente.bonus_fisico_total is distinct from v_bonus_fisico_total
       or v_existente.bonus_fisico_detalhe is distinct from p_resultado->'bonus_fisico_detalhe'
       or v_existente.bonus_posicao is distinct from v_bonus_posicao
       or v_existente.bonus_playstyle_1 is distinct from v_bonus_playstyle_1
       or v_existente.bonus_playstyle_2 is distinct from v_bonus_playstyle_2
       or v_existente.bonus_ia is distinct from v_bonus_ia
       or v_existente.bonus_outros is distinct from p_resultado->'bonus_outros'
       or v_existente.bonus_total is distinct from v_bonus_total
       or v_existente.contrato_versao is distinct from v_contrato_versao
       or v_existente.contrato_fingerprint is distinct from v_contrato_fingerprint
       or v_existente.carta_versao is distinct from v_comp.regra_versao
       or v_existente.carta_fingerprint is distinct from v_comp.completude_fingerprint_sha256
       or v_existente.formula_fingerprint is distinct from v_formula_fingerprint
       or v_existente.motor_versao is distinct from p_resultado->>'motor_versao' then
      raise exception 'resultado recusado: colisao de fingerprint com conteudo diferente';
    end if;
    v_bonus_id := v_existente.id;
    v_repeticao := true;
  else
    insert into clube_novo.build_bonificador(
      bonus_pe,bonus_fisico_total,bonus_fisico_detalhe,bonus_posicao,
      bonus_playstyle_1,bonus_playstyle_2,bonus_ia,bonus_outros,bonus_total,
      contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,
      formula_fingerprint,resultado_fingerprint,motor_versao
    ) values (
      v_bonus_pe,v_bonus_fisico_total,p_resultado->'bonus_fisico_detalhe',v_bonus_posicao,
      v_bonus_playstyle_1,v_bonus_playstyle_2,v_bonus_ia,p_resultado->'bonus_outros',v_bonus_total,
      v_contrato_versao,v_contrato_fingerprint,
      v_comp.regra_versao,v_comp.completude_fingerprint_sha256,
      v_formula_fingerprint,v_resultado_fingerprint,p_resultado->>'motor_versao'
    )
    returning id into v_bonus_id;
  end if;

  if v_linha.estado <> 'pendente'
     and (not v_repeticao or v_linha.build_bonificador_id is distinct from v_bonus_id) then
    raise exception 'resultado recusado: linha % esta em estado % e nao e repeticao identica',
      v_linha.id,v_linha.estado;
  end if;

  select l.id into v_ligacao
  from clube_novo.build_linha_card l
  where l.build_bonificador_id=v_bonus_id and l.id<>v_linha.id;
  if v_ligacao is not null then
    raise exception 'resultado recusado: build_bonificador % ja esta ligada a linha %',
      v_bonus_id,v_ligacao;
  end if;

  if v_linha.build_bonificador_id is null then
    update clube_novo.build_linha_card
    set build_bonificador_id=v_bonus_id,
        bonificador_motor_versao=p_resultado->>'motor_versao',
        bonificador_contrato_versao=v_contrato_versao,
        snapshot_bonificador_fingerprint=v_resultado_fingerprint
    where id=v_linha.id;
  elsif v_linha.build_bonificador_id is distinct from v_bonus_id then
    raise exception 'resultado recusado: linha % ja possui outro resultado do Bonificador',v_linha.id;
  elsif v_linha.bonificador_motor_versao is distinct from p_resultado->>'motor_versao'
     or v_linha.bonificador_contrato_versao is distinct from v_contrato_versao
     or v_linha.snapshot_bonificador_fingerprint is distinct from v_resultado_fingerprint then
    raise exception 'resultado recusado: ligacao idempotente existe, mas seus selos divergem';
  end if;

  if not exists (
    select 1
    from clube_novo.build_linha_card l
    join clube_novo.build_bonificador b on b.id=l.build_bonificador_id
    join clube_novo.carta_completude_motor_versao c
      on c.card_id=l.card_id and c.vigente and c.apto_motor
    where l.id=v_linha.id
      and b.id=v_bonus_id
      and b.resultado_fingerprint=v_resultado_fingerprint
      and b.carta_versao=c.regra_versao
      and b.carta_fingerprint=c.completude_fingerprint_sha256
      and l.carta_versao=c.regra_versao
      and l.carta_fingerprint=c.completude_fingerprint_sha256
      and l.snapshot_bonificador_fingerprint=b.resultado_fingerprint
  ) then
    raise exception 'readback transacional falhou; a transacao inteira sera revertida';
  end if;

  return jsonb_build_object(
    'gravado',not v_repeticao,
    'idempotente',v_repeticao,
    'build_linha_card_id',v_linha.id,
    'build_bonificador_id',v_bonus_id,
    'resultado_fingerprint',v_resultado_fingerprint,
    'carta_versao',v_comp.regra_versao,
    'carta_fingerprint',v_comp.completude_fingerprint_sha256,
    'contrato_versao',v_contrato_versao,
    'contrato_fingerprint',v_contrato_fingerprint,
    'formula_fingerprint',v_formula_fingerprint,
    'readback','ok'
  );
exception
  when invalid_text_representation or numeric_value_out_of_range then
    raise exception 'resultado recusado: id ou valor numerico fora do formato esperado'
      using errcode='22023';
end
$function$;

alter function public.gravar_build_bonificador_v1(jsonb) owner to postgres;

revoke all on function public.gravar_build_bonificador_v1(jsonb)
  from public, anon, authenticated;
grant execute on function public.gravar_build_bonificador_v1(jsonb)
  to service_role;

comment on function public.gravar_build_bonificador_v1(jsonb) is
  'Writer privado e transacional do Bonificador V1. Exige completude vigente/apta, sela resultado em clube_novo e nao interfere na publicacao.';
comment on function public.bonificador_contexto_escrita_v2(integer,integer) is
  'Contexto privado de escrita: entrega identidade da linha e selos atuais sem expor tabelas.';

do $readback_instalacao$
declare
  v_def text;
begin
  select pg_get_functiondef('public.gravar_build_bonificador_v1(jsonb)'::regprocedure)
    into v_def;
  if v_def not ilike '%SECURITY DEFINER%'
     or v_def not ilike '%SET search_path TO%'
     or v_def ilike '%clube.build%'
     or v_def ilike '%clube.fila%' then
    raise exception 'readback: definicao, search_path ou isolamento do writer ficaram incorretos';
  end if;
  if (select pg_get_userbyid(p.proowner)
      from pg_proc p
      where p.oid='public.gravar_build_bonificador_v1(jsonb)'::regprocedure)
     <> 'postgres' then
    raise exception 'readback: owner do writer nao e postgres';
  end if;
  if (select pg_get_userbyid(p.proowner)
      from pg_proc p
      where p.oid='public.bonificador_contexto_escrita_v2(integer,integer)'::regprocedure)
     <> 'postgres' then
    raise exception 'readback: owner do contexto nao e postgres';
  end if;
  if not has_function_privilege('service_role',
       'public.gravar_build_bonificador_v1(jsonb)','EXECUTE')
     or has_function_privilege('anon',
       'public.gravar_build_bonificador_v1(jsonb)','EXECUTE')
     or has_function_privilege('authenticated',
       'public.gravar_build_bonificador_v1(jsonb)','EXECUTE') then
    raise exception 'readback: privilegios do writer ficaram incorretos';
  end if;
  if not has_function_privilege('service_role',
       'public.bonificador_contexto_escrita_v2(integer,integer)','EXECUTE')
     or has_function_privilege('anon',
       'public.bonificador_contexto_escrita_v2(integer,integer)','EXECUTE')
     or has_function_privilege('authenticated',
       'public.bonificador_contexto_escrita_v2(integer,integer)','EXECUTE') then
    raise exception 'readback: privilegios do contexto ficaram incorretos';
  end if;
end
$readback_instalacao$;

commit;
