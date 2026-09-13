-- Executor seletivo: resultados antigos imutaveis; fila original preservada.
create table clube_novo.correcao_estilos_execucao_v12(
 id text primary key check(id='estilos-funcao-20260909-v1'),
 criada_em timestamptz not null default clock_timestamp(),
 auditoria jsonb not null, concluida_em timestamptz
);
create table clube_novo.correcao_estilos_item_v12(
 linha_id bigint primary key references clube_novo.build_linha_card(id),
 antigo_id bigint not null references clube_novo.build_bonificador(id),
 novo_id bigint references clube_novo.build_bonificador(id),
 card_id text not null,funcao_id bigint not null,posicao_id integer not null,
 carta_fingerprint text not null,otimizador_id bigint,otimizador_fingerprint text,
 ataque integer not null,defesa integer not null,esperado jsonb not null,
 novo_1 numeric not null,novo_2 numeric not null,
 era_publicada boolean not null,nota_anterior numeric,
 publicacao_anterior jsonb,
 estado text not null default 'pendente' check(estado in('pendente','corrigida','concluida','erro')),
 erro text,corrigida_em timestamptz,concluida_em timestamptz,
 resultado_novo_fingerprint text unique
);
create index correcao_estilos_v12_pendentes on clube_novo.correcao_estilos_item_v12(estado,era_publicada desc,linha_id);
alter table clube_novo.correcao_estilos_execucao_v12 enable row level security;
alter table clube_novo.correcao_estilos_item_v12 enable row level security;
revoke all on clube_novo.correcao_estilos_execucao_v12,clube_novo.correcao_estilos_item_v12 from public,anon,authenticated,service_role;
grant select on clube_novo.correcao_estilos_execucao_v12,clube_novo.correcao_estilos_item_v12 to service_role;

create or replace function clube_novo.bonus_estilo_conforme_v12(
 p_bonus_id bigint,p_card_id text,p_funcao_id bigint,p_posicao_id integer)
returns boolean language plpgsql stable set search_path='' as $f$
declare b clube_novo.build_bonificador%rowtype; s jsonb; e jsonb;
begin
 select * into b from clube_novo.build_bonificador where id=p_bonus_id;
 if b.id is null or not (
  (b.motor_versao='v11-0709-estilo-posicao-oficial-v1' and b.formula_fingerprint='2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879' and b.contrato_versao='bonificador-regua-v3')
  or (b.motor_versao='v12-0909-estilo-funcao-ativacao-v1' and b.formula_fingerprint='4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8' and b.contrato_versao='bonificador-regua-v4')
 ) then return false; end if;
 s:=clube_novo.carta_estilos_efetivos_v12(p_card_id);
 if not coalesce((s->>'pode_rodar')::boolean,false) then return false; end if;
 e:=clube_novo.conferir_bonus_estilo_0909_v1(p_funcao_id,p_posicao_id,(s->>'ataque_id')::int,(s->>'defesa_id')::int);
 return coalesce((e->>'pode_calcular')::boolean,false)
  and b.bonus_playstyle_1 is not distinct from (e->>'bonus_ataque')::numeric
  and b.bonus_playstyle_2 is not distinct from (e->>'bonus_defesa')::numeric
  and b.b_estilo is not distinct from (e->>'bonus_total')::numeric;
end $f$;
revoke all on function clube_novo.bonus_estilo_conforme_v12(bigint,text,bigint,integer) from public,anon,authenticated;
grant execute on function clube_novo.bonus_estilo_conforme_v12(bigint,text,bigint,integer) to service_role;

create or replace function public.correcao_estilos_status_v12()
returns jsonb language sql stable security definer set search_path='' as $f$
select jsonb_build_object('contrato','correcao-estilos-v12',
 'preparada',exists(select 1 from clube_novo.correcao_estilos_execucao_v12),
 'total',count(*),'pendentes',count(*) filter(where estado='pendente'),
 'corrigidas',count(*) filter(where novo_id is not null),
 'publicacoes_total',count(*) filter(where era_publicada),
 'publicacoes_concluidas',count(*) filter(where era_publicada and estado='concluida'),
 'concluidas',count(*) filter(where estado='concluida'),
 'erros',count(*) filter(where estado='erro'),
 'ultimo_erro',(select jsonb_build_object('linha',linha_id,'erro',erro) from clube_novo.correcao_estilos_item_v12 where estado='erro' order by linha_id limit 1),
 'concluida_em',(select concluida_em from clube_novo.correcao_estilos_execucao_v12),
 'producao_geral_liberada',coalesce((public.bonificador_regua_v4()->>'liberado_para_producao')::boolean,false))
from clube_novo.correcao_estilos_item_v12;
$f$;
revoke all on function public.correcao_estilos_status_v12() from public,anon,authenticated;
grant execute on function public.correcao_estilos_status_v12() to service_role;

create or replace function public.correcao_estilos_tick_v12(
 p_limite integer default 250,p_linhas bigint[] default null)
returns jsonb language plpgsql security definer set search_path='' set statement_timeout='55s' as $f$
declare v_regua jsonb; v_n integer; v_publicadas integer:=0; r record; f jsonb;
 v_inicio timestamptz:=clock_timestamp(); v_erro text; v_lock boolean;
