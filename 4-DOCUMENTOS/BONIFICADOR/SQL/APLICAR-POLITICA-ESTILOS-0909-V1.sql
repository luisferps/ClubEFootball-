-- Decisao aprovada por Luis em 09/09/2026. Persistencia e calculadora de conferencia.
-- Nao altera consumidores V11, fila, snapshots, cartas ou publicacoes.
begin;
select pg_advisory_xact_lock(hashtextextended('politica_estilos_20260909_v1',0));

create table if not exists clube_novo.bonificador_politica_estilo (
  versao text primary key,
  aprovada_em date not null,
  registrada_em timestamptz not null default now(),
  documento text not null,
  estado text not null check (estado in ('aprovada_implantacao_pendente','ativa','substituida')),
  politica jsonb not null check (jsonb_typeof(politica)='object'),
  politica_fingerprint text not null,
  check (politica_fingerprint=encode(extensions.digest(politica::text,'sha256'),'hex'))
);
alter table clube_novo.bonificador_politica_estilo enable row level security;
revoke all on clube_novo.bonificador_politica_estilo from public,anon,authenticated,service_role;
grant select on clube_novo.bonificador_politica_estilo to service_role;
comment on table clube_novo.bonificador_politica_estilo is
'Decisoes aprovadas de bonus de estilo. Estado pendente nao significa motor ou publicacao migrados. Politica imutavel por versao; nova decisao exige nova versao.';

do $registro$
declare
  v_politica jsonb := $json${
    "versao":"estilos-funcao-20260909-v1",
    "principal_por":"funcao_id",
    "ativacao_por":"posicao_escolhida_id",
    "fonte_ativacao":"clube_novo.bonificador_regra_playstyle.da_bonus",
    "pontos":{"principal":1.0,"secundario":0.5,"teto":1.5},
    "basico_id":256,
    "basico_pontua":false,
    "inativo_pontua":false,
    "promocao_generica_secundario":false,
    "principal_por_funcao":{
      "1":"ataque","2":"ataque","3":"ataque","4":"defesa","5":"defesa",
      "6":"defesa","7":"ataque","8":"ataque","9":"ataque","10":"ataque",
      "11":"ataque","12":"ataque","13":"ataque","14":"ataque","15":"ataque",
      "16":"ataque","17":"defesa","18":"defesa","19":"defesa"
    },
    "excecoes":[
      {"playstyle_id":271,"funcoes":[18,19],"posicoes":[1],"valor_unico_ativo":1.0},
      {"playstyle_id":268,"funcoes":[6],"posicoes":[2,3],"valor_unico_ativo":1.0}
    ],
    "pendentes_ativacao":[87,95,96,34],
    "tratamento_pendentes":"aguardar_definicao_do_jogo_em_extracao_futura_sem_inferir_posicoes",
    "normalizacao_slots":"usar_ataque_defesa_efetivos_do_jogo_nao_ordem_fisica_dos_campos",
    "motor_otimizador_alterado":false,
    "outros_bonus_alterados":false
  }$json$::jsonb;
begin
  if (select count(*) from jsonb_object_keys(v_politica->'principal_por_funcao'))<>19
     or exists (select 1 from jsonb_object_keys(v_politica->'principal_por_funcao') k
       where not exists (select 1 from clube_novo.funcao_sistema f where f.id=k::bigint and f.ativa)) then
    raise exception 'Classificacao deve cobrir as 19 funcoes existentes';
  end if;
  if exists (select 1 from clube_novo.bonificador_politica_estilo
       where versao='estilos-funcao-20260909-v1' and politica<>v_politica) then
    raise exception 'Versao ja registrada com outra regra. Nao sobrescrever decisao aprovada.';
  end if;
  insert into clube_novo.bonificador_politica_estilo
    (versao,aprovada_em,documento,estado,politica,politica_fingerprint)
  values ('estilos-funcao-20260909-v1','2026-09-09',
    '4-DOCUMENTOS/BONIFICADOR/REGRA-ESTILOS-APROVADA-0909.md',
    'aprovada_implantacao_pendente',v_politica,
    encode(extensions.digest(v_politica::text,'sha256'),'hex'))
  on conflict (versao) do nothing;
end;
$registro$;

create or replace function clube_novo.proteger_politica_estilo_v1()
returns trigger language plpgsql set search_path='' as $fn$
begin
  if tg_op in ('DELETE','TRUNCATE') then
    raise exception 'Preserve o historico das decisoes de estilo; registre nova versao.';
  end if;
  if new.versao is distinct from old.versao
     or new.politica is distinct from old.politica
     or new.politica_fingerprint is distinct from old.politica_fingerprint
     or new.aprovada_em is distinct from old.aprovada_em then
    raise exception 'Politica de estilo imutavel por versao; nova decisao exige nova versao.';
  end if;
  return new;
end;
$fn$;
revoke all on function clube_novo.proteger_politica_estilo_v1() from public,anon,authenticated,service_role;
drop trigger if exists proteger_politica_estilo_linha on clube_novo.bonificador_politica_estilo;
create trigger proteger_politica_estilo_linha before update or delete
on clube_novo.bonificador_politica_estilo for each row execute function clube_novo.proteger_politica_estilo_v1();
drop trigger if exists proteger_politica_estilo_truncate on clube_novo.bonificador_politica_estilo;
create trigger proteger_politica_estilo_truncate before truncate
on clube_novo.bonificador_politica_estilo for each statement execute function clube_novo.proteger_politica_estilo_v1();

