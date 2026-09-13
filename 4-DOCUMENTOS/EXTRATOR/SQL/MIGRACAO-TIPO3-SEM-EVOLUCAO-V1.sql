-- Contrato definitivo para cartas de tipo fisico 3 (Em destaque / Em evidencia).
-- Essas cartas chegam prontas: nivel maximo 1, orcamento 0, sem progressao.
-- O eFHUB permanece guardado como referencia bruta, mas nao pode sobrescrever
-- essa regra cadastral. A migracao tambem prepara as linhas afetadas para nova
-- execucao e mantem a publicacao antiga somente ate a substituicao atomica.

begin;

alter table clube_novo.contrato_leitura_nivel_runtime_v1
  drop constraint if exists contrato_leitura_nivel_runtime_v1_fonte_check;
alter table clube_novo.contrato_leitura_nivel_runtime_v1
  add constraint contrato_leitura_nivel_runtime_v1_fonte_check
  check (fonte in ('memoria_jogo','efhub','tipo_carta_fisico'));

alter table clube_novo.carta_nivel_evidencia_v1
  drop constraint if exists carta_nivel_evidencia_v1_fonte_check;
alter table clube_novo.carta_nivel_evidencia_v1
  add constraint carta_nivel_evidencia_v1_fonte_check
  check (fonte in ('memoria_jogo','efhub','tipo_carta_fisico'));

insert into clube_novo.contrato_leitura_nivel_runtime_v1
  (contrato_id,executavel_versao,executavel_sha256,leitor_versao,fonte,layout,prova,ativo)
values
  ('clubef-player-type3-sem-evolucao-v1','dt870-2026-atualizacao',
   '2afe17a686bef320dce3c4096355ba99b56bfb8a42b08018f0ae2fe444b05853',
   'player-type3-sem-evolucao-v1','tipo_carta_fisico',
   '{"arquivo":"Player.bin","registro_bytes":400,"card_id":{"offset":8,"tipo":"u64_le"},"codigo_tipo_carta_fisico":{"origem":"card_id","bits":[44,47],"valor_sem_evolucao":3},"marcador_subtipo_tipo_carta":{"bit":104,"largura":1},"regra":{"level_cap":1,"orcamento":0,"aceita_progressao":false}}'::jsonb,
   'Tipo fisico 3 identifica Em destaque/Em evidencia. Auditoria integral: 3.524 cartas; 3.498 ja estavam 1/0 e 26 respostas eFHUB divergentes foram corrigidas pela regra confirmada no jogo.',
   false)
on conflict (contrato_id) do update set
  executavel_versao=excluded.executavel_versao,
  executavel_sha256=excluded.executavel_sha256,
  leitor_versao=excluded.leitor_versao,
  fonte=excluded.fonte,
  layout=excluded.layout,
  prova=excluded.prova,
  ativo=false,
  atualizado_em=clock_timestamp();

alter table clube_novo.carta_jogo
  add column if not exists sem_evolucao boolean
  generated always as (coalesce(level_cap=1 and orcamento=0,false)) stored;
alter table clube_novo.carta_jogo alter column sem_evolucao set not null;

create index if not exists carta_jogo_sem_evolucao_overall_idx
  on clube_novo.carta_jogo(sem_evolucao,overall desc,card_id);

create or replace function clube_novo.tg_cap_do_id()
returns trigger language plpgsql set search_path='' as $fn$
declare e clube_novo.carta_nivel_evidencia_v1%rowtype;
begin
 new.grupo_id := (new.card_id::numeric::bigint >> 38) & 255;
 if new.codigo_tipo_carta_fisico=3 then
   new.level_cap:=1;
   new.orcamento:=0;
   new.cap_estimado:=false;
   return new;
 end if;
 select * into e from clube_novo.carta_nivel_evidencia_v1 where card_id=new.card_id;
 if found then
   new.level_cap:=e.nivel_maximo; new.orcamento:=e.orcamento_real; new.cap_estimado:=false;
 elsif new.level_cap is null then
   new.orcamento:=null; new.cap_estimado:=true;
 else
   new.orcamento:=greatest(0,2*new.level_cap-2);
 end if;
 return new;
end;
$fn$;