begin
 v_lock:=pg_try_advisory_xact_lock(hashtextextended('correcao-estilos-v12-executor',0));
 if not v_lock then return jsonb_build_object('ocupado',true); end if;
 if not exists(select 1 from clube_novo.correcao_estilos_execucao_v12) then raise exception 'auditoria nao preparada'; end if;
 if exists(select 1 from clube_novo.bonificador_correcao_item_v1 where estado_item='processando')
  or exists(select 1 from clube_novo.bonificador_correcao_lote_v1 where estado='rodando') then
  raise exception 'Bonificador geral em execucao; preserve a pausa durante a correcao seletiva';
 end if;
 if exists(select 1 from clube_novo.correcao_estilos_item_v12 where estado='erro') then return public.correcao_estilos_status_v12(); end if;
 v_regua:=public.bonificador_regua_v4();
 if v_regua->>'formula_fingerprint'<>'4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8'
  or not coalesce((v_regua->>'pode_rodar')::boolean,false) then raise exception 'regua V12 incompatível'; end if;
 perform set_config('clube_novo.correcao_estilos_v12','1',true);
 drop table if exists pg_temp._estilos_v12_batch;
 create temporary table _estilos_v12_batch on commit drop as
 select a.*,null::bigint criado_id
 from clube_novo.correcao_estilos_item_v12 a
 where a.estado='pendente' and (p_linhas is null or a.linha_id=any(p_linhas))
 order by a.era_publicada desc,a.linha_id
 limit least(greatest(coalesce(p_limite,250),1),500);
 get diagnostics v_n=row_count;
 if v_n>0 then
  perform 1 from clube_novo.build_linha_card l join _estilos_v12_batch a on a.linha_id=l.id order by l.id for update of l;
  if exists(select 1 from _estilos_v12_batch a join clube_novo.build_linha_card l on l.id=a.linha_id
   join clube_novo.build_bonificador b on b.id=a.antigo_id
   where l.estado<>'pendente' or l.card_id<>a.card_id or l.funcao_id<>a.funcao_id or l.posicao_id<>a.posicao_id
    or l.carta_fingerprint is distinct from a.carta_fingerprint
    or l.build_otimizador_id is distinct from a.otimizador_id
    or l.snapshot_otimizador_fingerprint is distinct from a.otimizador_fingerprint
    or b.carta_fingerprint is distinct from l.carta_fingerprint
    or b.entrada_bonificador_fingerprint is distinct from l.carta_fingerprint
    or b.carta_versao is distinct from l.carta_versao or coalesce(cardinality(b.faltou),-1)<>0
    or b.motor_versao<>'v11-0709-estilo-posicao-oficial-v1'
    or b.formula_fingerprint<>'2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879'
    or (l.build_bonificador_id is distinct from a.antigo_id and not exists(
     select 1 from clube_novo.bonificador_correcao_item_v1 i
     where i.build_linha_card_id=l.id and i.estado_item='preparado' and i.build_bonificador_id_novo=a.antigo_id))
    or exists(select 1 from clube_novo.orcamento_revisao_linha_v1 x where x.linha_anterior_id=l.id)
  ) then raise exception 'entrada ou identidade mudou desde a auditoria; nao corrigir sem nova conferência'; end if;
  for r in select distinct card_id,ataque,defesa from _estilos_v12_batch loop
   f:=clube_novo.carta_estilos_efetivos_v12(r.card_id);
   if not coalesce((f->>'pode_rodar')::boolean,false) or (f->>'ataque_id')::int<>r.ataque or (f->>'defesa_id')::int<>r.defesa then
    raise exception 'estilos da carta mudaram desde a auditoria'; end if;
  end loop;
  for r in select distinct funcao_id,posicao_id,ataque,defesa,novo_1,novo_2 from _estilos_v12_batch loop
   f:=clube_novo.conferir_bonus_estilo_0909_v1(r.funcao_id,r.posicao_id,r.ataque,r.defesa);
   if not coalesce((f->>'pode_calcular')::boolean,false) or (f->>'bonus_ataque')::numeric<>r.novo_1 or (f->>'bonus_defesa')::numeric<>r.novo_2 then
    raise exception 'regra mudou desde a auditoria'; end if;
  end loop;
  update _estilos_v12_batch a set resultado_novo_fingerprint=encode(extensions.digest(jsonb_build_object(
   'contrato','correcao-estilos-v12','linha',a.linha_id,'origem',b.resultado_fingerprint,
   'regua',v_regua->>'contrato_fingerprint','formula',v_regua->>'formula_fingerprint',
   'ataque',a.ataque,'defesa',a.defesa,'bonus_1',a.novo_1,'bonus_2',a.novo_2)::text,'sha256'),'hex')
  from clube_novo.build_bonificador b where b.id=a.antigo_id;
  insert into clube_novo.build_bonificador(
   bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,bonus_ia,bonus_outros,bonus_total,
   contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,formula_fingerprint,resultado_fingerprint,
   concluido_em,bonus_fisico_detalhe,criado_em,motor_versao,b_corpo,b_pe_ruim,b_estilo,b_total,faltou,corpo_soma,corpo_pct,entrada_bonificador_fingerprint)
  select b.bonus_pe,b.bonus_fisico_total,b.bonus_posicao,a.novo_1,a.novo_2,b.bonus_ia,b.bonus_outros,
   round(b.bonus_total-b.bonus_playstyle_1-b.bonus_playstyle_2+a.novo_1+a.novo_2,4),
   'bonificador-regua-v4',v_regua->>'contrato_fingerprint',b.carta_versao,b.carta_fingerprint,v_regua->>'formula_fingerprint',a.resultado_novo_fingerprint,
   clock_timestamp(),b.bonus_fisico_detalhe,clock_timestamp(),'v12-0909-estilo-funcao-ativacao-v1',
   b.b_corpo,b.b_pe_ruim,a.novo_1+a.novo_2,round(b.b_total-b.b_estilo+a.novo_1+a.novo_2,4),
   b.faltou,b.corpo_soma,b.corpo_pct,b.entrada_bonificador_fingerprint
  from _estilos_v12_batch a join clube_novo.build_bonificador b on b.id=a.antigo_id
  on conflict(resultado_fingerprint) do nothing;
  update _estilos_v12_batch a set criado_id=b.id from clube_novo.build_bonificador b where b.resultado_fingerprint=a.resultado_novo_fingerprint;
  if exists(select 1 from _estilos_v12_batch where criado_id is null) then raise exception 'resultado novo ausente'; end if;
  -- Apenas o ponteiro atual muda. Os campos anteriores/snapshots historicos ficam intactos.
  update clube_novo.bonificador_correcao_item_v1 i set build_bonificador_id_novo=a.criado_id
  from _estilos_v12_batch a where not a.era_publicada and i.build_linha_card_id=a.linha_id and i.build_bonificador_id_novo=a.antigo_id;
  update clube_novo.build_linha_card l set build_bonificador_id=a.criado_id,
   bonificador_motor_versao='v12-0909-estilo-funcao-ativacao-v1',bonificador_contrato_versao='bonificador-regua-v4',
   snapshot_bonificador_fingerprint=a.resultado_novo_fingerprint
  from _estilos_v12_batch a where not a.era_publicada and l.id=a.linha_id and l.build_bonificador_id=a.antigo_id;
  update clube_novo.correcao_estilos_item_v12 i set novo_id=a.criado_id,
   resultado_novo_fingerprint=a.resultado_novo_fingerprint,corrigida_em=clock_timestamp(),
   estado=case when i.era_publicada then 'corrigida' else 'concluida' end,
   concluida_em=case when not i.era_publicada then clock_timestamp() end
  from _estilos_v12_batch a where i.linha_id=a.linha_id;
 end if;
 -- Republicacao em pequenos lotes. Todo erro fica registrado para parada visivel.
 for r in select * from clube_novo.correcao_estilos_item_v12
  where estado='corrigida' and (p_linhas is null or linha_id=any(p_linhas))
  order by linha_id limit least(greatest(coalesce(p_limite,20),1),20)
 loop
  begin
   perform 1 from clube_novo.build_linha_card where id=r.linha_id for update;
   if not exists(select 1 from clube_novo.build_linha_card l
    join clube_novo.build_publicacao_linha_ativa_v1 p on p.linha_id=l.id
    where l.id=r.linha_id and l.build_bonificador_id=r.antigo_id
     and p.build_bonificador_id=(r.publicacao_anterior->>'build_bonificador_id')::bigint
     and p.publicacao_fingerprint is not distinct from r.publicacao_anterior->>'publicacao_fingerprint'
     and exists(select 1 from clube_novo.build_bonificador bp
      join clube_novo.build_bonificador ba on ba.id=r.antigo_id
      where bp.id=p.build_bonificador_id
       and (bp.bonus_pe,bp.bonus_fisico_total,bp.bonus_posicao,bp.bonus_ia,bp.bonus_outros,bp.bonus_playstyle_1,bp.bonus_playstyle_2,bp.bonus_total)
        is not distinct from
        (ba.bonus_pe,ba.bonus_fisico_total,ba.bonus_posicao,ba.bonus_ia,ba.bonus_outros,ba.bonus_playstyle_1,ba.bonus_playstyle_2,ba.bonus_total))
     and l.build_otimizador_id is not distinct from r.otimizador_id
     and l.snapshot_otimizador_fingerprint is not distinct from r.otimizador_fingerprint
     and p.nota_final is not distinct from r.nota_anterior)
   then raise exception 'publicacao ou Otimizador mudou desde a auditoria'; end if;
   -- Troca dos ponteiros e da publicacao no MESMO bloco transacional.
   -- Ate a confirmacao, a publicacao antiga continua integralmente visivel.
   update clube_novo.bonificador_correcao_item_v1 set build_bonificador_id_novo=r.novo_id
    where build_linha_card_id=r.linha_id and build_bonificador_id_novo=r.antigo_id;
   update clube_novo.build_linha_card set build_bonificador_id=r.novo_id,
    bonificador_motor_versao='v12-0909-estilo-funcao-ativacao-v1',bonificador_contrato_versao='bonificador-regua-v4',
    snapshot_bonificador_fingerprint=r.resultado_novo_fingerprint
    where id=r.linha_id;
   f:=clube_novo.finalizar_publicar_linha_v1(r.linha_id,'correcao_estilos_v12');
   if f->>'estado' not in ('publicada','ja_publicada') then raise exception 'publicacao recusada: %',f; end if;
   if not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 p
    join clube_novo.build_bonificador b on b.id=r.antigo_id
    where p.linha_id=r.linha_id and p.build_bonificador_id=r.novo_id
     and p.build_otimizador_id is not distinct from r.otimizador_id
     and p.nota_final=r.nota_anterior-b.bonus_playstyle_1-b.bonus_playstyle_2+r.novo_1+r.novo_2)
   then raise exception 'readback nao confirmou mudanca exclusiva de estilo'; end if;
   update clube_novo.correcao_estilos_item_v12 set estado='concluida',concluida_em=clock_timestamp(),erro=null where linha_id=r.linha_id;
   v_publicadas:=v_publicadas+1;
  exception when others then
   get stacked diagnostics v_erro=message_text;
   update clube_novo.correcao_estilos_item_v12 set estado='erro',erro=v_erro where linha_id=r.linha_id;
   exit;
  end;
 end loop;
 if not exists(select 1 from clube_novo.correcao_estilos_item_v12 where estado<>'concluida') then
  update clube_novo.correcao_estilos_execucao_v12 set concluida_em=coalesce(concluida_em,clock_timestamp())
   where id='estilos-funcao-20260909-v1' and concluida_em is null;
 end if;
 return public.correcao_estilos_status_v12()||jsonb_build_object('corrigidas_neste_lote',v_n,
  'publicadas_neste_lote',v_publicadas,'duracao_ms',round(extract(epoch from clock_timestamp()-v_inicio)*1000,2));
