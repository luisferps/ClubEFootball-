-- Preparação da integração por lote; aplicar/testar antes de usar em produção.
create table if not exists clube_novo.bonificador_reaproveitamento_lote_v1 (
 lote_id uuid not null references clube_novo.otimizador_lote_producao_v3(id),
 linha_id bigint primary key references clube_novo.build_linha_card(id),
 estado text not null check(estado in ('reaproveitado','recalcular','bloqueado')),
 origem_linha_id bigint references clube_novo.build_linha_card(id),
 origem_bonus_id bigint references clube_novo.build_bonificador(id),
 entrada_fingerprint text not null,
 regra_fingerprint text not null,
 motivo text not null,
 prova jsonb not null default '{}'::jsonb,
 conferido_em timestamptz not null default now()
);
create index if not exists bonificador_reaproveitamento_lote_estado_idx
 on clube_novo.bonificador_reaproveitamento_lote_v1(lote_id,estado,linha_id);
alter table clube_novo.bonificador_reaproveitamento_lote_v1 enable row level security;
revoke all on clube_novo.bonificador_reaproveitamento_lote_v1 from public,anon,authenticated;

create or replace function clube_novo.reaproveitar_bonificador_lote_fatia_v1(p_lote uuid,p_limite integer default 25)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
 lote clube_novo.otimizador_lote_producao_v3%rowtype;
 d clube_novo.build_linha_card%rowtype;
 fonte record;
 antes clube_novo.recalculo_1209_entrada_antes_v1%rowtype;
 entrada jsonb; esperado jsonb; prova jsonb; erro text; regra text;
 estado_item text; motivo_item text; antes_igual boolean;
 processadas integer:=0; reutilizadas integer:=0; recalcular integer:=0; bloqueadas integer:=0;
 origem_linha bigint; origem_bonus bigint;