create or replace function clube_novo.tg_evidencia_tipo3_sem_evolucao_v1()
returns trigger language plpgsql set search_path='' as $fn$
declare v_captura uuid; v_tipo smallint; v_original jsonb;
begin
 select codigo_tipo_carta_fisico into v_tipo
 from clube_novo.carta_jogo where card_id=new.card_id;
 if v_tipo=3 then
   select captura_id into v_captura
   from clube_novo.nivel_runtime_captura_v1
   where contrato_id='clubef-player-type3-sem-evolucao-v1'
   order by capturado_em desc limit 1;
   if v_captura is null then
     raise exception 'tipo3_sem_evolucao: captura de contrato ausente';
   end if;
   v_original:=jsonb_build_object(
     'fonte_recebida',new.fonte,
     'nivel_recebido',new.nivel_maximo,
     'orcamento_recebido',new.orcamento_real,
     'captura_recebida',new.captura_id
   );
   new.nivel_maximo:=1;
   new.orcamento_real:=0;
   new.fonte:='tipo_carta_fisico';
   new.contrato_id:='clubef-player-type3-sem-evolucao-v1';
   new.captura_id:=v_captura;
   new.prova_json:=coalesce(new.prova_json,'{}'::jsonb)||
     jsonb_build_object('regra_tipo3_sem_evolucao',true,'entrada_original',v_original);
 end if;
 return new;
end;
$fn$;

drop trigger if exists carta_nivel_evidencia_tipo3_sem_evolucao_v1
  on clube_novo.carta_nivel_evidencia_v1;
create trigger carta_nivel_evidencia_tipo3_sem_evolucao_v1
before insert or update of nivel_maximo,orcamento_real,fonte,contrato_id,captura_id
on clube_novo.carta_nivel_evidencia_v1
for each row execute function clube_novo.tg_evidencia_tipo3_sem_evolucao_v1();

comment on column clube_novo.carta_jogo.sem_evolucao is
  'Verdadeiro quando a carta tem level_cap=1 e orcamento=0. Campo gerado; nao aceita divergencia manual.';

create or replace view clube_novo.otimizador_prioridade_orcamento_v1
with (security_barrier=true)
as
select c.card_id,c.overall,e.nivel_maximo,e.orcamento_real,e.captura_id,
       case when c.tipo_carta_id='player_type_0_subtype_0' and c.codigo_tipo_carta_fisico=0 then 3
            when c.codigo_tipo_carta_fisico in (1,3,4,5,6,7) and not c.sem_evolucao then 1
            when c.codigo_tipo_carta_fisico in (1,3,4,5,6,7) and c.sem_evolucao then 2 end as prioridade_grupo
from clube_novo.carta_jogo c
join clube_novo.carta_nivel_evidencia_v1 e on e.card_id=c.card_id
where e.nivel_maximo>=1 and e.orcamento_real=2*(e.nivel_maximo-1)
  and c.tipo_carta_id<>'player_delete_list';
revoke all on clube_novo.otimizador_prioridade_orcamento_v1 from public,anon,authenticated;
grant select on clube_novo.otimizador_prioridade_orcamento_v1 to service_role;

create or replace view clube_novo.carta_nivel_pendente_v1
with (security_barrier=true)
as
select c.card_id,c.nome,c.tipo,c.overall,c.level_cap as nivel_cadastral_nao_comprovado,
       'nivel_maximo_nao_coletado'::text as motivo
from clube_novo.carta_jogo c
where c.tipo_carta_id<>'player_delete_list'
  and c.roda_motor is not false
  and (
    c.codigo_tipo_carta_fisico=any(array[1,4,5,6,7])
    or (c.codigo_tipo_carta_fisico=0 and c.tipo_carta_id='player_type_0_subtype_0')
  )
  and not exists(select 1 from clube_novo.carta_nivel_evidencia_v1 e where e.card_id=c.card_id);
revoke all on clube_novo.carta_nivel_pendente_v1 from public,anon,authenticated;
grant select on clube_novo.carta_nivel_pendente_v1 to service_role;

-- O planejador deixa de consultar o eFHUB para tipo 3. O tipo fisico ja
-- determina 1/0 e uma resposta externa divergente nao e dado de progressao.
do $fn$
declare v_def text;
begin
 select pg_get_functiondef(p.oid) into v_def
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='extrator_efhub_planejar_lote_v1';
 v_def:=replace(v_def,'ARRAY[1, 3, 4, 5, 6, 7]','ARRAY[1, 4, 5, 6, 7]');
 v_def:=replace(v_def,'array[1,3,4,5,6,7]','array[1,4,5,6,7]');
 execute v_def;

 select pg_get_functiondef(p.oid) into v_def
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname='extrator_efhub_aplicar_lote_v1';
 v_def:=replace(v_def,'v_e.fonte = ''memoria_jogo''::text',
   'v_e.fonte = ANY (ARRAY[''memoria_jogo''::text, ''tipo_carta_fisico''::text])');
 v_def:=replace(v_def,'v_e.fonte=''memoria_jogo''',
   'v_e.fonte=any(array[''memoria_jogo'',''tipo_carta_fisico''])');
 v_def:=replace(v_def,'v_e.fonte <> ''memoria_jogo''::text',
   'NOT (v_e.fonte = ANY (ARRAY[''memoria_jogo''::text, ''tipo_carta_fisico''::text]))');
 v_def:=replace(v_def,'v_e.fonte<>''memoria_jogo''',
   'not (v_e.fonte=any(array[''memoria_jogo'',''tipo_carta_fisico'']))');
 execute v_def;