end $f$;
revoke all on function public.correcao_estilos_tick_v12(integer,bigint[]) from public,anon,authenticated;
grant execute on function public.correcao_estilos_tick_v12(integer,bigint[]) to service_role;

-- O calculo da nota permanece integralmente o mesmo; apenas a admissao dos estilos muda.
CREATE OR REPLACE FUNCTION clube_novo.finalizar_publicar_linha_v1(p_linha_id bigint, p_origem text DEFAULT 'desconhecida'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  l clube_novo.build_linha_card%rowtype;
  o clube_novo.build_otimizador%rowtype;
  b clube_novo.build_bonificador%rowtype;
  f record;
  v_bonus_id bigint;
  v_agora timestamptz:=clock_timestamp();
  v_numerador numeric; v_denominador numeric; v_nota_motor numeric; v_nota_final numeric;
  v_linha_publicacao_fp text; v_publicacao_v2_fp text; v_proveniencia jsonb;
  v_delta integer; v_ativa clube_novo.build_publicacao_linha_ativa_v1%rowtype;
  v_erro text; v_estado text; v_motivo text;
begin
  if p_linha_id is null then raise exception 'finalizacao: linha obrigatoria'; end if;
  select * into l from clube_novo.build_linha_card where id=p_linha_id for update;
  if l.id is null then return jsonb_build_object('ok',false,'estado','erro','motivo','linha inexistente'); end if;

  if exists(select 1 from clube_novo.orcamento_revisao_linha_v1 r where r.linha_anterior_id=l.id) then
    update clube_novo.build_finalizacao_fila_v1 set estado='erro',
      motivo='resultado anterior invalidado por correcao de orcamento',
      proxima_tentativa_em='infinity'::timestamptz, atualizado_em=clock_timestamp()
    where linha_id=l.id;
    return jsonb_build_object('ok',false,'linha_id',l.id,'estado','invalidada',
      'motivo','resultado anterior substituido por revisao de orcamento');
  end if;

  insert into clube_novo.build_finalizacao_fila_v1(
    linha_id,estado,prioridade,overall_origem,tentativas,origem_ultima,
    proxima_tentativa_em,ultima_tentativa_em,atualizado_em)
  select l.id,'processando',coalesce((
      select min(i.prioridade_grupo)::integer
      from clube_novo.bonificador_correcao_item_v1 i
      join clube_novo.bonificador_correcao_lote_v1 lo on lo.id=i.lote_id
      where i.build_linha_card_id=l.id and i.estado_item='preparado'
        and lo.motor_versao='v11-0709-estilo-posicao-oficial-v1'
    ),10),c.overall,1,coalesce(nullif(p_origem,''),'desconhecida'),v_agora,v_agora,v_agora
  from clube_novo.carta_jogo c where c.card_id=l.card_id
  on conflict(linha_id) do update set estado='processando',
    tentativas=clube_novo.build_finalizacao_fila_v1.tentativas+1,
    prioridade=least(clube_novo.build_finalizacao_fila_v1.prioridade,excluded.prioridade),
    overall_origem=excluded.overall_origem,origem_ultima=excluded.origem_ultima,
    ultima_tentativa_em=v_agora,atualizado_em=v_agora;

  select bx.id into v_bonus_id
  from clube_novo.build_bonificador bx
  where bx.id=l.build_bonificador_id
    and clube_novo.bonus_estilo_conforme_v12(bx.id,l.card_id,l.funcao_id,l.posicao_id)
    and bx.carta_versao is not distinct from l.carta_versao
    and bx.carta_fingerprint is not distinct from l.carta_fingerprint
    and bx.entrada_bonificador_fingerprint is not distinct from l.carta_fingerprint
    and coalesce(cardinality(bx.faltou), -1)=0
  limit 1;
  if v_bonus_id is null then
    select i.build_bonificador_id_novo into v_bonus_id
    from clube_novo.bonificador_correcao_item_v1 i
    join clube_novo.bonificador_correcao_lote_v1 lo on lo.id=i.lote_id
    join clube_novo.build_bonificador bx on bx.id=i.build_bonificador_id_novo
    where i.build_linha_card_id=l.id and i.estado_item='preparado'
      and clube_novo.bonus_estilo_conforme_v12(bx.id,l.card_id,l.funcao_id,l.posicao_id)
      and bx.carta_versao is not distinct from l.carta_versao
      and bx.carta_fingerprint is not distinct from l.carta_fingerprint
      and bx.entrada_bonificador_fingerprint is not distinct from l.carta_fingerprint
      and coalesce(cardinality(bx.faltou), -1)=0
    order by lo.criado_em desc,i.preparado_em desc limit 1;
  end if;

  if l.build_otimizador_id is null or l.estado_otimizador<>'concluido' then
    v_estado:='aguardando'; v_motivo:='aguardando Otimizador concluido';
  elsif v_bonus_id is null then
    v_estado:='aguardando'; v_motivo:='aguardando Bonificador com estilos conferidos';
  else
    select * into o from clube_novo.build_otimizador where id=l.build_otimizador_id;
    select * into b from clube_novo.build_bonificador where id=v_bonus_id;
    if o.id is null then v_estado:='erro'; v_motivo:='resultado do Otimizador inexistente';
    elsif b.id is null then v_estado:='erro'; v_motivo:='resultado do Bonificador inexistente';
    elsif not clube_novo.bonus_estilo_conforme_v12(b.id,l.card_id,l.funcao_id,l.posicao_id) then
      v_estado:='erro'; v_motivo:='Bonificador sem selo ou estilos compativeis com a politica V12';
    elsif o.carta_versao<>l.carta_versao or b.carta_versao<>l.carta_versao
       or b.carta_fingerprint is distinct from l.carta_fingerprint
       or b.entrada_bonificador_fingerprint is distinct from l.carta_fingerprint then
      v_estado:='erro'; v_motivo:='versao ou entrada do Bonificador incompatível';
    elsif o.resultado_fingerprint is distinct from l.snapshot_otimizador_fingerprint then
      v_estado:='erro'; v_motivo:='selo do Otimizador nao coincide com a linha';
    elsif jsonb_typeof(o.atributos_finais)<>'array' or jsonb_array_length(o.atributos_finais)<>26
       or jsonb_typeof(coalesce(o.atributos_internos,o.atributos_finais))<>'array'
       or jsonb_array_length(coalesce(o.atributos_internos,o.atributos_finais))<>26
       or o.arows_snapshot is null then
      v_estado:='aguardando'; v_motivo:='aguardando 26 atributos e arows do Otimizador';
    elsif cardinality(l.pendencias)<>0 or l.execucao_tipo<>'producao' or l.lote_teste_id is not null
       or l.pendencias @> array['teste_nao_publicado'::text] then
      v_estado:='erro'; v_motivo:='linha nao e publicavel pelo contrato produtivo';
    end if;
  end if;

  if v_estado is not null then
    update clube_novo.build_finalizacao_fila_v1 set estado=v_estado,motivo=v_motivo,
      proxima_tentativa_em=v_agora+case when v_estado='erro' then interval '1 hour' else interval '5 minutes' end,
      atualizado_em=v_agora where linha_id=l.id;
    return jsonb_build_object('ok',v_estado<>'erro','linha_id',l.id,'estado',v_estado,'motivo',v_motivo);
  end if;

  select * into v_ativa from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=l.id;
  if v_ativa.linha_id is not null
     and v_ativa.build_otimizador_id=l.build_otimizador_id
     and v_ativa.build_bonificador_id=v_bonus_id
     and l.build_bonificador_id=v_bonus_id
     and l.nota_final is not distinct from v_ativa.nota_final
     and l.nota_bonificador_resultado_fingerprint is not distinct from b.resultado_fingerprint
     and l.nota_otimizador_resultado_fingerprint is not distinct from o.resultado_fingerprint
     and exists(select 1 from clube_novo.build_pontuacao_final_v2_delta_v1 d where d.linha_id=l.id) then
    update clube_novo.build_finalizacao_fila_v1 set estado='concluido',motivo='idempotente',
      concluido_em=coalesce(concluido_em,v_agora),publicacao_fingerprint=v_ativa.publicacao_fingerprint,
      atualizado_em=v_agora where linha_id=l.id;
    return jsonb_build_object('ok',true,'linha_id',l.id,'estado','ja_publicada',
      'publicacao_fingerprint',v_ativa.publicacao_fingerprint,'idempotente',true);
  end if;

  begin
    perform set_config('clube_novo.finalizacao_linha_em_curso',l.id::text,true);
    update clube_novo.build_linha_card set
      build_bonificador_id=v_bonus_id,
      bonificador_motor_versao=b.motor_versao,
      bonificador_contrato_versao=b.contrato_versao,
      snapshot_bonificador_fingerprint=b.resultado_fingerprint,
      publicacao_fingerprint=null,publicada_em=null,
      nota_contrato=null,nota_otimizador_resultado_fingerprint=null,
      nota_bonificador_resultado_fingerprint=null,nota_carta_fingerprint=null,
      nota_formula_fingerprint=null,nota_contrato_fingerprint=null,
      nota_bruta_selada=null,nota_bonus_pe=null,nota_bonus_fisico_total=null,
      nota_bonus_posicao=null,nota_bonus_playstyle_1=null,nota_bonus_playstyle_2=null,
      nota_bonus_ia=null,nota_bonus_outros=null,nota_bonus_total=null,
      nota_numerador=null,nota_denominador=null,nota_do_motor=null,nota_final=null,
      nota_normalizacao_fingerprint=null,nota_calculo_fingerprint=null,
      nota_publicacao_fingerprint_v1=null,nota_publicada_em_v1=null,nota_calculada_em=null,
      atualizado_em=v_agora
    where id=l.id;

    select * into f from clube_novo.build_pontuacao_final_v1 where linha_id=l.id;
    if f.linha_id is null or f.estado_final<>'elegivel_para_publicacao'
       or f.selo_final_fingerprint is null then
      raise exception 'linha nao ficou elegivel: %',coalesce(f.motivo_final,'sem contrato final');
    end if;

    v_numerador:=clube_novo.calcular_numerador_normalizacao_v2(
      coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot);
    v_denominador:=clube_novo.calcular_denominador_normalizacao_v2(o.arows_snapshot);
    v_nota_motor:=clube_novo.calcular_pontuacao_normalizada_v2(
      coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot);
    v_nota_final:=v_nota_motor+b.bonus_total;

    update clube_novo.build_linha_card set
      publicacao_fingerprint=f.selo_final_fingerprint,publicada_em=v_agora,
      nota_contrato='clube-novo-pontuacao-normalizada-v2',
      nota_otimizador_resultado_fingerprint=o.resultado_fingerprint,
      nota_bonificador_resultado_fingerprint=b.resultado_fingerprint,
      nota_carta_fingerprint=o.carta_fingerprint,
      nota_formula_fingerprint=o.formula_fingerprint,
      nota_contrato_fingerprint=o.contrato_fingerprint,
      nota_bruta_selada=f.pontuacao_otimizador,
      nota_bonus_pe=b.bonus_pe,nota_bonus_fisico_total=b.bonus_fisico_total,
      nota_bonus_posicao=b.bonus_posicao,nota_bonus_playstyle_1=b.bonus_playstyle_1,
      nota_bonus_playstyle_2=b.bonus_playstyle_2,nota_bonus_ia=b.bonus_ia,
      nota_bonus_outros=coalesce(b.bonus_outros,'{}'::jsonb),nota_bonus_total=b.bonus_total,
      nota_numerador=v_numerador,nota_denominador=v_denominador,
      nota_do_motor=v_nota_motor,nota_final=v_nota_final,
      nota_normalizacao_fingerprint=clube_novo.fingerprint_normalizacao_v2(
        l.id,o.id,b.id,o.resultado_fingerprint,b.resultado_fingerprint,f.selo_final_fingerprint),
      nota_calculo_fingerprint=clube_novo.fingerprint_calculo_pontuacao_v2(
        l.id,coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total),
      nota_publicacao_fingerprint_v1=f.selo_final_fingerprint,
      nota_publicada_em_v1=v_agora,nota_calculada_em=v_agora,atualizado_em=v_agora
    where id=l.id;

    v_linha_publicacao_fp:=pg_catalog.encode(extensions.digest(pg_catalog.convert_to(
      jsonb_build_object(
        'contrato','clube-novo-pontuacao-final-v2','linha_id',l.id,
        'calculo_banco_fingerprint',clube_novo.fingerprint_calculo_pontuacao_v2(
          l.id,coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total),
        'bonificador_resultado_fingerprint',b.resultado_fingerprint,
        'overall_final',v_nota_final,'publicacao_fingerprint_v1',f.selo_final_fingerprint
      )::text,'UTF8'::name),'sha256'),'hex');
    v_publicacao_v2_fp:=pg_catalog.encode(extensions.digest(pg_catalog.convert_to(
      jsonb_build_object('contrato','clube-novo-publicacao-automatica-por-linha-v1',
        'linha_id',l.id,'publicacao_linha_fingerprint_v2',v_linha_publicacao_fp)::text,
      'UTF8'::name),'sha256'),'hex');
    v_proveniencia:=jsonb_build_object(
      'contrato','clube-novo-pontuacao-final-v2','modo','automatico_por_linha',
      'linha_id',l.id,
      'otimizador',jsonb_build_object('id',o.id,'resultado_fingerprint',o.resultado_fingerprint,
        'pontuacao_bruta_apenas_evidencia',f.pontuacao_otimizador,
        'pontuacao_normalizada',v_nota_motor),
      'bonificador',jsonb_build_object('id',b.id,'resultado_fingerprint',b.resultado_fingerprint,
        'componentes',jsonb_build_object('pe',b.bonus_pe,'fisico',b.bonus_fisico_total,
          'posicao',b.bonus_posicao,'playstyle_1',b.bonus_playstyle_1,
          'playstyle_2',b.bonus_playstyle_2,'ia',b.bonus_ia,
          'outros',coalesce(b.bonus_outros,'{}'::jsonb)),
        'bonus_total',b.bonus_total),
      'pontuacao_final_oficial',v_nota_final,
      'publicacao_v1',f.selo_final_fingerprint,'publicacao_v2',v_linha_publicacao_fp);

    delete from clube_novo.build_pontuacao_final_v2_delta_v1 where linha_id=l.id;
    insert into clube_novo.build_pontuacao_final_v2_delta_v1(
      publicacao_v2_fingerprint,linha_id,card_id,funcao_id,posicao_id,
      build_otimizador_id,build_bonificador_id,tecnico_id,barras,
      impeto_adicional_codigo,habilidades_adicionais,atributos_finais,arows_snapshot,
      pontuacao_otimizador_bruta_evidencia,pontuacao_otimizador_normalizada,
      bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,
      bonus_ia,bonus_outros,bonus_total_bonificador,overall_final,
      normalizacao_fingerprint,calculo_banco_fingerprint,carta_fingerprint,
      formula_fingerprint,contrato_fingerprint,otimizador_resultado_fingerprint,
      bonificador_resultado_fingerprint,publicacao_fingerprint_v1,publicada_em,
      publicacao_linha_fingerprint_v2,topo_funcao,percentual_topo,
      estado_final,motivo_final,proveniencia)
    values(
      v_publicacao_v2_fp,l.id,l.card_id,l.funcao_id,l.posicao_id,
      o.id,b.id,o.tecnico_id,o.barras,o.impeto_adicional_codigo,o.habilidades_adicionais,
      o.atributos_finais,o.arows_snapshot,f.pontuacao_otimizador,v_nota_motor,
      b.bonus_pe,b.bonus_fisico_total,b.bonus_posicao,b.bonus_playstyle_1,
      b.bonus_playstyle_2,b.bonus_ia,coalesce(b.bonus_outros,'{}'::jsonb),b.bonus_total,
      v_nota_final,
      clube_novo.fingerprint_normalizacao_v2(l.id,o.id,b.id,o.resultado_fingerprint,
        b.resultado_fingerprint,f.selo_final_fingerprint),
      clube_novo.fingerprint_calculo_pontuacao_v2(l.id,
        coalesce(o.atributos_internos,o.atributos_finais),o.arows_snapshot,b.bonus_total),
      o.carta_fingerprint,o.formula_fingerprint,o.contrato_fingerprint,
      o.resultado_fingerprint,b.resultado_fingerprint,f.selo_final_fingerprint,v_agora,
      v_linha_publicacao_fp,null,null,'publicada',
      'PUBLICADA_AUTOMATICAMENTE_POR_LINHA',v_proveniencia);
    get diagnostics v_delta=row_count;
    if v_delta<>1 then raise exception 'read model incremental recebeu % linhas',v_delta; end if;

    insert into clube_novo.build_publicacao_linha_ativa_v1(
      linha_id,card_id,funcao_id,posicao_id,build_otimizador_id,build_bonificador_id,
      nota_final,selo_final_fingerprint,publicacao_fingerprint,publicacao_v2_fingerprint,
      proveniencia,publicada_em,versao_publicacao,atualizado_em)
    select l.id,l.card_id,l.funcao_id,l.posicao_id,o.id,b.id,v_nota_final,
      f.selo_final_fingerprint,f.selo_final_fingerprint,d.publicacao_v2_fingerprint,
      v_proveniencia,v_agora,1,v_agora
    from clube_novo.build_pontuacao_final_v2_delta_v1 d where d.linha_id=l.id
    on conflict(linha_id) do update set
      card_id=excluded.card_id,funcao_id=excluded.funcao_id,posicao_id=excluded.posicao_id,
      build_otimizador_id=excluded.build_otimizador_id,
      build_bonificador_id=excluded.build_bonificador_id,nota_final=excluded.nota_final,
      selo_final_fingerprint=excluded.selo_final_fingerprint,
      publicacao_fingerprint=excluded.publicacao_fingerprint,
      publicacao_v2_fingerprint=excluded.publicacao_v2_fingerprint,
      proveniencia=excluded.proveniencia,publicada_em=excluded.publicada_em,
      versao_publicacao=clube_novo.build_publicacao_linha_ativa_v1.versao_publicacao+1,
      atualizado_em=excluded.atualizado_em;

    if not exists(select 1 from clube_novo.build_pontuacao_final_v2_publica_v1 p
      join clube_novo.build_publicacao_linha_ativa_v1 a using(linha_id)
      where p.linha_id=l.id and p.build_otimizador_id=a.build_otimizador_id
        and p.build_bonificador_id=a.build_bonificador_id and p.overall_final=a.nota_final) then
      raise exception 'readback da ponte publica falhou';
    end if;
  exception when others then
    get stacked diagnostics v_erro=message_text;
    update clube_novo.build_finalizacao_fila_v1 set estado='erro',motivo=v_erro,
      proxima_tentativa_em=clock_timestamp()+interval '10 minutes',atualizado_em=clock_timestamp()
      where linha_id=l.id;
    insert into clube_novo.build_finalizacao_evento_v1(linha_id,evento,detalhe)
      values(l.id,'falhou',jsonb_build_object('origem',p_origem,'erro',v_erro));
    return jsonb_build_object('ok',false,'linha_id',l.id,'estado','erro','motivo',v_erro);
  end;

  update clube_novo.build_finalizacao_fila_v1 set estado='concluido',motivo=null,
    concluido_em=v_agora,publicacao_fingerprint=f.selo_final_fingerprint,
    atualizado_em=v_agora where linha_id=l.id;
  insert into clube_novo.build_finalizacao_evento_v1(linha_id,evento,detalhe)
    values(l.id,'publicada',jsonb_build_object('origem',p_origem,
      'build_otimizador_id',o.id,'build_bonificador_id',b.id,
      'nota_final',v_nota_final,'selo',f.selo_final_fingerprint));
  update clube_novo.orcamento_revisao_linha_v1 set estado='republicada'
    where linha_nova_id=l.id;
  return jsonb_build_object('ok',true,'linha_id',l.id,'card_id',l.card_id,
    'estado','publicada','nota_final',v_nota_final,'publicacao_fingerprint',f.selo_final_fingerprint,
    'build_otimizador_id',o.id,'build_bonificador_id',b.id,'idempotente',false);
end
$function$
;

CREATE OR REPLACE FUNCTION clube_novo.disparar_finalizacao_linha_v1()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
begin
  if current_setting('clube_novo.migracao_estilo_v11',true)='1' then return new; end if;
  if current_setting('clube_novo.correcao_estilos_v12',true)='1' then return new; end if;
  if current_setting('clube_novo.finalizacao_linha_em_curso',true)=new.id::text
     or pg_trigger_depth()>1 then return new; end if;
  perform clube_novo.finalizar_publicar_linha_v1(new.id,'build_linha_card:'||tg_op);
  return new;
end
$function$;

CREATE OR REPLACE FUNCTION clube_novo.disparar_finalizacao_correcao_v1()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_linha_nova_id bigint;
  v_erro text;
begin
  if current_setting('clube_novo.migracao_estilo_v11',true)='1' then return new; end if;
  if current_setting('clube_novo.correcao_estilos_v12',true)='1' then return new; end if;
  if new.estado_item = 'preparado'
     and new.build_bonificador_id_novo is not null
     and (
       tg_op = 'INSERT'
       or old.estado_item is distinct from new.estado_item
       or old.build_bonificador_id_novo is distinct from new.build_bonificador_id_novo
     ) then
    begin
      select r.linha_nova_id into v_linha_nova_id
      from clube_novo.orcamento_revisao_linha_v1 r
      where r.linha_anterior_id = new.build_linha_card_id;

      if v_linha_nova_id is not null then
        perform clube_novo.reaproveitar_bonificador_revisao_orcamento_v1(
          new.build_linha_card_id,
          new.build_bonificador_id_novo,
          'bonificador_correcao:' || tg_op
        );
      else
        perform clube_novo.vincular_bonificador_v10_independente_v1(
          new.build_linha_card_id,
          new.build_linha_card_id,
          new.build_bonificador_id_novo,
          'bonificador_correcao:' || tg_op
        );
      end if;
    exception when others then
      get stacked diagnostics v_erro = message_text;
      insert into clube_novo.build_finalizacao_evento_v1(linha_id, evento, detalhe)
      values (
        coalesce(v_linha_nova_id, new.build_linha_card_id),
        'bonificador_v10_vinculo_falhou',
        jsonb_build_object(
          'origem', 'bonificador_correcao:' || tg_op,
          'linha_fonte_id', new.build_linha_card_id,
          'build_bonificador_id', new.build_bonificador_id_novo,
          'erro', v_erro
        )
      );
    end;
  end if;
  return new;
end
$function$;

-- Projecao visual dos estilos efetivos; campos fisicos originais preservados.
CREATE OR REPLACE FUNCTION public.site_novo_ficha_v2(p_card_id text DEFAULT NULL::text, p_linha_id bigint DEFAULT NULL::bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET jit TO 'off'
AS $function$
declare
  ficha jsonb;
  impetos jsonb;
  sugestoes jsonb;
  estilos jsonb;
  pe_rotulado jsonb;
  build jsonb;
  tecnico jsonb;
  degraus jsonb;
begin
  ficha := public.site_novo_ficha_v1(p_card_id,p_linha_id)
    || jsonb_build_object('contrato','site-novo-ficha-v2','versao',2);
  if jsonb_typeof(ficha #> '{dados,card}') = 'object' then
    select coalesce(jsonb_agg(jsonb_build_object(
      'id',p.id_jogo,'slot',cp.slot_fisico,
      'tipo',case cp.slot_fisico when 1 then 'ofensivo' when 2 then 'defensivo' end,
      'nome',coalesce(p.nome_tela,p.nome_pt,p.nome_en)
    ) order by cp.slot_fisico,p.id_jogo),'[]'::jsonb)
    into estilos
    from lateral(select clube_novo.carta_estilos_efetivos_v12(ficha #>> '{dados,card,card_id}') j) s
    cross join lateral(values (1,(s.j->>'ataque_id')::integer),(2,(s.j->>'defesa_id')::integer)) cp(slot_fisico,playstyle_id)
    join clube_novo.playstyle p on p.id_jogo=cp.playstyle_id
    where coalesce((s.j->>'pode_rodar')::boolean,false);
    ficha := jsonb_set(ficha,'{dados,card,estilos_jogo}',estilos);
    if jsonb_typeof(ficha #> '{dados,card,pe}')='array' then
      select coalesce(jsonb_agg(e.item || jsonb_build_object(
        'rotulo_valor',case when p.campo='pe_dominante' then p.nome_pt else nullif(p.nome_antigo,'') end
      ) order by e.ordem),'[]'::jsonb)
      into pe_rotulado
      from jsonb_array_elements(ficha #> '{dados,card,pe}') with ordinality e(item,ordem)
      left join clube_novo.pe p on p.campo=e.item->>'campo'
        and p.valor=(e.item->>'valor')::integer;
      ficha := jsonb_set(ficha,'{dados,card,pe}',pe_rotulado);
    end if;
  end if;
  build := ficha #> '{dados,build}';
  if jsonb_typeof(build) <> 'object' or build is null then
    return ficha;
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
    'nivel',d.impeto_condicional_nivel,
    'linha_id',d.linha_id
  ) order by d.impeto_condicional_nivel),'[]'::jsonb)
  into degraus
  from (
    select distinct on (alvo.impeto_condicional_nivel)
      alvo.impeto_condicional_nivel,
      alvo.linha_id
    from clube_novo.build_publicacao_linha_ativa_v1 atual
    join clube_novo.build_publicacao_linha_ativa_v1 alvo
      on alvo.card_id=atual.card_id
     and alvo.funcao_id=atual.funcao_id
     and alvo.posicao_id=atual.posicao_id
     and alvo.impeto_condicional_codigo=atual.impeto_condicional_codigo
    where atual.linha_id=(build->>'linha_id')::bigint
      and atual.impeto_condicional_codigo is not null
      and alvo.impeto_condicional_nivel between 1 and 3
    order by alvo.impeto_condicional_nivel,alvo.nota_final desc nulls last,alvo.linha_id
  ) d;
  ficha := jsonb_set(ficha,'{dados,degraus_condicionais}',degraus,true);

  if jsonb_typeof(build->'impetos') = 'array' then
    select coalesce(jsonb_agg(elemento.item || jsonb_build_object(
      'cor_visual',cor.cor_visual,
      'cor_visual_estado',coalesce(cor.estado_validacao,'aguardando_mapeamento')
    ) order by elemento.ordem),'[]'::jsonb)
    into impetos
    from jsonb_array_elements(build->'impetos') with ordinality elemento(item,ordem)
    left join clube_novo.impeto_jogo ij on ij.codigo_jogo=case
      when coalesce(elemento.item->>'codigo','') ~ '^[0-9]+$'
      then (elemento.item->>'codigo')::integer else null end
    left join clube_novo.tipo_impeto_cor_visual_jogo cor
      on cor.tipo_raw=ij.tipo_condicao_raw and cor.estado_validacao='confirmada';
    build := jsonb_set(build,'{impetos}',impetos);
  end if;
  sugestoes := clube_novo.site_novo_ficha_sugestoes_v1(
    ficha #>> '{dados,card,card_id}',(build->>'linha_id')::bigint);
  build := build || jsonb_build_object(
    'habilidades_sugeridas',sugestoes->'habilidades',
    'habilidades_sugeridas_estado',sugestoes->>'estado');
  tecnico := build->'tecnico';
  if jsonb_typeof(tecnico)='object' then
    build := jsonb_set(build,'{tecnico}',tecnico || jsonb_build_object(
      'sugeridos',sugestoes->'tecnicos','sugeridos_estado',sugestoes->>'estado'));
  end if;
  build := build || jsonb_build_object('pontos_distribuicao',
    clube_novo.site_novo_contador_pontos_v1(build->'barras',(build->>'orcamento_total')::integer));
  return jsonb_set(ficha,'{dados,build}',build);
end;
$function$
;
