create table if not exists clube_novo.correcao_altura_ia_v13 (
 linha_id bigint primary key, antigo_id bigint not null, novo_id bigint,
 estado text not null default 'pendente' check(estado in('pendente','concluida','erro','aguardando_otimizador')),
 era_publicada boolean not null, erro text, criado_em timestamptz not null default now(),
 concluida_em timestamptz
);
alter table clube_novo.correcao_altura_ia_v13 drop constraint if exists correcao_altura_ia_v13_estado_check;
alter table clube_novo.correcao_altura_ia_v13 add constraint correcao_altura_ia_v13_estado_check check(estado in('pendente','concluida','erro','aguardando_otimizador'));
create index if not exists correcao_altura_ia_estado on clube_novo.correcao_altura_ia_v13(estado,era_publicada desc,linha_id);
alter table clube_novo.correcao_altura_ia_v13 enable row level security;
revoke all on clube_novo.correcao_altura_ia_v13 from public,anon,authenticated;
create table if not exists clube_novo.bonificador_altura_ia_sucessor_v13 (
 linha_id bigint not null,antigo_id bigint not null,novo_id bigint not null,
 altura_anterior numeric not null,altura_nova numeric not null,ia_anterior numeric not null,ia_nova numeric not null,
 criado_em timestamptz not null default now(), primary key(linha_id,antigo_id)
);
alter table clube_novo.bonificador_altura_ia_sucessor_v13 enable row level security;
revoke all on clube_novo.bonificador_altura_ia_sucessor_v13 from public,anon,authenticated;

create or replace function clube_novo.corrigir_altura_ia_resultado_v13(p_linha bigint,p_antigo bigint)
returns bigint language plpgsql security definer set search_path='' as $$
declare l clube_novo.build_linha_card%rowtype;b clube_novo.build_bonificador%rowtype;
 n bigint;h jsonb;ia numeric;fp text;total numeric;den numeric;novo bigint;
begin
 select * into l from clube_novo.build_linha_card where id=p_linha for update;
 select * into b from clube_novo.build_bonificador where id=p_antigo;
 if l.id is null or b.id is null then raise exception 'Linha ou resultado ausente';end if;
 if b.motor_versao='v13-1009-altura-ia-v1' then return b.id;end if;
 select novo_id into novo from clube_novo.bonificador_altura_ia_sucessor_v13 where linha_id=l.id and antigo_id=b.id;
 if novo is not null then return novo;end if;
 if not clube_novo.bonus_estilo_conforme_v12(b.id,l.card_id,l.funcao_id,l.posicao_id)
  or b.carta_fingerprint is distinct from l.carta_fingerprint
  or b.entrada_bonificador_fingerprint is distinct from l.carta_fingerprint
  or b.carta_versao is distinct from l.carta_versao or coalesce(cardinality(b.faltou),-1)<>0 then
  raise exception 'Base incompatível: identidade ou estilos não conferem';end if;
 if not (l.build_bonificador_id=b.id or exists(select 1 from clube_novo.bonificador_correcao_item_v1 i where i.build_linha_card_id=l.id and i.build_bonificador_id_novo=b.id and i.estado_item='preparado')) then
  raise exception 'Resultado não é referência vigente';end if;
 h:=clube_novo.separar_altura_v1(b.bonus_fisico_detalhe,l.funcao_id,true);
 select count(distinct bit_estilo_ia) into n from clube_novo.carta_estilo_ia_jogo where card_id=l.card_id;
 ia:=least(n,5)*0.1;
 total:=round(b.bonus_total+(h->>'delta')::numeric-b.bonus_ia+ia,4);
 select sum(2*(x->>'peso')::numeric) into den
 from clube_novo.bonificador_altura_politica_v1 p,jsonb_array_elements(p.regra->'molde_base')x
 where p.versao='altura-independente-20260909-v1' and (x->>'funcao_id')::bigint=l.funcao_id and (x->>'direcao')::int<>0;
 if den is null or den<=0 then raise exception 'Referência física congelada ausente';end if;
 fp:=encode(extensions.digest(jsonb_build_object('regra','afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f',
 'linha',l.id,'base',b.resultado_fingerprint,'altura',h,'ia',ia)::text,'sha256'),'hex');
 insert into clube_novo.build_bonificador(bonus_pe,bonus_fisico_total,bonus_posicao,bonus_playstyle_1,bonus_playstyle_2,bonus_ia,bonus_outros,bonus_total,
 contrato_versao,contrato_fingerprint,carta_versao,carta_fingerprint,formula_fingerprint,resultado_fingerprint,concluido_em,bonus_fisico_detalhe,
 motor_versao,b_corpo,b_pe_ruim,b_estilo,b_total,faltou,corpo_soma,corpo_pct,entrada_bonificador_fingerprint)
 values(b.bonus_pe,(h->>'total')::numeric,b.bonus_posicao,b.bonus_playstyle_1,b.bonus_playstyle_2,ia,b.bonus_outros,total,
 'bonificador-altura-ia-v13','afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f',b.carta_versao,b.carta_fingerprint,
 'afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f',fp,clock_timestamp(),h->'detalhe',
 'v13-1009-altura-ia-v1',(h->>'total')::numeric,b.b_pe_ruim,b.b_estilo,total,b.faltou,
 (h->>'total')::numeric/1.5*den,round((h->>'total')::numeric/1.5,4),b.entrada_bonificador_fingerprint)
 on conflict(resultado_fingerprint) do nothing returning id into novo;
 if novo is null then select id into novo from clube_novo.build_bonificador where resultado_fingerprint=fp;end if;
 if not exists(select 1 from clube_novo.build_bonificador x where x.id=novo
  and x.bonus_fisico_detalhe-'altura'=b.bonus_fisico_detalhe-'altura'
  and (x.bonus_pe,x.bonus_posicao,x.bonus_playstyle_1,x.bonus_playstyle_2,x.bonus_outros) is not distinct from
      (b.bonus_pe,b.bonus_posicao,b.bonus_playstyle_1,b.bonus_playstyle_2,b.bonus_outros)
  and x.bonus_total=total and x.bonus_ia=ia) then raise exception 'Readback das parcelas falhou';end if;
 insert into clube_novo.bonificador_altura_ia_sucessor_v13 values(l.id,b.id,novo,(h->>'altura_anterior')::numeric,(h->>'altura')::numeric,b.bonus_ia,ia,clock_timestamp());
 return novo;