end $fn$;

create or replace function public.otimizador_manter_publicacao_ate_substituicao_v1(p_linhas bigint[])
returns jsonb language plpgsql security definer set search_path='' as $fn$
declare v_id bigint; v_r clube_novo.orcamento_revisao_linha_v1%rowtype;
 v_total integer:=0; v_invalidadas integer:=0; v_mantidas integer:=0;
begin
 if coalesce(cardinality(p_linhas),0) not between 1 and 1000
    or cardinality(p_linhas)<>(select count(distinct x) from unnest(p_linhas)x)
 then raise exception 'substituicao: lista de linhas revisadas obrigatoria'; end if;
 perform pg_advisory_xact_lock(hashtextextended('orcamento-substituicao-sem-interrupcao-v1',0));
 foreach v_id in array p_linhas loop
   select * into v_r from clube_novo.orcamento_revisao_linha_v1
   where linha_anterior_id=v_id for update;
   if not found or v_r.linha_nova_id is null then
     raise exception 'substituicao: linha % sem revisao pronta',v_id;
   end if;
   if exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=v_id) then
     update clube_novo.orcamento_revisao_linha_v1
       set estado='aguardando_substituicao'
       where linha_anterior_id=v_id;
     v_mantidas:=v_mantidas+1;
   else
     update clube_novo.build_linha_card set
       estado='invalida',
       estado_otimizador=case when estado_otimizador='pendente' then 'bloqueado' else estado_otimizador end,
       erro_otimizador=case when estado_otimizador='pendente' then 'entrada_substituida_por_revisao_sem_evolucao' else erro_otimizador end,
       pendencias=case when pendencias @> array['orcamento_invalido'] then pendencias else array_append(pendencias,'orcamento_invalido') end,
       atualizado_em=clock_timestamp()
     where id=v_id and estado_otimizador<>'processando';
     if not found then raise exception 'substituicao: linha % em processamento',v_id; end if;
     update clube_novo.orcamento_revisao_linha_v1 set estado='em_fila'
       where linha_anterior_id=v_id;
     v_invalidadas:=v_invalidadas+1;
   end if;
   v_total:=v_total+1;
 end loop;
 return jsonb_build_object('ok',true,'linhas',v_total,
   'linhas_antigas_invalidadas',v_invalidadas,
   'publicacoes_mantidas_ate_substituicao',v_mantidas,
   'publicacoes_retiradas',0);
end $fn$;
revoke all on function public.otimizador_manter_publicacao_ate_substituicao_v1(bigint[]) from public,anon,authenticated;
grant execute on function public.otimizador_manter_publicacao_ate_substituicao_v1(bigint[]) to service_role;

