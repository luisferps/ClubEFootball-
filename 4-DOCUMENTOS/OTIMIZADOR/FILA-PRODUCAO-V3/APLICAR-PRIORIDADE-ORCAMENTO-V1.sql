-- Prioridade por nível comprovado. Preparação não inicia qualquer worker.
-- Dependência: clube_novo.carta_nivel_evidencia_v1, instalada pela frente do extrator.
begin;
do $$
declare v_expr text;
begin
 select pg_get_expr(conbin,conrelid) into v_expr
 from pg_constraint where conrelid='clube_novo.otimizador_evento_producao_v3'::regclass
   and conname='otimizador_evento_producao_v3_evento_check';
 if v_expr is null then raise exception 'Constraint de eventos não encontrada'; end if;
 if position('prioridade_orcamento_reordenada' in v_expr)=0
    or position('revisao_orcamento_preparada' in v_expr)=0 then
   alter table clube_novo.otimizador_evento_producao_v3 drop constraint otimizador_evento_producao_v3_evento_check;
   execute format('alter table clube_novo.otimizador_evento_producao_v3 add constraint otimizador_evento_producao_v3_evento_check check ((%s) or evento in (%L,%L))',
     v_expr,'prioridade_orcamento_reordenada','revisao_orcamento_preparada');
 end if;
end $$;

create or replace view clube_novo.otimizador_prioridade_orcamento_v1
with (security_invoker=true) as
select c.card_id, c.overall, e.nivel_maximo, e.orcamento_real, e.captura_id,
       case when c.tipo_carta_id='player_type_0_subtype_0' and c.codigo_tipo_carta_fisico=0 then 3
            when c.codigo_tipo_carta_fisico in (1,3,4,5,6,7) and not c.sem_evolucao then 1
            when c.codigo_tipo_carta_fisico in (1,3,4,5,6,7) and c.sem_evolucao then 2 end as prioridade_grupo
from clube_novo.carta_jogo c
join clube_novo.carta_nivel_evidencia_v1 e on e.card_id=c.card_id
where e.nivel_maximo>=1 and e.orcamento_real=2*(e.nivel_maximo-1)
  and c.tipo_carta_id<>'player_delete_list';
revoke all on clube_novo.otimizador_prioridade_orcamento_v1 from public,anon,authenticated;
grant select on clube_novo.otimizador_prioridade_orcamento_v1 to service_role;

create or replace view clube_novo.otimizador_fila_prioridade_v1
with (security_invoker=true) as
select q.*, l.funcao_id, l.posicao_id, l.impeto_condicional_codigo,l.impeto_condicional_nivel,
       p.prioridade_grupo,p.overall as overall_prioridade,p.nivel_maximo,p.orcamento_real,p.captura_id
from clube_novo.otimizador_lote_producao_linha_v3 q
join clube_novo.build_linha_card l on l.id=q.linha_id
join clube_novo.otimizador_lote_producao_carta_v3 s on s.lote_id=q.lote_id and s.card_id=q.card_id
join clube_novo.otimizador_prioridade_orcamento_v1 p on p.card_id=q.card_id
where l.estado_otimizador='pendente' and l.estado<>'invalida'
  and p.prioridade_grupo is not null
  and q.entrada_fingerprint=s.entrada_fingerprint
  and (s.entrada_otimizador#>>'{escalares,orcamento}')::integer=p.orcamento_real
  and ((l.impeto_condicional_codigo is null)=(l.impeto_condicional_nivel is null));
revoke all on clube_novo.otimizador_fila_prioridade_v1 from public,anon,authenticated;
grant select on clube_novo.otimizador_fila_prioridade_v1 to service_role;

create or replace function public.otimizador_reordenar_prioridade_v1(p_lotes uuid[])
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_lote uuid; v_max bigint; v_base bigint; v_total integer:=0; v_n integer;
begin
  if coalesce(cardinality(p_lotes),0)=0 then raise exception 'Informe os lotes pausados'; end if;
  perform pg_advisory_xact_lock(hashtext('otimizador_prioridade_orcamento_v1'));
  foreach v_lote in array p_lotes loop
    perform 1 from clube_novo.otimizador_lote_producao_v3 where id=v_lote and estado='pausado' for update;
    if not found then raise exception 'Lote % não está pausado',v_lote; end if;
    if exists(select 1 from clube_novo.build_linha_card where lote_producao_id=v_lote and estado_otimizador='processando')
       or exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=v_lote and reserva_token is not null and finalizada_em is null)
    then raise exception 'Lote % possui reserva; ordem não alterada',v_lote; end if;
    select coalesce(max(q.ordem_fila),0),
           coalesce(max(q.ordem_fila) filter(where l.estado_otimizador<>'pendente' or l.estado='invalida'),0)
      into v_max,v_base
      from clube_novo.otimizador_lote_producao_linha_v3 q join clube_novo.build_linha_card l on l.id=q.linha_id
      where q.lote_id=v_lote;
    -- A faixa temporária deve ficar acima também de TODA a faixa final.
    v_max:=v_max+(select count(*) from clube_novo.otimizador_lote_producao_linha_v3 where lote_id=v_lote)+1;
    -- Faixa temporária positiva evita colisão da chave UNIQUE sem tocar no histórico.
    with novas as (
      select q.linha_id,row_number() over(order by p.prioridade_grupo nulls last,c.overall desc nulls first,
        q.card_id collate "C",l.funcao_id,l.posicao_id,l.impeto_condicional_codigo nulls first,
        l.impeto_condicional_nivel nulls first,l.id) as rn
      from clube_novo.otimizador_lote_producao_linha_v3 q
      join clube_novo.build_linha_card l on l.id=q.linha_id
      join clube_novo.carta_jogo c on c.card_id=q.card_id
      left join clube_novo.otimizador_prioridade_orcamento_v1 p on p.card_id=q.card_id
      where q.lote_id=v_lote and l.estado_otimizador='pendente' and l.estado<>'invalida'
    )
    update clube_novo.otimizador_lote_producao_linha_v3 q set ordem_fila=v_max+n.rn
    from novas n where q.lote_id=v_lote and q.linha_id=n.linha_id;
    get diagnostics v_n=row_count; v_total:=v_total+v_n;
    update clube_novo.otimizador_lote_producao_linha_v3 q set ordem_fila=v_base+(q.ordem_fila-v_max)
    where q.lote_id=v_lote and q.ordem_fila>v_max;
    update clube_novo.otimizador_lote_producao_v3 l set fingerprint=encode(extensions.digest(convert_to(
      l.id::text||':'||l.formula_fingerprint||':'||l.contrato_fingerprint||':'||l.motor_versao||':'||
      coalesce((select string_agg(q.card_id||':'||b.funcao_id::text||':'||b.posicao_id::text||':'||q.ordem_fila::text,',' order by q.ordem_fila)
       from clube_novo.otimizador_lote_producao_linha_v3 q join clube_novo.build_linha_card b on b.id=q.linha_id where q.lote_id=l.id),''),
      'UTF8'),'sha256'),'hex'), atualizado_em=clock_timestamp() where l.id=v_lote;
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(v_lote,'prioridade_orcamento_reordenada',jsonb_build_object('linhas_pendentes',v_n,'contrato','prioridade_orcamento_v1','worker_iniciado',false));
  end loop;
  return jsonb_build_object('contrato','prioridade_orcamento_v1','linhas_reordenadas',v_total,'worker_iniciado',false);