end $$;
revoke all on function clube_novo.corrigir_altura_ia_resultado_v13(bigint,bigint) from public,anon,authenticated;

create or replace function public.correcao_altura_ia_status_v13()
returns jsonb language sql stable security definer set search_path='' as $$
select jsonb_build_object('contrato','correcao-altura-ia-v13','preparada',count(*)>0,'total',count(*),
 'corrigidas',count(*) filter(where estado in('concluida','aguardando_otimizador')),'aguardando_otimizador',count(*) filter(where estado='aguardando_otimizador'),'concluidas',count(*) filter(where estado='concluida'),
 'publicacoes_total',count(*) filter(where era_publicada),'publicacoes_concluidas',count(*) filter(where era_publicada and estado='concluida'),
 'erros',count(*) filter(where estado='erro'),'ultimo_erro',(select jsonb_build_object('linha',linha_id,'erro',erro) from clube_novo.correcao_altura_ia_v13 where estado='erro' order by linha_id limit 1),
 'concluida_em',case when count(*)>0 and count(*) filter(where estado<>'concluida')=0 then max(concluida_em) end)
from clube_novo.correcao_altura_ia_v13 $$;
revoke all on function public.correcao_altura_ia_status_v13() from public,anon,authenticated;
grant execute on function public.correcao_altura_ia_status_v13() to service_role;

create or replace function public.correcao_altura_ia_tick_v13(p_limite integer default 100,p_linhas bigint[] default null)
returns jsonb language plpgsql security definer set search_path='' set statement_timeout='55s' as $$
declare r record;l clube_novo.build_linha_card%rowtype;b clube_novo.build_bonificador%rowtype;
 nb clube_novo.build_bonificador%rowtype;p clube_novo.build_publicacao_linha_ativa_v1%rowtype;
 novo bigint;f jsonb;v_erro text;ini timestamptz:=clock_timestamp();qt int:=0;