create or replace function clube_novo.tg_substituir_publicacao_revisao_orcamento_v1()
returns trigger language plpgsql set search_path='' as $fn$
declare v_r clube_novo.orcamento_revisao_linha_v1%rowtype;
begin
 select * into v_r from clube_novo.orcamento_revisao_linha_v1
 where linha_nova_id=new.linha_id for update;
 if not found then return new; end if;

 delete from clube_novo.build_publicacao_linha_ativa_v1
 where linha_id=v_r.linha_anterior_id and linha_id<>new.linha_id;
 delete from clube_novo.build_pontuacao_final_v2_delta_v1
 where linha_id=v_r.linha_anterior_id and linha_id<>new.linha_id;
 update clube_novo.build_linha_card set
   estado='invalida',
   estado_otimizador=case when estado_otimizador='pendente' then 'bloqueado' else estado_otimizador end,
   erro_otimizador=case when estado_otimizador='pendente' then 'entrada_substituida_por_revisao_sem_evolucao' else erro_otimizador end,
   pendencias=case when pendencias @> array['orcamento_invalido'] then pendencias else array_append(pendencias,'orcamento_invalido') end,
   publicada_em=null,publicacao_fingerprint=null,
   nota_contrato=null,nota_otimizador_resultado_fingerprint=null,
   nota_bonificador_resultado_fingerprint=null,nota_carta_fingerprint=null,
   nota_formula_fingerprint=null,nota_contrato_fingerprint=null,
   nota_bruta_selada=null,nota_bonus_pe=null,nota_bonus_fisico_total=null,
   nota_bonus_posicao=null,nota_bonus_playstyle_1=null,nota_bonus_playstyle_2=null,
   nota_bonus_ia=null,nota_bonus_outros=null,nota_bonus_total=null,
   nota_numerador=null,nota_denominador=null,nota_do_motor=null,nota_final=null,
   nota_normalizacao_fingerprint=null,nota_calculo_fingerprint=null,
   nota_publicacao_fingerprint_v1=null,nota_publicada_em_v1=null,
   nota_calculada_em=null,atualizado_em=clock_timestamp()
 where id=v_r.linha_anterior_id;
 update clube_novo.build_finalizacao_fila_v1 set
   estado='erro',motivo='resultado substituido por revisao sem evolucao; nova linha '||new.linha_id,
   proxima_tentativa_em='infinity'::timestamptz,publicacao_fingerprint=null,
   atualizado_em=clock_timestamp()
 where linha_id=v_r.linha_anterior_id;
 update clube_novo.orcamento_revisao_linha_v1 set estado='republicada'
 where linha_anterior_id=v_r.linha_anterior_id;
 return new;
end $fn$;

drop trigger if exists build_publicacao_substituir_revisao_orcamento_v1
  on clube_novo.build_publicacao_linha_ativa_v1;
create trigger build_publicacao_substituir_revisao_orcamento_v1
after insert or update of build_otimizador_id,build_bonificador_id,nota_final
on clube_novo.build_publicacao_linha_ativa_v1
for each row execute function clube_novo.tg_substituir_publicacao_revisao_orcamento_v1();

-- Registra uma captura categorial e corrige todas as cartas tipo 3. A resposta
-- eFHUB original continua intacta em efhub_nivel_atual_v1 para auditoria.
do $fn$
declare
 v_captura uuid:=gen_random_uuid();
 v_agora timestamptz:=clock_timestamp();
 v_quantidade integer;
 v_manifesto text;
 v_linhas bigint[];
 v_cartas_corretivas integer;
 v_lote_modelo uuid;
 v_lote_corretivo uuid:=gen_random_uuid();
 v_preparo jsonb;
 v_ativacao jsonb;