begin
 if p_lote is null or p_limite is null or p_limite not between 1 and 100 then
  raise exception 'Lote explícito e limite de 1 a 100 obrigatórios';
 end if;
 perform pg_advisory_xact_lock(hashtextextended('reaproveitar-bonus-lote:'||p_lote::text,0));
 select * into lote from clube_novo.otimizador_lote_producao_v3 where id=p_lote for share;
 if not found or lote.estado<>'pausado' or lote.tipo_lote<>'integral'
    or lote.preparo_fingerprint_final is null
    or lote.contrato_fingerprint is distinct from clube_novo.otimizador_producao_contrato_fingerprint_v3(public.otimizador_regua_v2()) then
  raise exception 'Reaproveitamento exige lote integral preparado, pausado e da régua vigente';
 end if;
 regra:=clube_novo.bonificador_conferencia_regra_fingerprint_v1();
 for d in
  select l.* from clube_novo.build_linha_card l
  where l.lote_producao_id=p_lote and l.execucao_tipo='producao'
   and l.lote_teste_id is null and l.estado<>'invalida' and l.estado_otimizador<>'interrompido' and l.build_bonificador_id is null
   and not exists(select 1 from clube_novo.bonificador_reaproveitamento_lote_v1 a
     where a.linha_id=l.id and a.entrada_fingerprint=l.carta_fingerprint and a.regra_fingerprint=regra)
  order by l.id limit p_limite
 loop
  processadas:=processadas+1; origem_linha:=null; origem_bonus:=null; prova:='{}'::jsonb;
  estado_item:='recalcular'; motivo_item:='Nenhum resultado com identidade, entradas e componentes vigentes comprovados';
  begin
   entrada:=clube_novo.bonificador_carta_v1(d.card_id);
   if coalesce((entrada->>'pode_rodar')::boolean,false)=false
      or d.carta_fingerprint is distinct from clube_novo.bonificador_carta_fingerprint_v1(d.card_id)
      or not exists(select 1 from clube_novo.carta_jogo c where c.card_id=d.card_id and c.roda_motor
          and not coalesce(c.jogador_indisponivel,false) and c.extraido_em::text=d.carta_versao) then
    raise exception 'Entrada destino indisponível, incompleta ou fora da versão vigente';
   end if;
   esperado:=clube_novo.bonificador_componentes_vigentes_v1(d.card_id,d.funcao_id,d.posicao_id);
   select * into antes from clube_novo.recalculo_1209_entrada_antes_v1 where card_id=d.card_id;
   antes_igual:=found and coalesce((antes.entrada_bonificador->>'pode_rodar')::boolean,false)
     and (antes.entrada_bonificador-array['nome','slot1_nome','slot2_nome','proveniencia'])
       is not distinct from (entrada-array['nome','slot1_nome','slot2_nome','proveniencia']);
   for fonte in
    select s.id linha_id,b.id bonus_id
    from clube_novo.build_linha_card s
    cross join lateral (
      select s.build_bonificador_id id,2 prioridade
      union all select v.novo_id,0 from clube_novo.bonificador_altura_ia_sucessor_v13 v where v.linha_id=s.id
      union all select i.build_bonificador_id_novo,1 from clube_novo.bonificador_correcao_item_v1 i
        where i.build_linha_card_id=s.id and i.estado_item='preparado'
    ) candidato
    join clube_novo.build_bonificador b on b.id=candidato.id
    where s.id<>d.id and s.card_id=d.card_id and s.funcao_id=d.funcao_id and s.posicao_id=d.posicao_id
      and s.execucao_tipo='producao' and s.lote_teste_id is null
      and s.impeto_condicional_codigo is not distinct from d.impeto_condicional_codigo
      and s.impeto_condicional_nivel is not distinct from d.impeto_condicional_nivel
      and b.carta_fingerprint=s.carta_fingerprint and b.carta_versao=s.carta_versao
      and b.entrada_bonificador_fingerprint=b.carta_fingerprint
      and ((b.carta_fingerprint=d.carta_fingerprint and b.carta_versao=d.carta_versao)
        or (antes_igual and b.carta_fingerprint=antes.carta_fingerprint
             and b.carta_versao=(antes.carta->>'extraido_em')::timestamptz::text))
      and clube_novo.bonificador_resultado_conforme_componentes_v1(to_jsonb(b),esperado)
    order by candidato.prioridade,b.id desc,s.id desc
   loop
    prova:=clube_novo.reaproveitar_bonificador_conforme_v1(d.id,fonte.linha_id,fonte.bonus_id,'lote-integral:'||p_lote::text);
    origem_linha:=fonte.linha_id; origem_bonus:=fonte.bonus_id;
    estado_item:='reaproveitado'; motivo_item:='Valores preservados; entradas e componentes conferidos';
    exit;
   end loop;
  exception when others then
   estado_item:='bloqueado'; motivo_item:=sqlerrm; prova:=jsonb_build_object('sqlstate',sqlstate);
  end;
  insert into clube_novo.bonificador_reaproveitamento_lote_v1
   (lote_id,linha_id,estado,origem_linha_id,origem_bonus_id,entrada_fingerprint,regra_fingerprint,motivo,prova)
  values(p_lote,d.id,estado_item,origem_linha,origem_bonus,d.carta_fingerprint,regra,motivo_item,prova)
  on conflict(linha_id) do update set estado=excluded.estado,origem_linha_id=excluded.origem_linha_id,
   origem_bonus_id=excluded.origem_bonus_id,entrada_fingerprint=excluded.entrada_fingerprint,
   regra_fingerprint=excluded.regra_fingerprint,motivo=excluded.motivo,prova=excluded.prova,conferido_em=now();
  if estado_item='reaproveitado' then reutilizadas:=reutilizadas+1;
  elsif estado_item='recalcular' then recalcular:=recalcular+1; else bloqueadas:=bloqueadas+1; end if;
 end loop;
 return jsonb_build_object('lote_id',p_lote,'processadas',processadas,'reaproveitadas',reutilizadas,
   'recalcular',recalcular,'bloqueadas',bloqueadas,'sem_recalculo',true);
end $$;
revoke all on function clube_novo.reaproveitar_bonificador_lote_fatia_v1(uuid,integer) from public,anon,authenticated;
