
create table if not exists clube_novo.contrato_leitura_nivel_runtime_v1 (
 contrato_id text primary key,
 executavel_versao text not null,
 executavel_sha256 text not null unique check(executavel_sha256 ~ '^[0-9a-f]{64}$'),
 leitor_versao text not null,
 fonte text not null check(fonte in ('memoria_jogo','efhub','tipo_carta_fisico')),
 layout jsonb not null,
 prova text not null,
 ativo boolean not null default true,
 atualizado_em timestamptz not null default clock_timestamp()
);
create table if not exists clube_novo.contrato_leitura_campo_runtime_v1 (
 contrato_id text not null references clube_novo.contrato_leitura_nivel_runtime_v1(contrato_id),
 chave_campo text not null,
 byte_offset integer,
 bit_inicio integer,
 largura_bits integer,
 tipo_leitura text not null,
 transformacao jsonb not null,
 destino text not null,
 prova text not null,
 primary key(contrato_id,chave_campo)
);
create table if not exists clube_novo.nivel_runtime_captura_v1 (
 captura_id uuid primary key,
 contrato_id text not null references clube_novo.contrato_leitura_nivel_runtime_v1(contrato_id),
 executavel_sha256 text not null,
 executavel_versao text not null,
 leitor_versao text not null,
 capturado_em timestamptz not null,
 recebido_em timestamptz not null default clock_timestamp(),
 quantidade integer not null,
 manifesto_sha256 text not null,
 prova_json jsonb not null
);
create table if not exists clube_novo.carta_nivel_evidencia_v1 (
 card_id text primary key references clube_novo.carta_jogo(card_id),
 nivel_maximo integer not null check(nivel_maximo>=1),
 orcamento_real integer not null check(orcamento_real=2*nivel_maximo-2),
 fonte text not null check(fonte in ('memoria_jogo','efhub','tipo_carta_fisico')),
 contrato_id text not null references clube_novo.contrato_leitura_nivel_runtime_v1(contrato_id),
 captura_id uuid not null references clube_novo.nivel_runtime_captura_v1(captura_id),
 prova_json jsonb not null,
 comprovado_em timestamptz not null,
 atualizado_em timestamptz not null default clock_timestamp()
);
create table if not exists clube_novo.carta_nivel_historico_v1 (
 captura_id uuid not null references clube_novo.nivel_runtime_captura_v1(captura_id),
 card_id text not null references clube_novo.carta_jogo(card_id),
 nivel_anterior integer,
 orcamento_anterior integer,
 cap_estimado_anterior boolean,
 nivel_maximo integer not null,
 orcamento_real integer not null,
 prova_json jsonb not null,
 aplicado_em timestamptz not null default clock_timestamp(),
 primary key(captura_id,card_id)
);
alter table clube_novo.contrato_leitura_nivel_runtime_v1 enable row level security;
alter table clube_novo.contrato_leitura_campo_runtime_v1 enable row level security;
alter table clube_novo.nivel_runtime_captura_v1 enable row level security;
alter table clube_novo.carta_nivel_evidencia_v1 enable row level security;
alter table clube_novo.carta_nivel_historico_v1 enable row level security;
revoke all on clube_novo.contrato_leitura_nivel_runtime_v1,clube_novo.contrato_leitura_campo_runtime_v1,clube_novo.nivel_runtime_captura_v1,clube_novo.carta_nivel_evidencia_v1,clube_novo.carta_nivel_historico_v1 from public,anon,authenticated;
grant select on clube_novo.contrato_leitura_nivel_runtime_v1,clube_novo.contrato_leitura_campo_runtime_v1,clube_novo.nivel_runtime_captura_v1,clube_novo.carta_nivel_evidencia_v1,clube_novo.carta_nivel_historico_v1 to service_role;
insert into clube_novo.contrato_leitura_nivel_runtime_v1
(contrato_id,executavel_versao,executavel_sha256,leitor_versao,fonte,layout,prova)
values ('clubef-card-level-runtime-v1','6.0.0.0','a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4','card-level-runtime-v1','memoria_jogo',
'{"raiz_rva":"0x86c9fc0","raiz_cadeia":["deref","0x28","deref"],"proprias":{"offset":"0x08","stride":"0xf0","header_offsets":["0x00","0x08","0x10"]},"boxes":{"offset":"0x20","agent_stride":"0x238","listas":[{"nome":"pickup_list","offset":"0xe8","stride":"0xf8"},{"nome":"banner_a_pickup_list","offset":"0x200","stride":"0xf0"},{"nome":"banner_c_pickup_list","offset":"0x218","stride":"0xf0"}]},"decodificador":{"tipo":"xor_u32","mascara_rva":"0x8686608","persistir_mascara":false},"formula":"2 * nivel_maximo - 2","cobertura":"somente_colecoes_carregadas","nivel_ausente":"nao_observado"}'::jsonb,
'Leitura física de 46 IDs em 2026-09-06; controles visuais Adriano34, Totti34, Shevchenko32, Hicky52/102 e Vitinha1/0. Campo do objeto convertido em RAM, não Player.bin.')
on conflict(contrato_id) do update set layout=excluded.layout,prova=excluded.prova,atualizado_em=clock_timestamp();
insert into clube_novo.contrato_leitura_campo_runtime_v1
(contrato_id,chave_campo,byte_offset,bit_inicio,largura_bits,tipo_leitura,transformacao,destino,prova)
values
('clubef-card-level-runtime-v1','card_id',8,64,64,'u64_le','{}','clube_novo.carta_jogo.card_id','Identidade física comum ao objeto e Player.bin.'),
('clubef-card-level-runtime-v1','nivel_atual',40,320,32,'xor_u32_le','{"decoder":"xor_u32","mask_rva":"0x8686608","persist_mask":false}','instancia_da_carta_apenas','Valor da instância; não substituir máximo cadastral.'),
('clubef-card-level-runtime-v1','nivel_maximo',44,352,32,'xor_u32_le','{"decoder":"xor_u32","mask_rva":"0x8686608","persist_mask":false}','clube_novo.carta_jogo.level_cap','Campo convertido observado em cartas próprias e boxes.'),
('clubef-card-level-runtime-v1','orcamento_maximo',null,null,null,'derivado','{"expression":"2 * nivel_maximo - 2","zero_valid_if_max":1}','clube_novo.carta_jogo.orcamento','Fórmula do jogo; Hicky52 gera102 pontos na prévia.')
on conflict(contrato_id,chave_campo) do update set byte_offset=excluded.byte_offset,bit_inicio=excluded.bit_inicio,largura_bits=excluded.largura_bits,tipo_leitura=excluded.tipo_leitura,transformacao=excluded.transformacao,destino=excluded.destino,prova=excluded.prova;