begin
 select count(*),encode(extensions.digest(convert_to(
   string_agg(card_id,',' order by card_id collate "C")||':tipo3:level1:orcamento0','UTF8'),'sha256'),'hex')
 into v_quantidade,v_manifesto
 from clube_novo.carta_jogo where codigo_tipo_carta_fisico=3;
 if v_quantidade=0 then raise exception 'tipo3_sem_evolucao: nenhuma carta encontrada'; end if;

 insert into clube_novo.nivel_runtime_captura_v1
   (captura_id,contrato_id,executavel_sha256,executavel_versao,leitor_versao,
    capturado_em,quantidade,manifesto_sha256,prova_json)
 values(v_captura,'clubef-player-type3-sem-evolucao-v1',
   '2afe17a686bef320dce3c4096355ba99b56bfb8a42b08018f0ae2fe444b05853',
   'dt870-2026-atualizacao','player-type3-sem-evolucao-v1',v_agora,
   v_quantidade,v_manifesto,
   jsonb_build_object('regra','codigo_tipo_carta_fisico=3','level_cap',1,
     'orcamento',0,'cartas',v_quantidade,'auditoria_1_0',3498,
     'divergencias_efhub_corrigidas',26));

 insert into clube_novo.carta_nivel_historico_v1
   (captura_id,card_id,nivel_anterior,orcamento_anterior,cap_estimado_anterior,
    nivel_maximo,orcamento_real,prova_json)
 select v_captura,c.card_id,c.level_cap,c.orcamento,c.cap_estimado,1,0,
   jsonb_build_object('codigo_tipo_carta_fisico',c.codigo_tipo_carta_fisico,
     'marcador_subtipo_tipo_carta',c.marcador_subtipo_tipo_carta,
     'efhub_bruto',(select jsonb_build_object('nivel_maximo',a.nivel_maximo,
       'orcamento_real',a.orcamento_real,'lote_id',a.lote_id)
       from clube_novo.efhub_nivel_atual_v1 a where a.card_id=c.card_id))
 from clube_novo.carta_jogo c where c.codigo_tipo_carta_fisico=3;

 insert into clube_novo.carta_nivel_evidencia_v1
   (card_id,nivel_maximo,orcamento_real,fonte,contrato_id,captura_id,prova_json,comprovado_em)
 select c.card_id,1,0,'tipo_carta_fisico','clubef-player-type3-sem-evolucao-v1',v_captura,
   jsonb_build_object('codigo_tipo_carta_fisico',3,
     'marcador_subtipo_tipo_carta',c.marcador_subtipo_tipo_carta,
     'aceita_progressao',false,
     'efhub_bruto',(select jsonb_build_object('nivel_maximo',a.nivel_maximo,
       'orcamento_real',a.orcamento_real,'lote_id',a.lote_id)
       from clube_novo.efhub_nivel_atual_v1 a where a.card_id=c.card_id)),v_agora
 from clube_novo.carta_jogo c where c.codigo_tipo_carta_fisico=3
 on conflict(card_id) do update set
   nivel_maximo=excluded.nivel_maximo,orcamento_real=excluded.orcamento_real,
   fonte=excluded.fonte,contrato_id=excluded.contrato_id,captura_id=excluded.captura_id,
   prova_json=excluded.prova_json,comprovado_em=excluded.comprovado_em,
   atualizado_em=clock_timestamp();

 update clube_novo.carta_jogo set level_cap=1,orcamento=0,cap_estimado=false
 where codigo_tipo_carta_fisico=3;

 select array_agg(b.id order by b.id),count(distinct b.card_id)::integer
 into v_linhas,v_cartas_corretivas
 from clube_novo.build_linha_card b
 join clube_novo.carta_jogo c on c.card_id=b.card_id
 join clube_novo.otimizador_lote_producao_carta_v3 s
   on s.lote_id=b.lote_producao_id and s.card_id=b.card_id
 where b.execucao_tipo='producao' and b.estado<>'invalida'
   and b.estado_otimizador<>'processando'
   and c.codigo_tipo_carta_fisico=3
   and (s.entrada_otimizador#>>'{escalares,orcamento}')::integer<>0
   and not exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r
     where r.linha_anterior_id=b.id);

 if coalesce(cardinality(v_linhas),0)>0 then
   if cardinality(v_linhas)>500 then
     raise exception 'tipo3_sem_evolucao: % linhas excedem o lote atomico de 500',cardinality(v_linhas);
   end if;
   select l.id into v_lote_modelo
   from clube_novo.otimizador_lote_producao_v3 l
   join clube_novo.build_linha_card b on b.lote_producao_id=l.id
   where b.id=any(v_linhas) and l.estado='pausado' and l.pode_publicar=false
   group by l.id,l.linhas,l.criado_em
   order by count(*) desc,l.criado_em desc limit 1;
   if v_lote_modelo is null then
     raise exception 'tipo3_sem_evolucao: lote modelo pausado ausente';
   end if;
   v_preparo:=public.otimizador_preparar_revisao_orcamento_v1(
     v_lote_modelo,v_lote_corretivo,v_linhas);
   v_ativacao:=public.otimizador_manter_publicacao_ate_substituicao_v1(v_linhas);
   insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
   values(v_lote_corretivo,'revisao_orcamento_preparada',
     jsonb_build_object('motivo','tipo3_sem_evolucao','captura_id',v_captura,'cartas',v_cartas_corretivas,
       'linhas',cardinality(v_linhas),'preparo',v_preparo,'ativacao',v_ativacao));
 end if;
end $fn$;

-- A atualização acima dispara triggers diferidas do cadastro. Fechar essa
-- transação antes de validar a constraint evita "pending trigger events".
commit;
begin;

alter table clube_novo.carta_jogo
  drop constraint if exists carta_jogo_tipo3_sem_evolucao_chk;
alter table clube_novo.carta_jogo
  add constraint carta_jogo_tipo3_sem_evolucao_chk
  check (codigo_tipo_carta_fisico<>3 or
    (level_cap=1 and orcamento=0 and cap_estimado=false)) not valid;
alter table clube_novo.carta_jogo validate constraint carta_jogo_tipo3_sem_evolucao_chk;

comment on table clube_novo.carta_nivel_evidencia_v1 is
  'Nivel maximo por ID. Memoria do jogo e regra do tipo fisico prevalecem sobre eFHUB; tipo fisico 3 e sempre nivel 1, orcamento 0.';
comment on view clube_novo.otimizador_prioridade_orcamento_v1 is
  'Fila: especiais que evoluem, cartas sem evolucao e base; dentro de cada bloco, overall decrescente.';

notify pgrst,'reload schema';
commit;