end $$;
revoke all on function public.otimizador_reordenar_prioridade_v1(uuid[]) from public,anon,authenticated;
grant execute on function public.otimizador_reordenar_prioridade_v1(uuid[]) to service_role;

-- Contratos vigentes preservados, com prioridade e filtro físico coerentes.
CREATE OR REPLACE FUNCTION public.otimizador_producao_criar_lote_integral_v5(p_lote_id uuid, p_formula_fingerprint text, p_motor_versao text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_formula constant text:='5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89';
  v_regua jsonb; v_contrato_fp text; v_fingerprint text;
  v_total integer:=0; v_condicionais integer:=0; v_inseridas integer:=0;
begin
  if p_lote_id is null or p_formula_fingerprint<>v_formula
     or nullif(btrim(coalesce(p_motor_versao,'')),'') is null then
    raise exception 'criação integral recusada: selo de fórmula ou versão local inválidos';
  end if;
  if exists(
    select 1 from clube_novo.otimizador_lote_producao_v3 where tipo_lote='integral'
  ) then
    raise exception 'criação integral recusada: já existe lote integral V5; a recuperação exige decisão explícita';
  end if;

  select public.otimizador_regua_v2() into v_regua;
  if not coalesce((v_regua->'gate'->>'pode_rodar')::boolean,false) then
    raise exception 'criação integral recusada: gate da régua do Otimizador está fechado';
  end if;
  v_contrato_fp:=clube_novo.otimizador_producao_contrato_fingerprint_v3(v_regua);

  select count(*) into v_total
  from clube_novo.carta_jogo c
  join clube_novo.otimizador_prioridade_orcamento_v1 pr on pr.card_id=c.card_id and pr.prioridade_grupo is not null
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  if v_total=0 then
    raise exception 'criação integral recusada: não há candidata básica elegível';
  end if;

  select count(*) into v_condicionais
  from clube_novo.carta_jogo c
  join clube_novo.otimizador_prioridade_orcamento_v1 pr on pr.card_id=c.card_id and pr.prioridade_grupo is not null
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );

  v_fingerprint:=encode(extensions.digest(convert_to(
    'preparando:'||p_lote_id::text||':'||v_formula||':'||v_contrato_fp||':'||p_motor_versao,
    'UTF8'),'sha256'),'hex');

  insert into clube_novo.otimizador_lote_producao_v3(
    id,tipo_lote,estado,formula_fingerprint,contrato_fingerprint,motor_versao,
    regua_snapshot,fingerprint,cards,linhas,preparo_total,preparo_concluido,
    excluidas_incompletas,excluidas_impeto_condicional,excluidas_sem_linha,pode_publicar
  ) values (
    p_lote_id,'integral','preparando',v_formula,v_contrato_fp,p_motor_versao,
    v_regua,v_fingerprint,0,0,v_total,0,0,v_condicionais,0,false
  );

  insert into clube_novo.otimizador_lote_producao_candidata_v5(
    lote_id,card_id,ordem_candidata,overall_snapshot,carta_versao_snapshot
  )
  select p_lote_id,c.card_id,
         row_number() over(order by pr.prioridade_grupo,c.overall desc nulls first,c.card_id collate "C")::bigint,
         c.overall::integer,coalesce(c.extraido_em::text,'')
  from clube_novo.carta_jogo c
  join clube_novo.otimizador_prioridade_orcamento_v1 pr on pr.card_id=c.card_id and pr.prioridade_grupo is not null
  where coalesce(c.roda_motor,false)
    and coalesce(c.pode_rodar_vinculos,false)
    and not exists(
      select 1 from clube_novo.carta_impeto_jogo ci
      where ci.card_id=c.card_id and coalesce(ci.condicional,false)
    );
  get diagnostics v_inseridas=row_count;
  if v_inseridas<>v_total then
    raise exception 'criação integral recusada: fotografia de candidatas não foi preservada (% de %)',v_inseridas,v_total;
  end if;

  insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
  values(p_lote_id,'preparo_integral_criado',jsonb_build_object(
    'candidatas_basicas',v_total,
    'excluidas_impeto_condicional',v_condicionais,
    'ordem','prioridade_orcamento_v1',
    'preparo','somente snapshots e linhas; nenhum cálculo foi iniciado',
    'pode_publicar',false
  ));
  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_preparar_fatia_v5(p_lote_id uuid, p_limite integer DEFAULT 10)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_formula constant text:='5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89';
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_c clube_novo.otimizador_lote_producao_candidata_v5%rowtype;
  v_entrada jsonb; v_bonificador jsonb; v_versao_atual text;
  v_motivo text; v_processadas integer:=0; v_linhas integer:=0;
  v_linhas_inseridas integer:=0; v_ordem_base bigint:=0;
  v_pendentes_preparo integer:=0; v_concluidas_preparo integer:=0;
  v_cards_final integer:=0; v_linhas_final integer:=0; v_fingerprint text;