create or replace function clube_novo.conferir_bonus_estilo_0909_v1(
  p_funcao_id bigint,p_posicao_id integer,p_estilo_ataque integer,p_estilo_defesa integer
) returns jsonb language plpgsql stable security invoker set search_path='' as $fn$
declare
  v_registro clube_novo.bonificador_politica_estilo%rowtype;
  v_p jsonb;
  v_principal text;
  v_a boolean;
  v_d boolean;
  v_ba numeric:=0;
  v_bd numeric:=0;
  v_e jsonb;
  v_aplicada integer;
  v_id integer;
begin
  select * into strict v_registro from clube_novo.bonificador_politica_estilo
    where versao='estilos-funcao-20260909-v1';
  v_p:=v_registro.politica;
  v_principal:=v_p->'principal_por_funcao'->>p_funcao_id::text;
  if v_principal is null then raise exception 'Funcao sem classificacao aprovada: %',p_funcao_id; end if;
  if p_posicao_id is null or not exists(select 1 from clube_novo.posicao_jogo where id=p_posicao_id) then
    raise exception 'Posicao invalida: %',p_posicao_id;
  end if;
  if p_estilo_ataque is null or p_estilo_defesa is null then
    raise exception 'Estilo ausente nao significa Basico: informe os dois estilos efetivos do jogo.';
  end if;
  foreach v_id in array array[p_estilo_ataque,p_estilo_defesa] loop
    if not exists(select 1 from clube_novo.playstyle where id_jogo=v_id) then
      raise exception 'Estilo desconhecido: %',v_id;
    end if;
    if (v_p->'pendentes_ativacao') @> jsonb_build_array(v_id) then
      return jsonb_build_object('pode_calcular',false,'pendencia','ativacao_sem_definicao',
        'playstyle_id',v_id,'versao',v_registro.versao,'politica_fingerprint',v_registro.politica_fingerprint);
    end if;
  end loop;
  -- Bits 6-7 do ID fisico: 0 ataque, 1 defesa, 2 ambos; Basico e especial.
  if (p_estilo_ataque<>256 and ((p_estilo_ataque>>6)&3) not in (0,2))
     or (p_estilo_defesa<>256 and ((p_estilo_defesa>>6)&3) not in (1,2)) then
    raise exception 'Slots semanticos incorretos: resolver ataque/defesa efetivos antes da bonificacao.';
  end if;
  select p_estilo_ataque<>256 and exists(select 1 from clube_novo.bonificador_regra_playstyle
      where playstyle_id=p_estilo_ataque and posicao_id=p_posicao_id and da_bonus) into v_a;
  select p_estilo_defesa<>256 and exists(select 1 from clube_novo.bonificador_regra_playstyle
      where playstyle_id=p_estilo_defesa and posicao_id=p_posicao_id and da_bonus) into v_d;
  if v_a then v_ba:=(v_p->'pontos'->>(case when v_principal='ataque' then 'principal' else 'secundario' end))::numeric; end if;
  if v_d then v_bd:=(v_p->'pontos'->>(case when v_principal='defesa' then 'principal' else 'secundario' end))::numeric; end if;
  if v_a and not v_d then
    for v_e in select value from jsonb_array_elements(v_p->'excecoes') loop
      if (v_e->>'playstyle_id')::integer=p_estilo_ataque
         and (v_e->'funcoes') @> jsonb_build_array(p_funcao_id)
         and (v_e->'posicoes') @> jsonb_build_array(p_posicao_id) then
        v_ba:=(v_e->>'valor_unico_ativo')::numeric;
        v_aplicada:=p_estilo_ataque;
      end if;
    end loop;
  end if;
  return jsonb_build_object('pode_calcular',true,'versao',v_registro.versao,
    'politica_fingerprint',v_registro.politica_fingerprint,'estado',v_registro.estado,
    'principal',v_principal,'ataque_ativo',v_a,'defesa_ativa',v_d,
    'bonus_ataque',v_ba,'bonus_defesa',v_bd,
    'bonus_total',least(v_ba+v_bd,(v_p->'pontos'->>'teto')::numeric),
    'excecao_aplicada',v_aplicada);
end;
$fn$;
revoke all on function clube_novo.conferir_bonus_estilo_0909_v1(bigint,integer,integer,integer)
  from public,anon,authenticated,service_role;
comment on function clube_novo.conferir_bonus_estilo_0909_v1(bigint,integer,integer,integer) is
'Calculadora interna de conferencia da decisao 09/09. Recebe estilos semanticos ataque/defesa. Nao escreve resultados e nao e chamada pela producao V11.';

-- A guarda do consumidor V11 precisa continuar intacta.
do $conservacao$
begin
  if not coalesce((public.bonificador_regua_v3()->>'pode_rodar')::boolean,false) then
    raise exception 'Regua operacional ficou inapta: abortando registro da decisao.';
  end if;
end;
$conservacao$;
commit;