create or replace function public.extrator_contrato_niveis_runtime_v1()
returns jsonb language sql stable security definer set search_path='' as $fn$
 select jsonb_build_object('contrato',to_jsonb(c),'campos',
 (select jsonb_agg(to_jsonb(f) order by f.chave_campo) from clube_novo.contrato_leitura_campo_runtime_v1 f where f.contrato_id=c.contrato_id))
 from clube_novo.contrato_leitura_nivel_runtime_v1 c where c.ativo order by c.atualizado_em desc limit 1;
$fn$;
revoke all on function public.extrator_contrato_niveis_runtime_v1() from public,anon,authenticated;
grant execute on function public.extrator_contrato_niveis_runtime_v1() to service_role;

create or replace function clube_novo.tg_cap_do_id()
returns trigger language plpgsql set search_path='' as $fn$
declare e clube_novo.carta_nivel_evidencia_v1%rowtype;
begin
 new.grupo_id := (new.card_id::numeric::bigint >> 38) & 255;
 if new.codigo_tipo_carta_fisico=3 then
   new.level_cap:=1; new.orcamento:=0; new.cap_estimado:=false;
   return new;
 end if;
 select * into e from clube_novo.carta_nivel_evidencia_v1 where card_id=new.card_id;
 if found then
   new.level_cap:=e.nivel_maximo; new.orcamento:=e.orcamento_real; new.cap_estimado:=false;
 elsif new.level_cap is null then
   new.orcamento:=null; new.cap_estimado:=true;
 else
   -- Valores históricos sem evidência continuam identificáveis; nenhuma inferência por ID/moda.
   new.orcamento:=greatest(0,2*new.level_cap-2);
 end if;
 return new;
end;
$fn$;

create or replace function public.extrator_aplicar_niveis_runtime_v1(p_captura jsonb,p_cartas jsonb)
returns jsonb language plpgsql security definer set search_path='' as $fn$
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
 if exists(select 1 from jsonb_array_elements(p_cartas)x join clube_novo.carta_nivel_evidencia_v1 e on e.card_id=x->>'card_id'
   where e.comprovado_em>v_instante or (e.comprovado_em=v_instante and e.nivel_maximo<>(x->>'nivel_maximo')::integer)) then
   raise exception 'nivel_runtime: captura antiga ou conflitante'; end if;
 v_manifesto:=encode(extensions.digest(convert_to(jsonb_build_object('captura',p_captura,'cartas',p_cartas)::text,'UTF8'),'sha256'),'hex');
 perform pg_advisory_xact_lock(hashtextextended('clubef-nivel-runtime-aplicar',0));
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
$fn$;
revoke all on function public.extrator_aplicar_niveis_runtime_v1(jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.extrator_aplicar_niveis_runtime_v1(jsonb,jsonb) to service_role;
comment on table clube_novo.carta_nivel_evidencia_v1 is 'Nível máximo físico observado por ID. Ausência não é nível1. Orçamento é 2*max-2; fontes de sessão versionadas.';
notify pgrst,'reload schema';

-- Ampliação V2 validada por referência do conversor e leitura estável de cabeçalho.
update clube_novo.contrato_leitura_nivel_runtime_v1 set leitor_versao='card-level-runtime-v2',
 layout=layout||'{"lista_recrutamento":{"offset":"0x380","stride":"0xf0","total_offset":"0x398","indice_inicial_offset":"0x3d4","tamanho_pagina_offset":"0x3d0","tipo_contadores":"u32_le"}}'::jsonb,
 atualizado_em=clock_timestamp() where contrato_id='clubef-card-level-runtime-v1';
insert into clube_novo.contrato_leitura_campo_runtime_v1(contrato_id,chave_campo,byte_offset,bit_inicio,largura_bits,tipo_leitura,transformacao,destino,prova)
values
('clubef-card-level-runtime-v1','recrutamento_total_reportado',920,7360,32,'u32_le','{"relative_to":"B=[A+0x20]","meaning":"total_reportado_na_resposta"}','coleta.cobertura','StandardDraft144677c40 grava total em B+0x398; não é nível de carta.'),
('clubef-card-level-runtime-v1','recrutamento_indice_inicial',980,7840,32,'u32_le','{"relative_to":"B=[A+0x20]","meaning":"indice_da_pagina"}','coleta.cobertura','Índice de paginação em B+0x3d4; não inferir total carregado.')
on conflict(contrato_id,chave_campo) do nothing;