begin
  if p_lote_id is null or coalesce(p_limite,0) not between 1 and 20 then
    raise exception 'preparo V5 recusado: lote e limite 1..20 são obrigatórios';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id=p_lote_id
  for update;
  if not found then raise exception 'lote integral V5 inexistente'; end if;
  if v_lote.tipo_lote<>'integral' then raise exception 'preparo V5 recusado: lote não é integral'; end if;
  if v_lote.formula_fingerprint<>v_formula or v_lote.pode_publicar is not false then
    raise exception 'preparo V5 recusado: selo do lote não é a fórmula aprovada';
  end if;
  if v_lote.estado<>'preparando' then
    return public.otimizador_producao_status_v5(p_lote_id);
  end if;

  loop
    exit when v_processadas>=p_limite;
    select * into v_c
    from clube_novo.otimizador_lote_producao_candidata_v5 c
    where c.lote_id=p_lote_id and c.estado='pendente'
    order by (select p.prioridade_grupo from clube_novo.otimizador_prioridade_orcamento_v1 p where p.card_id=c.card_id) nulls last,
             c.overall_snapshot desc nulls first,c.card_id collate "C"
    for update skip locked
    limit 1;
    exit when not found;
    v_processadas:=v_processadas+1;

    begin
      v_versao_atual:=null;
      select coalesce(c.extraido_em::text,'') into v_versao_atual
      from clube_novo.carta_jogo c
      where c.card_id=v_c.card_id;
      if not found or v_versao_atual is distinct from v_c.carta_versao_snapshot then
        update clube_novo.otimizador_lote_producao_candidata_v5
        set estado='divergente',motivo='a versão física da carta mudou durante o preparo',
            atualizado_em=clock_timestamp()
        where lote_id=p_lote_id and card_id=v_c.card_id;
        update clube_novo.otimizador_lote_producao_v3
        set estado='falhou',falha='preparo recusado: a fonte de uma carta mudou; recrie a fotografia do lote',
            atualizado_em=clock_timestamp()
        where id=p_lote_id;
        insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
        values(p_lote_id,'preparo_falhou',jsonb_build_object(
          'card_id',v_c.card_id,'motivo','versão física divergente'
        ));
        return public.otimizador_producao_status_v5(p_lote_id);
      end if;

      select public.otimizador_carta_v3(v_c.card_id),
             public.bonificador_carta_v2(v_c.card_id)
      into v_entrada,v_bonificador;

      if v_entrada is null or v_bonificador is null
         or not coalesce((v_entrada->'gate'->>'pode_rodar')::boolean,false)
         or not coalesce((v_bonificador->>'pode_rodar')::boolean,false)
         or not (v_bonificador ? 'carta_versao')
         or not (v_bonificador ? 'carta_fingerprint') then
        v_motivo:=coalesce(v_entrada#>>'{gate,motivos}',v_bonificador#>>'{gate,motivos}',
          'contrato de entrada incompleto ou gate fechado');
        update clube_novo.otimizador_lote_producao_candidata_v5
        set estado='incompleta',motivo=left(v_motivo,1000),preparado_em=clock_timestamp(),
            atualizado_em=clock_timestamp()
        where lote_id=p_lote_id and card_id=v_c.card_id;
        update clube_novo.otimizador_lote_producao_v3
        set excluidas_incompletas=excluidas_incompletas+1,
            preparo_concluido=preparo_concluido+1,atualizado_em=clock_timestamp()
        where id=p_lote_id;
      else
        select count(*) into v_linhas
        from (
          select distinct fp.funcao_id,fp.posicao_id
          from (
            select cpp.posicao_id
            from clube_novo.carta_posicao_principal_jogo cpp
            where cpp.card_id=v_c.card_id
            union
            select cp.posicao_id
            from clube_novo.carta_posicao_jogo cp
            where cp.card_id=v_c.card_id and cp.nivel_aptidao>0
          ) px
          join clube_novo.otimizador_funcao_posicao fp on fp.posicao_id=px.posicao_id
          join clube_novo.funcao_sistema fs on fs.id=fp.funcao_id and fs.ativa and fs.pode_rodar
          join clube_novo.posicao_jogo p on p.id=fp.posicao_id and p.pode_rodar
        ) linhas;
        if exists (select 1 from clube_novo.carta_impeto_jogo ci
                    where ci.card_id=v_c.card_id and coalesce(ci.condicional,false)) then
          v_linhas := v_linhas * 3;
        end if;

        if v_linhas=0 then
          update clube_novo.otimizador_lote_producao_candidata_v5
          set estado='sem_linha',motivo='não há posição e função canônicas aptas para a carta',
              preparado_em=clock_timestamp(),atualizado_em=clock_timestamp()
          where lote_id=p_lote_id and card_id=v_c.card_id;
          update clube_novo.otimizador_lote_producao_v3
          set excluidas_sem_linha=excluidas_sem_linha+1,
              preparo_concluido=preparo_concluido+1,atualizado_em=clock_timestamp()
          where id=p_lote_id;
        else
          insert into clube_novo.otimizador_lote_producao_carta_v3(
            lote_id,card_id,overall_snapshot,entrada_otimizador,entrada_fingerprint,
            carta_versao_bonificador,carta_fingerprint_bonificador
          ) values (
            p_lote_id,v_c.card_id,v_c.overall_snapshot,v_entrada,
            encode(extensions.digest(convert_to(v_entrada::text,'UTF8'),'sha256'),'hex'),
            v_bonificador->>'carta_versao',v_bonificador->>'carta_fingerprint'
          );

          select coalesce(max(ordem_fila),0) into v_ordem_base
          from clube_novo.otimizador_lote_producao_linha_v3
          where lote_id=p_lote_id;

          with linhas_base as (
            select distinct fp.funcao_id,fp.posicao_id
            from (
              select cpp.posicao_id
              from clube_novo.carta_posicao_principal_jogo cpp
              where cpp.card_id=v_c.card_id
              union
              select cp.posicao_id
              from clube_novo.carta_posicao_jogo cp
              where cp.card_id=v_c.card_id and cp.nivel_aptidao>0
            ) px
            join clube_novo.otimizador_funcao_posicao fp on fp.posicao_id=px.posicao_id
            join clube_novo.funcao_sistema fs on fs.id=fp.funcao_id and fs.ativa and fs.pode_rodar
            join clube_novo.posicao_jogo p on p.id=fp.posicao_id and p.pode_rodar
          ), inseridas as (
            insert into clube_novo.build_linha_card(
              card_id,funcao_id,posicao_id,lote_producao_id,carta_versao,carta_fingerprint,
              estado,pendencias,execucao_tipo,estado_otimizador,
              otimizador_formula_fingerprint_esperado,otimizador_contrato_fingerprint_esperado,
              otimizador_motor_versao_esperada,impeto_condicional_codigo,impeto_condicional_nivel
            )
            select v_c.card_id,b.funcao_id,b.posicao_id,p_lote_id,
                   v_bonificador->>'carta_versao',v_bonificador->>'carta_fingerprint',
                   'pendente','{}'::text[],'producao','pendente',
                   v_lote.formula_fingerprint,v_lote.contrato_fingerprint,v_lote.motor_versao,
                   cond.codigo,cond.nivel
            from linhas_base b
            cross join lateral (
              select ci.codigo_impeto::integer as codigo, d.nivel::smallint as nivel
                from (select ci2.codigo_impeto
                        from clube_novo.carta_impeto_jogo ci2
                       where ci2.card_id=v_c.card_id and coalesce(ci2.condicional,false)
                       order by ci2.slot limit 1) ci
                cross join (values (1),(2),(3)) d(nivel)
              union all
              select null::integer, null::smallint
               where not exists (select 1 from clube_novo.carta_impeto_jogo ci3
                                  where ci3.card_id=v_c.card_id and coalesce(ci3.condicional,false))
            ) cond
            order by b.funcao_id,b.posicao_id,cond.nivel
            returning id,card_id,funcao_id,posicao_id,impeto_condicional_codigo,impeto_condicional_nivel
          )
          insert into clube_novo.otimizador_lote_producao_linha_v3(
            lote_id,linha_id,card_id,ordem_fila,overall_snapshot,entrada_fingerprint
          )
          select p_lote_id,i.id,i.card_id,
                 v_ordem_base+row_number() over(order by b.funcao_id,b.posicao_id,i.impeto_condicional_codigo nulls first,i.impeto_condicional_nivel nulls first,i.id),
                 v_c.overall_snapshot,
                 encode(extensions.digest(convert_to(v_entrada::text,'UTF8'),'sha256'),'hex')
          from inseridas i
          join linhas_base b
            on b.funcao_id=i.funcao_id and b.posicao_id=i.posicao_id;
          get diagnostics v_linhas_inseridas=row_count;
          if v_linhas_inseridas<>v_linhas then
            raise exception 'preparo recusado: cardinalidade de linhas divergente para card_id %',v_c.card_id;
          end if;

          update clube_novo.otimizador_lote_producao_candidata_v5
          set estado='preparada',motivo=null,preparado_em=clock_timestamp(),atualizado_em=clock_timestamp()
          where lote_id=p_lote_id and card_id=v_c.card_id;
          update clube_novo.otimizador_lote_producao_v3
          set cards=cards+1,linhas=linhas+v_linhas,
              preparo_concluido=preparo_concluido+1,atualizado_em=clock_timestamp()
          where id=p_lote_id;
        end if;
      end if;
    exception when others then
      v_motivo:=left(sqlerrm,1000);
      update clube_novo.otimizador_lote_producao_candidata_v5
      set estado='divergente',motivo=v_motivo,atualizado_em=clock_timestamp()
      where lote_id=p_lote_id and card_id=v_c.card_id;
      update clube_novo.otimizador_lote_producao_v3
      set estado='falhou',falha='preparo V5 falhou fechado: '||v_motivo,
          atualizado_em=clock_timestamp()
      where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(p_lote_id,'preparo_falhou',jsonb_build_object('card_id',v_c.card_id,'motivo',v_motivo));
      return public.otimizador_producao_status_v5(p_lote_id);
    end;
  end loop;

  select count(*) filter(where estado='pendente'),count(*) filter(where estado<>'pendente')
  into v_pendentes_preparo,v_concluidas_preparo
  from clube_novo.otimizador_lote_producao_candidata_v5
  where lote_id=p_lote_id;

  if v_pendentes_preparo=0 then
    select count(distinct card_id),count(*) into v_cards_final,v_linhas_final
    from clube_novo.otimizador_lote_producao_linha_v3
    where lote_id=p_lote_id;
    if v_linhas_final=0 then
      update clube_novo.otimizador_lote_producao_v3
      set estado='falhou',falha='preparo V5 terminou sem linha canônica apta',
          preparo_concluido=v_concluidas_preparo,atualizado_em=clock_timestamp()
      where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(p_lote_id,'preparo_falhou',jsonb_build_object('motivo','nenhuma linha apta'));
    else
      select encode(extensions.digest(convert_to(
        p_lote_id::text||':'||v_lote.formula_fingerprint||':'||v_lote.contrato_fingerprint||':'||
        v_lote.motor_versao||':'||
        string_agg(q.card_id||':'||l.funcao_id::text||':'||l.posicao_id::text||':'||q.ordem_fila::text,
                   ',' order by q.ordem_fila),
        'UTF8'),'sha256'),'hex')
      into v_fingerprint
      from clube_novo.otimizador_lote_producao_linha_v3 q
      join clube_novo.build_linha_card l on l.id = q.linha_id
      where q.lote_id=p_lote_id;
      update clube_novo.otimizador_lote_producao_v3
      set estado='parado',cards=v_cards_final,linhas=v_linhas_final,
          preparo_concluido=v_concluidas_preparo,fingerprint=v_fingerprint,
          atualizado_em=clock_timestamp()
      where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
      values(p_lote_id,'preparo_integral_concluido',jsonb_build_object(
        'cards',v_cards_final,'linhas',v_linhas_final,'fingerprint',v_fingerprint,
        'impetos_condicionais','desligados','pode_publicar',false
      ));
    end if;
  elsif v_processadas>0 then
    insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento,detalhe)
    values(p_lote_id,'preparo_fatia_concluida',jsonb_build_object(
      'candidatas_processadas',v_processadas,'pendentes_preparo',v_pendentes_preparo
    ));
  end if;
  return public.otimizador_producao_status_v5(p_lote_id);
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_pacote_local_manifesto_v2(p_lote_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '90s'
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_cartas integer;
  v_linhas integer;
  v_condicionais integer;
  v_prioridade_fingerprint text;
begin
  if p_lote_id is null then
    raise exception 'pacote local v2 recusado: lote obrigatório';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'pacote local v2 recusado: lote integral inexistente';
  end if;
  if v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint not in (
       '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
       'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070',
       '5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89'
     )
     or not coalesce((v_lote.regua_snapshot -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'pacote local v2 recusado: lote não está pausado e apto para fotografia selada';
  end if;
  if exists (
    select 1
    from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'processando'
  ) then
    raise exception 'pacote local v2 recusado: há reserva ativa no lote';
  end if;

  -- 03/09: a linha condicional deixa de derrubar o lote. Ela só entra quando
  -- traz o PAR completo — código e nível — porque é o par que diz qual dos
  -- três degraus está sendo calculado. Meio par continua sendo recusa.
  if exists (
    select 1
    from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id
      and l.estado_otimizador = 'pendente'
      and ((l.impeto_condicional_codigo is null) <> (l.impeto_condicional_nivel is null))
  ) then
    raise exception 'pacote local v2 recusado: há linha com Ímpeto condicional pela metade (código sem nível, ou o contrário)';
  end if;

  with pendentes as materialized (
    select p.* from clube_novo.otimizador_fila_prioridade_v1 p
    where p.lote_id = p_lote_id
  )
  select count(distinct card_id)::integer, count(*)::integer,
         count(*) filter(where impeto_condicional_codigo is not null)::integer,
         encode(extensions.digest(convert_to(coalesce(
           string_agg(linha_id::text||':'||ordem_fila::text||':'||prioridade_grupo::text||':'||
             coalesce(overall_prioridade::text,'null')||':'||nivel_maximo::text||':'||captura_id::text||':'||entrada_fingerprint,
             ',' order by ordem_fila),''),'UTF8'),'sha256'),'hex')
  into v_cartas,v_linhas,v_condicionais,v_prioridade_fingerprint
  from pendentes;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', v_lote.id,
    'formula_fingerprint', v_lote.formula_fingerprint,
    'contrato_fingerprint', v_lote.contrato_fingerprint,
    'motor_versao', v_lote.motor_versao,
    'lote_fingerprint', v_lote.fingerprint,
    'regua', v_lote.regua_snapshot,
    'pode_publicar', false,
    'impetos_condicionais', case when v_condicionais > 0 then 'por_degrau' else 'nenhum_no_lote' end,
    'linhas_condicionais', v_condicionais,
    'cartas_total', coalesce(v_cartas, 0),
    'linhas_total', coalesce(v_linhas, 0),
    'paginacao', 'cursor_canonico',
    'prioridade_contrato','prioridade_orcamento_v1',
    'prioridade_fingerprint', v_prioridade_fingerprint,
    'fonte', 'clube_novo.otimizador_entrada_linha_v1'
  );
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_pacote_local_cartas_v2(p_lote_id uuid, p_depois_de_card_id text DEFAULT NULL::text, p_limite integer DEFAULT 1000)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '30s'
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_itens jsonb := '[]'::jsonb;
  v_proximo_card_id text;
begin
  if p_lote_id is null or coalesce(p_limite, 0) not between 1 and 1000 then
    raise exception 'página de cartas local v2 recusada: argumentos inválidos';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false then
    raise exception 'página de cartas local v2 recusada: fotografia não está estável';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'página de cartas local v2 recusada: há reserva ativa';
  end if;

  with pagina as materialized (
    select s.card_id, s.entrada_fingerprint, s.entrada_otimizador,
           s.carta_versao_bonificador, s.carta_fingerprint_bonificador,
           c.nome as carta_nome
    from clube_novo.otimizador_lote_producao_carta_v3 s
    left join clube_novo.carta_jogo c on c.card_id = s.card_id
    where s.lote_id = p_lote_id
      and exists(select 1 from clube_novo.otimizador_fila_prioridade_v1 p where p.lote_id=s.lote_id and p.card_id=s.card_id)
      and (nullif(trim(p_depois_de_card_id), '') is null or s.card_id > p_depois_de_card_id)
    order by s.card_id
    limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'card_id', card_id,
    'carta_entrada_fingerprint', entrada_fingerprint,
    'carta', entrada_otimizador,
    'carta_nome', carta_nome,
    'carta_versao', carta_versao_bonificador,
    'carta_fingerprint', carta_fingerprint_bonificador
  ) order by card_id), '[]'::jsonb), max(card_id)
  into v_itens, v_proximo_card_id
  from pagina;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', p_lote_id,
    'depois_de_card_id', p_depois_de_card_id,
    'proximo_card_id', v_proximo_card_id,
    'limite', p_limite,
    'contagem_no_manifesto', true,
    'itens', v_itens,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados'
  );
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_pacote_local_linhas_v2(p_lote_id uuid, p_depois_de_ordem bigint DEFAULT NULL::bigint, p_limite integer DEFAULT 1000)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
 SET statement_timeout TO '30s'
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_itens jsonb := '[]'::jsonb;
  v_proxima_ordem bigint;