begin
 if not pg_try_advisory_xact_lock(hashtextextended('correcao-altura-ia-v13',0)) then return jsonb_build_object('ocupado',true);end if;
 if exists(select 1 from clube_novo.bonificador_correcao_lote_v1 where estado in('rodando','pausando')) then raise exception 'Pause o Bonificador completo antes da correção seletiva';end if;
 if exists(select 1 from clube_novo.correcao_altura_ia_v13 where estado='erro') then return public.correcao_altura_ia_status_v13();end if;
 for r in select * from clube_novo.correcao_altura_ia_v13 where (estado='pendente' or (estado='aguardando_otimizador' and exists(select 1 from clube_novo.build_linha_card z where z.id=linha_id and z.estado_otimizador='concluido' and z.build_otimizador_id is not null))) and (p_linhas is null or linha_id=any(p_linhas)) order by era_publicada desc,linha_id limit least(greatest(p_limite,1),250) loop
  begin
   select * into l from clube_novo.build_linha_card where id=r.linha_id for update;
   select * into b from clube_novo.build_bonificador where id=r.antigo_id;
   select * into p from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=l.id;
   if l.estado<>'pendente' or exists(select 1 from clube_novo.orcamento_revisao_linha_v1 where linha_anterior_id=l.id) then raise exception 'Linha deixou de ser vigente';end if;
   if p.linha_id is not null and p.build_bonificador_id<>b.id and not exists(select 1 from clube_novo.build_bonificador x where x.id=p.build_bonificador_id and
    (x.bonus_fisico_detalhe,x.bonus_ia,x.bonus_total,x.bonus_playstyle_1,x.bonus_playstyle_2,x.bonus_pe) is not distinct from
    (b.bonus_fisico_detalhe,b.bonus_ia,b.bonus_total,b.bonus_playstyle_1,b.bonus_playstyle_2,b.bonus_pe)) then raise exception 'Publicação usa outra base de bônus';end if;
   novo:=clube_novo.corrigir_altura_ia_resultado_v13(l.id,b.id);
   select * into nb from clube_novo.build_bonificador where id=novo;
   update clube_novo.bonificador_correcao_item_v1 set build_bonificador_id_novo=novo where build_linha_card_id=l.id and build_bonificador_id_novo=b.id and estado_item='preparado';
   update clube_novo.build_linha_card set build_bonificador_id=novo,bonificador_motor_versao=nb.motor_versao,
    bonificador_contrato_versao=nb.contrato_versao,snapshot_bonificador_fingerprint=nb.resultado_fingerprint where id=l.id and (p.linha_id is null or (l.estado_otimizador='concluido' and l.build_otimizador_id is not null));
   if l.estado_otimizador='concluido' and l.build_otimizador_id is not null then
    f:=clube_novo.finalizar_publicar_linha_v1(l.id,'correcao_altura_ia_v13');
    if f->>'estado' not in('publicada','ja_publicada') then raise exception 'Finalização recusada: %',f;end if;
    if p.linha_id is not null and not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 x where x.linha_id=l.id and x.build_bonificador_id=novo and x.build_otimizador_id=l.build_otimizador_id and abs(x.nota_final-(p.nota_final-b.bonus_total+nb.bonus_total))<0.000001) then raise exception 'Readback da nota final falhou';end if;
   end if;
   if not exists(select 1 from clube_novo.build_linha_card x where x.id=l.id and x.build_otimizador_id is not distinct from l.build_otimizador_id and x.snapshot_otimizador_fingerprint is not distinct from l.snapshot_otimizador_fingerprint) then raise exception 'Otimizador alterado';end if;
   update clube_novo.correcao_altura_ia_v13 set estado=case when p.linha_id is not null and (l.estado_otimizador<>'concluido' or l.build_otimizador_id is null) then 'aguardando_otimizador' else 'concluida' end,novo_id=novo,concluida_em=clock_timestamp(),erro=null where linha_id=l.id;
   qt:=qt+1;
  exception when others then
   get stacked diagnostics v_erro=message_text;
   update clube_novo.correcao_altura_ia_v13 set estado='erro',erro=v_erro where linha_id=r.linha_id;
   return public.correcao_altura_ia_status_v13();
  end;
  exit when clock_timestamp()-ini>interval '20 seconds';
 end loop;
 return public.correcao_altura_ia_status_v13()||jsonb_build_object('corrigidas_neste_lote',qt);
end $$;
revoke all on function public.correcao_altura_ia_tick_v13(integer,bigint[]) from public,anon,authenticated;
grant execute on function public.correcao_altura_ia_tick_v13(integer,bigint[]) to service_role;

CREATE OR REPLACE FUNCTION clube_novo.bonus_estilo_conforme_v12(p_bonus_id bigint, p_card_id text, p_funcao_id bigint, p_posicao_id integer)
 RETURNS boolean
 LANGUAGE plpgsql
 STABLE
 SET search_path TO ''
AS $function$
declare b clube_novo.build_bonificador%rowtype; s jsonb; e jsonb;
begin
 select * into b from clube_novo.build_bonificador where id=p_bonus_id;
 if b.id is null or not (
  (b.motor_versao='v11-0709-estilo-posicao-oficial-v1' and b.formula_fingerprint='2e80a07d51f2bc8f456f9710c82717d38e3142cb3d52fd325b7b587c58ed2879' and b.contrato_versao='bonificador-regua-v3')
  or (b.motor_versao='v12-0909-estilo-funcao-ativacao-v1' and b.formula_fingerprint='4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8' and b.contrato_versao='bonificador-regua-v4')
 or (b.motor_versao='v13-1009-altura-ia-v1' and b.formula_fingerprint='afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f' and b.contrato_versao='bonificador-altura-ia-v13')
 ) then return false; end if;
 s:=clube_novo.carta_estilos_efetivos_v12(p_card_id);
 if not coalesce((s->>'pode_rodar')::boolean,falseor (b.motor_versao='v13-1009-altura-ia-v1' and b.formula_fingerprint='afa495d927fe99730fa154e5d91c227e56c36c51bd048cd8881b688bc2aa126f' and b.contrato_versao='bonificador-altura-ia-v13')
 ) then return false; end if;
 e:=clube_novo.conferir_bonus_estilo_0909_v1(p_funcao_id,p_posicao_id,(s->>'ataque_id')::int,(s->>'defesa_id')::int);
 return coalesce((e->>'pode_calcular')::boolean,false)
  and b.bonus_playstyle_1 is not distinct from (e->>'bonus_ataque')::numeric
  and b.bonus_playstyle_2 is not distinct from (e->>'bonus_defesa')::numeric
  and b.b_estilo is not distinct from (e->>'bonus_total')::numeric;
end $function$
