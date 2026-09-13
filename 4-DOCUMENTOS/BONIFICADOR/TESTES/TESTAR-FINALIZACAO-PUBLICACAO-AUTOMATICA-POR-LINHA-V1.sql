select public.site_novo_publicacao_status_v1('89136409091415');

select estado,count(*)
from clube_novo.build_finalizacao_fila_v1
group by estado order by estado;

select count(*) as linhas_ativas,
       count(*) filter(where b.motor_versao<>'v10-0409-fisico-regra-aprovada-v1'
         or b.formula_fingerprint<>'756e9b49160dfc640cf278ccc172219987526e091fed9dd3d37a243ed9c01a0b')
         as linhas_fora_v10,
       count(*) filter(where jsonb_typeof(o.atributos_finais)<>'array'
         or jsonb_array_length(o.atributos_finais)<>26) as linhas_sem_26,
       count(*) filter(where a.nota_final<>d.overall_final) as notas_divergentes
from clube_novo.build_publicacao_linha_ativa_v1 a
join clube_novo.build_bonificador b on b.id=a.build_bonificador_id
join clube_novo.build_otimizador o on o.id=a.build_otimizador_id
join clube_novo.build_pontuacao_final_v2_delta_v1 d on d.linha_id=a.linha_id;

select * from public.frontend_build_publicada_v2(null,null,10,0);

select public.site_novo_ficha_v1(
  (select card_id from clube_novo.build_publicacao_linha_ativa_v1 order by atualizado_em desc limit 1),
  null
);

-- Regra estrutural: a rota global removida nao pode reaparecer no catalogo
-- nem ser chamada por outra funcao viva.
do $do$
declare v_referencias integer;
begin
  if to_regprocedure('clube_novo.publicar_e_normalizar_v2(integer,boolean)') is not null
     or to_regprocedure('clube_novo.atualizar_lista_publicada_v1()') is not null
     or to_regclass('clube_novo.build_pontuacao_final_v2_mat') is not null
     or to_regprocedure('public.bonificador_correcao_cortar_v1(uuid)') is not null
     or to_regprocedure('public.bonificador_correcao_reverter_v1(uuid)') is not null then
    raise exception 'rota global/manual removida reapareceu no catalogo';
  end if;
  select count(*) into v_referencias
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where p.prokind='f' and (
    pg_get_functiondef(p.oid) ilike '%clube_novo.publicar_e_normalizar_v2%'
    or pg_get_functiondef(p.oid) ilike '%clube_novo.atualizar_lista_publicada_v1%'
    or pg_get_functiondef(p.oid) ilike '%clube_novo.build_pontuacao_final_v2_mat%'
  );
  if v_referencias<>0 then
    raise exception 'ha % funcao(oes) viva(s) referindo a rota removida',v_referencias;
  end if;
end
$do$;

select count(*) as v9_ativas
from clube_novo.build_publicacao_linha_ativa_v1 a
join clube_novo.build_bonificador b on b.id=a.build_bonificador_id
where b.motor_versao<>'v10-0409-fisico-regra-aprovada-v1';

select count(*) as composicoes_incorretas
from clube_novo.build_publicacao_linha_ativa_v1 a
join clube_novo.build_linha_card l on l.id=a.linha_id
where l.nota_final is distinct from l.nota_do_motor+l.nota_bonus_total
   or a.nota_final is distinct from l.nota_final;

-- Prova transacional das duas ordens de chegada, complemento posterior,
-- idempotencia e preservacao da ponte. Tudo e revertido ao final.
begin;
do $do$
declare
  v_linha bigint; v_otimizador bigint; v_bonificador bigint; v_lote uuid;
  v_eventos integer; v_eventos_depois integer; v_r1 jsonb; v_r2 jsonb;
begin
  select a.linha_id,a.build_otimizador_id,a.build_bonificador_id,i.lote_id
  into v_linha,v_otimizador,v_bonificador,v_lote
  from clube_novo.build_publicacao_linha_ativa_v1 a
  join clube_novo.bonificador_correcao_item_v1 i
    on i.build_linha_card_id=a.linha_id
   and i.build_bonificador_id_novo=a.build_bonificador_id
   and i.estado_item='preparado'
  order by a.atualizado_em desc limit 1;
  if v_linha is null then raise exception 'sem linha publicada para o teste funcional'; end if;

  select count(*) into v_eventos from clube_novo.build_finalizacao_evento_v1
  where linha_id=v_linha and evento='publicada';
  v_r1:=clube_novo.finalizar_publicar_linha_v1(v_linha,'teste_idempotencia_1');
  v_r2:=clube_novo.finalizar_publicar_linha_v1(v_linha,'teste_idempotencia_2');
  select count(*) into v_eventos_depois from clube_novo.build_finalizacao_evento_v1
  where linha_id=v_linha and evento='publicada';
  if v_r1->>'estado'<>'ja_publicada' or v_r2->>'estado'<>'ja_publicada'
     or v_eventos_depois<>v_eventos then
    raise exception 'idempotencia falhou';
  end if;

  -- Bonificador ja existe; Otimizador chega por ultimo.
  update clube_novo.build_linha_card set build_otimizador_id=null where id=v_linha;
  if not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=v_linha) then
    raise exception 'ponte ativa sumiu enquanto aguardava Otimizador';
  end if;
  update clube_novo.build_linha_card set build_otimizador_id=v_otimizador where id=v_linha;
  if not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1
    where linha_id=v_linha and build_otimizador_id=v_otimizador) then
    raise exception 'chegada do Otimizador nao finalizou';
  end if;

  -- Otimizador ja existe; Bonificador chega por ultimo pelo writer corretivo.
  update clube_novo.bonificador_correcao_item_v1
  set estado_item='pendente',build_bonificador_id_novo=null where lote_id=v_lote and build_linha_card_id=v_linha;
  update clube_novo.build_linha_card set build_bonificador_id=null where id=v_linha;
  if not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=v_linha) then
    raise exception 'ponte ativa sumiu enquanto aguardava Bonificador';
  end if;
  update clube_novo.bonificador_correcao_item_v1
  set estado_item='preparado',build_bonificador_id_novo=v_bonificador
  where lote_id=v_lote and build_linha_card_id=v_linha;
  if not exists(select 1 from clube_novo.build_linha_card l
    join clube_novo.build_publicacao_linha_ativa_v1 a on a.linha_id=l.id
    where l.id=v_linha and l.build_bonificador_id=v_bonificador
      and a.build_bonificador_id=v_bonificador) then
    raise exception 'chegada do Bonificador nao finalizou';
  end if;
end
$do$;
rollback;

do $do$
declare v_def text; v_trigger integer;
begin
  select pg_get_functiondef('public.finalizacao_publica_tick_v1(integer)'::regprocedure)
  into v_def;
  if position('FOR UPDATE SKIP LOCKED' in upper(v_def))=0 then
    raise exception 'tick perdeu a trava concorrente SKIP LOCKED';
  end if;
  select count(*) into v_trigger
  from pg_trigger t join pg_proc p on p.oid=t.tgfoid
  join pg_namespace n on n.oid=p.pronamespace
  where t.tgrelid='clube_novo.build_otimizador'::regclass
    and not t.tgisinternal
    and t.tgname='otimizador_vals_finalizar_automatico_v1'
    and n.nspname='clube_novo'
    and p.proname='disparar_finalizacao_otimizador_vals_v1';
  if v_trigger<>1 then
    raise exception 'gatilho do complemento posterior nao esta instalado';
  end if;
end
$do$;