begin
  if p_lote_id is null or coalesce(p_limite, 0) not between 1 and 1000
     or coalesce(p_depois_de_ordem, 0) < 0 then
    raise exception 'página de linhas local v2 recusada: argumentos inválidos';
  end if;
  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id;
  if not found or v_lote.tipo_lote <> 'integral'
     or v_lote.estado <> 'pausado'
     or v_lote.preparo_concluido <> v_lote.preparo_total
     or v_lote.pode_publicar is distinct from false
     or v_lote.formula_fingerprint not in (
       '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad',
       'bf6040b6fdbbb4a6b8cf97fe66cb441507ee637ec7edb300cf2ebabb5814f070',
       '5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89'
     ) then
    raise exception 'página de linhas local v2 recusada: fotografia não está estável';
  end if;
  if exists (
    select 1 from clube_novo.build_linha_card l
    where l.lote_producao_id = p_lote_id and l.estado_otimizador = 'processando'
  ) then
    raise exception 'página de linhas local v2 recusada: há reserva ativa';
  end if;

  with pagina as materialized (
    select q.linha_id, q.ordem_fila, q.entrada_fingerprint,
           q.prioridade_grupo,q.overall_prioridade,q.nivel_maximo,q.orcamento_real,q.captura_id,
           l.card_id, l.funcao_id, l.posicao_id,
           l.impeto_condicional_codigo, l.impeto_condicional_nivel,
           c.nome as carta_nome, f.rotulo as funcao_rotulo, p.nome_pt as posicao_rotulo
    from clube_novo.otimizador_fila_prioridade_v1 q
    join clube_novo.build_linha_card l on l.id = q.linha_id
    left join clube_novo.carta_jogo c on c.card_id = l.card_id
    left join clube_novo.funcao_sistema f on f.id = l.funcao_id
    left join clube_novo.posicao_jogo p on p.id = l.posicao_id
    where q.lote_id = p_lote_id
      and (p_depois_de_ordem is null or q.ordem_fila > p_depois_de_ordem)
      and l.estado_otimizador = 'pendente'
      -- 03/09: a linha condicional entra. Só fica de fora a que veio pela
      -- metade, sem o par completo que identifica o degrau.
      and ((l.impeto_condicional_codigo is null) = (l.impeto_condicional_nivel is null))
    order by q.ordem_fila
    limit p_limite
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'linha_id', linha_id,
    'ordem_fila', ordem_fila,
    'prioridade_grupo',prioridade_grupo,'overall_prioridade',overall_prioridade,
    'nivel_maximo',nivel_maximo,'orcamento_real',orcamento_real,'captura_id',captura_id,
    'card_id', card_id,
    'funcao_id', funcao_id,
    'posicao_id', posicao_id,
    'carta_entrada_fingerprint', entrada_fingerprint,
    'carta_nome', carta_nome,
    'funcao_rotulo', funcao_rotulo,
    'posicao_rotulo', posicao_rotulo,
    'impeto_condicional_codigo', impeto_condicional_codigo,
    'impeto_condicional_nivel', impeto_condicional_nivel
  ) order by ordem_fila), '[]'::jsonb), max(ordem_fila)
  into v_itens, v_proxima_ordem
  from pagina;

  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v2',
    'lote_id', p_lote_id,
    'depois_de_ordem', p_depois_de_ordem,
    'proxima_ordem_fila', v_proxima_ordem,
    'limite', p_limite,
    'contagem_no_manifesto', true,
    'itens', v_itens,
    'pode_publicar', false,
    'impetos_condicionais', 'por_degrau'
  );
end
$function$
;
CREATE OR REPLACE FUNCTION public.otimizador_producao_reservar_entrada_v7(p_lote_id uuid, p_worker_id uuid, p_formula_fingerprint text, p_motor_versao text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_entrada record;
  v_token uuid;
begin
  if p_worker_id is null
     or nullif(trim(coalesce(p_formula_fingerprint, '')), '') is null
     or nullif(trim(coalesce(p_motor_versao, '')), '') is null then
    raise exception 'reserva V7 recusada: worker, fórmula e versão são obrigatórios';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;

  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'reserva V7 recusada: lote integral inexistente';
  end if;
  if v_lote.formula_fingerprint <> p_formula_fingerprint
     or v_lote.motor_versao <> p_motor_versao
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad'
     or v_lote.pode_publicar is distinct from false then
    raise exception 'reserva V7 recusada: selo da fórmula/versão/publicação não confere';
  end if;
  if v_lote.estado <> 'rodando' then
    return jsonb_build_object(
      'contrato', 'otimizador_entrada_linha_v1',
      'reservada', false,
      'estado_lote', v_lote.estado
    );
  end if;

  select q.* into v_q
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id = q.linha_id
  where q.lote_id = p_lote_id
    and l.estado_otimizador = 'pendente'
    and exists(select 1 from clube_novo.otimizador_fila_prioridade_v1 p where p.linha_id=q.linha_id)
  order by q.ordem_fila
  for update of q, l skip locked
  limit 1;

  if not found then
    if v_lote.preparo_concluido < v_lote.preparo_total then
      return jsonb_build_object(
        'contrato', 'otimizador_entrada_linha_v1',
        'reservada', false,
        'estado_lote', 'rodando',
        'aguardando_preparo', true
      );
    end if;
    if not exists (
      select 1
      from clube_novo.otimizador_lote_producao_linha_v3 q2
      join clube_novo.build_linha_card l2 on l2.id = q2.linha_id
      where q2.lote_id = p_lote_id
        and l2.estado_otimizador in ('pendente', 'processando')
    ) then
      update clube_novo.otimizador_lote_producao_v3
      set estado = 'concluido', finalizado_em = clock_timestamp(), atualizado_em = clock_timestamp()
      where id = p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id, evento)
      values(p_lote_id, 'lote_concluido');
      return jsonb_build_object(
        'contrato', 'otimizador_entrada_linha_v1',
        'reservada', false,
        'estado_lote', 'concluido'
      );
    end if;
    return jsonb_build_object(
      'contrato', 'otimizador_entrada_linha_v1',
      'reservada', false,
      'estado_lote', 'rodando'
    );
  end if;

  select * into v_entrada
  from clube_novo.otimizador_entrada_linha_v1 e
  where e.lote_id = p_lote_id and e.linha_id = v_q.linha_id;

  if not found
     or v_entrada.card_id <> v_q.card_id
     or v_entrada.carta_entrada_fingerprint <> v_q.entrada_fingerprint
     or v_entrada.snapshot_entrada_fingerprint <> v_q.entrada_fingerprint
     or v_entrada.carta is null
     or v_entrada.impeto_condicional_codigo is not null
     or v_entrada.impeto_condicional_nivel is not null
     or not coalesce((v_entrada.regua -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'reserva V7 recusada: fotografia única da entrada não passou os gates';
  end if;

  v_token := extensions.gen_random_uuid();
  update clube_novo.otimizador_lote_producao_linha_v3
  set reserva_token = v_token,
      worker_id = p_worker_id,
      reservada_em = clock_timestamp(),
      tentativas = tentativas + 1
  where lote_id = p_lote_id and linha_id = v_q.linha_id;

  update clube_novo.build_linha_card
  set estado_otimizador = 'processando',
      erro_otimizador = null,
      otimizador_iniciado_em = clock_timestamp(),
      atualizado_em = clock_timestamp()
  where id = v_q.linha_id and estado_otimizador = 'pendente';

  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  values(
    p_lote_id,
    v_q.linha_id,
    'linha_reservada',
    jsonb_build_object(
      'worker_id', p_worker_id,
      'ordem_fila', v_q.ordem_fila,
      'contrato_entrada_v7', true,
      'origem', 'clube_novo.otimizador_entrada_linha_v1'
    )
  );

  return jsonb_build_object(
    'contrato', 'otimizador_entrada_linha_v1',
    'reservada', true,
    'lote_id', v_entrada.lote_id,
    'linha_id', v_entrada.linha_id,
    'reserva_token', v_token,
    'ordem_fila', v_entrada.ordem_fila,
    'card_id', v_entrada.card_id,
    'funcao_id', v_entrada.funcao_id,
    'posicao_id', v_entrada.posicao_id,
    'impeto_condicional_codigo', null,
    'impeto_condicional_nivel', null,
    'carta', v_entrada.carta,
    'carta_entrada_fingerprint', v_entrada.carta_entrada_fingerprint,
    'formula_fingerprint', v_entrada.formula_fingerprint,
    'contrato_fingerprint', v_entrada.contrato_fingerprint,
    'motor_versao', v_entrada.motor_versao,
    'lote_fingerprint', v_entrada.lote_fingerprint,
    'carta_versao', v_entrada.carta_versao,
    'carta_fingerprint', v_entrada.carta_fingerprint,
    'regua', v_entrada.regua,
    'impetos_condicionais', 'desligados'
  );
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_reservar_linha_local_v1(p_lote_id uuid, p_worker_id uuid, p_linha_id bigint, p_card_id text, p_funcao_id bigint, p_posicao_id integer, p_carta_entrada_fingerprint text, p_formula_fingerprint text, p_contrato_fingerprint text, p_motor_versao text, p_lote_fingerprint text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_token uuid;
begin
  if p_lote_id is null or p_worker_id is null or p_linha_id is null
     or nullif(trim(coalesce(p_card_id, '')), '') is null
     or p_funcao_id is null or p_posicao_id is null
     or nullif(trim(coalesce(p_carta_entrada_fingerprint, '')), '') is null
     or nullif(trim(coalesce(p_formula_fingerprint, '')), '') is null
     or nullif(trim(coalesce(p_contrato_fingerprint, '')), '') is null
     or nullif(trim(coalesce(p_motor_versao, '')), '') is null
     or nullif(trim(coalesce(p_lote_fingerprint, '')), '') is null then
    raise exception 'reserva local recusada: identidade e selos são obrigatórios';
  end if;

  select * into v_lote
  from clube_novo.otimizador_lote_producao_v3
  where id = p_lote_id
  for update;
  if not found or v_lote.tipo_lote <> 'integral' then
    raise exception 'reserva local recusada: lote integral inexistente';
  end if;
  if v_lote.formula_fingerprint <> p_formula_fingerprint
     or v_lote.contrato_fingerprint <> p_contrato_fingerprint
     or v_lote.motor_versao <> p_motor_versao
     or v_lote.fingerprint <> p_lote_fingerprint
     or v_lote.formula_fingerprint <> '7aaa3cccb536ae8fbe77a3fd91a447738132d6f1b89706bc375314e8028a80ad'
     or v_lote.pode_publicar is distinct from false then
    raise exception 'reserva local recusada: selo do pacote diverge do lote';
  end if;
  if v_lote.estado <> 'rodando' then
    return jsonb_build_object(
      'contrato', 'otimizador_pacote_local_v1', 'reservada', false,
      'estado_lote', v_lote.estado, 'pode_publicar', false
    );
  end if;

  select * into v_q
  from clube_novo.otimizador_lote_producao_linha_v3
  where lote_id = p_lote_id and linha_id = p_linha_id
  for update;
  select * into v_l
  from clube_novo.build_linha_card
  where id = p_linha_id
  for update;
  if v_q.linha_id is null or v_l.id is null then
    raise exception 'reserva local recusada: linha inexistente';
  end if;
  if not exists(select 1 from clube_novo.otimizador_fila_prioridade_v1 p where p.linha_id=p_linha_id and p.lote_id=p_lote_id) then
    raise exception 'reserva local recusada: orçamento sem prova ou entrada divergente';
  end if;
  if v_l.lote_producao_id <> p_lote_id or v_q.card_id <> v_l.card_id then
    raise exception 'reserva local recusada: vínculo canônico da linha diverge';
  end if;
  if v_l.estado_otimizador <> 'pendente' then
    return jsonb_build_object(
      'contrato', 'otimizador_pacote_local_v1', 'reservada', false,
      'estado_lote', v_lote.estado, 'linha_estado', v_l.estado_otimizador,
      'pode_publicar', false
    );
  end if;
  if v_l.card_id <> p_card_id
     or v_l.funcao_id <> p_funcao_id
     or v_l.posicao_id <> p_posicao_id
     or v_q.entrada_fingerprint <> p_carta_entrada_fingerprint
     or v_l.impeto_condicional_codigo is not null
     or v_l.impeto_condicional_nivel is not null
     or not exists (
       select 1
       from clube_novo.otimizador_lote_producao_carta_v3 s
       where s.lote_id = p_lote_id and s.card_id = v_l.card_id
         and s.entrada_fingerprint = v_q.entrada_fingerprint
         and s.entrada_otimizador is not null
     )
     or not coalesce((v_lote.regua_snapshot -> 'gate' ->> 'pode_rodar')::boolean, false) then
    raise exception 'reserva local recusada: fotografia/gates canônicos divergentes';
  end if;

  v_token := extensions.gen_random_uuid();
  update clube_novo.otimizador_lote_producao_linha_v3
  set reserva_token = v_token,
      worker_id = p_worker_id,
      reservada_em = clock_timestamp(),
      tentativas = tentativas + 1
  where lote_id = p_lote_id and linha_id = p_linha_id;
  update clube_novo.build_linha_card
  set estado_otimizador = 'processando',
      erro_otimizador = null,
      otimizador_iniciado_em = clock_timestamp(),
      atualizado_em = clock_timestamp()
  where id = p_linha_id and estado_otimizador = 'pendente';
  insert into clube_novo.otimizador_evento_producao_v3(lote_id, linha_id, evento, detalhe)
  values(
    p_lote_id, p_linha_id, 'linha_reservada',
    jsonb_build_object(
      'worker_id', p_worker_id,
      'ordem_fila', v_q.ordem_fila,
      'pacote_local_v1', true,
      'origem', 'clube_novo.otimizador_entrada_linha_v1'
    )
  );
  return jsonb_build_object(
    'contrato', 'otimizador_pacote_local_v1',
    'reservada', true,
    'lote_id', p_lote_id,
    'linha_id', p_linha_id,
    'ordem_fila', v_q.ordem_fila,
    'reserva_token', v_token,
    'card_id', v_l.card_id,
    'funcao_id', v_l.funcao_id,
    'posicao_id', v_l.posicao_id,
    'carta_entrada_fingerprint', v_q.entrada_fingerprint,
    'pode_publicar', false,
    'impetos_condicionais', 'desligados'
  );
end
$function$
;

CREATE OR REPLACE FUNCTION public.otimizador_producao_reservar_linha_v3(p_lote_id uuid, p_worker_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare v_lote clube_novo.otimizador_lote_producao_v3%rowtype;
  v_q clube_novo.otimizador_lote_producao_linha_v3%rowtype;
  v_l clube_novo.build_linha_card%rowtype;
  v_c clube_novo.otimizador_lote_producao_carta_v3%rowtype;
  v_token uuid;
begin
  if p_worker_id is null then raise exception 'worker_id obrigatório'; end if;
  select * into v_lote from clube_novo.otimizador_lote_producao_v3 where id=p_lote_id for update;
  if not found then raise exception 'lote V3 inexistente'; end if;
  if v_lote.estado<>'rodando' then
    return jsonb_build_object('contrato','otimizador_fila_producao_v3','reservada',false,'estado_lote',v_lote.estado);
  end if;
  select q.* into v_q
  from clube_novo.otimizador_lote_producao_linha_v3 q
  join clube_novo.build_linha_card l on l.id=q.linha_id
  where q.lote_id=p_lote_id and l.estado_otimizador='pendente'
    and exists(select 1 from clube_novo.otimizador_fila_prioridade_v1 p where p.linha_id=q.linha_id)
  order by q.ordem_fila
  for update of q,l skip locked
  limit 1;
  if not found then
    if not exists(select 1 from clube_novo.otimizador_lote_producao_linha_v3 q join clube_novo.build_linha_card l on l.id=q.linha_id where q.lote_id=p_lote_id and l.estado_otimizador in ('pendente','processando')) then
      update clube_novo.otimizador_lote_producao_v3 set estado='concluido',finalizado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=p_lote_id;
      insert into clube_novo.otimizador_evento_producao_v3(lote_id,evento) values(p_lote_id,'lote_concluido');
      return jsonb_build_object('contrato','otimizador_fila_producao_v3','reservada',false,'estado_lote','concluido');
    end if;
    return jsonb_build_object('contrato','otimizador_fila_producao_v3','reservada',false,'estado_lote','rodando');
  end if;
  select * into v_l from clube_novo.build_linha_card where id=v_q.linha_id;
  select * into v_c from clube_novo.otimizador_lote_producao_carta_v3 where lote_id=p_lote_id and card_id=v_q.card_id;
  if not found or v_c.entrada_fingerprint<>v_q.entrada_fingerprint then
    raise exception 'reserva recusada: snapshot de entrada inconsistente';
  end if;
  v_token:=extensions.gen_random_uuid();
  update clube_novo.otimizador_lote_producao_linha_v3 set reserva_token=v_token,worker_id=p_worker_id,reservada_em=clock_timestamp(),tentativas=tentativas+1 where lote_id=p_lote_id and linha_id=v_q.linha_id;
  update clube_novo.build_linha_card set estado_otimizador='processando',erro_otimizador=null,otimizador_iniciado_em=clock_timestamp(),atualizado_em=clock_timestamp() where id=v_q.linha_id and estado_otimizador='pendente';
  insert into clube_novo.otimizador_evento_producao_v3(lote_id,linha_id,evento,detalhe) values(p_lote_id,v_q.linha_id,'linha_reservada',jsonb_build_object('worker_id',p_worker_id,'ordem_fila',v_q.ordem_fila));
  return jsonb_build_object(
    'contrato','otimizador_fila_producao_v3','reservada',true,'lote_id',p_lote_id,
    'linha_id',v_q.linha_id,'reserva_token',v_token,'ordem_fila',v_q.ordem_fila,
    'card_id',v_l.card_id,'funcao_id',v_l.funcao_id,'posicao_id',v_l.posicao_id,
    'impeto_condicional_codigo',null,'impeto_condicional_nivel',null,
    'carta',v_c.entrada_otimizador,'carta_entrada_fingerprint',v_c.entrada_fingerprint,
    'formula_fingerprint',v_lote.formula_fingerprint,'contrato_fingerprint',v_lote.contrato_fingerprint,
    'motor_versao',v_lote.motor_versao,'lote_fingerprint',v_lote.fingerprint,
    'carta_versao',v_l.carta_versao,'carta_fingerprint',v_l.carta_fingerprint,
    'impetos_condicionais','desligados'
  );
end
$function$
;
commit;
